"""Etapa de análisis espacial, densidad y flujo."""
import math
from functools import reduce
from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa el análisis por zonas y los cálculos de densidad y flujo."""
    ZONAS: dict[str, tuple[float,float]]= {
        "zona_1_entrada": (2.0, 4.0),
        "zona_2_centro_der": (0.0, 2.0),
        "zona_3_centro_izq": (-2.0, 0.0),
        "zona_4_salida": (-4.0, -2.0)
    }
    ANCHO_CORREDOR: float = 5.0  
    X_MIN_AREA: float = -4.0
    X_MAX_AREA: float = 4.0

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Analiza las zonas, la densidad y el flujo de cada experimento."""
        for experimento in experimentos:
            fps_exp = (
                contexto.fps
                if (hasattr(contexto, "fps") and contexto.fps)
                else experimento.resultados_colectivos.get("fps_archivo", 25.0)
            )
            experimento.resultados_colectivos["fps_usado"] = fps_exp

            res_zonas = self._analizar_zonas(experimento)
            res_densidad = self._calcular_densidad(experimento)
            res_flujo = self._calcular_flujo(experimento, fps_exp)

            experimento.resultados_colectivos.update(res_zonas)
            experimento.resultados_colectivos.update(res_densidad)
            experimento.resultados_colectivos.update(res_flujo)

        return experimentos

    def _analizar_zonas(self, experimento: Experimento) -> dict[str, float]:
        fps = experimento.resultados_colectivos.get("fps_usado", 25.0)
        fps_val = fps if fps and fps > 0 else 25.0

        # Acumuladores por zona: velocidades instantáneas y tiempos por peatón
        vel_por_zona: dict[str, list[float]] = {z: [] for z in self.ZONAS}
        tiempos_peaton_zona: dict[str, dict[int, float]] = {z: {} for z in self.ZONAS}

        for trayectoria in experimento.trayectorias:
            obs = trayectoria.observaciones
            for i in range(1, len(obs)):
                p1, p2 = obs[i - 1], obs[i]
                dt = (p2.frame - p1.frame) / fps_val
                if dt <= 0:
                    continue
                d_i = math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)
                v_i = d_i / dt

                for nombre_zona, (x_min, x_max) in self.ZONAS.items():
                    if x_min <= p2.x < x_max:
                        vel_por_zona[nombre_zona].append(v_i)
                        tiempos_peaton_zona[nombre_zona][trayectoria.id_peaton] = (
                            tiempos_peaton_zona[nombre_zona].get(trayectoria.id_peaton, 0.0) + dt
                        )
                        break

        resultados_zonas: dict[str, float] = {}
        for nombre_zona in self.ZONAS:
            tiempos_dict = tiempos_peaton_zona[nombre_zona]
            vels = vel_por_zona[nombre_zona]

            cant_peatones = float(len(tiempos_dict))
            vel_media = (sum(vels) / len(vels)) if vels else 0.0
            tiempo_medio = (
                (sum(tiempos_dict.values()) / len(tiempos_dict))
                if tiempos_dict
                else 0.0
            )

            resultados_zonas[f"{nombre_zona}_peatones"] = cant_peatones
            resultados_zonas[f"{nombre_zona}_velocidad_media"] = vel_media
            resultados_zonas[f"{nombre_zona}_tiempo_medio"] = tiempo_medio

        return resultados_zonas

    def _calcular_densidad(self, experimento: Experimento) -> dict[str, float]:
        fps = experimento.resultados_colectivos.get("fps_usado", 25.0)
        fps_val = fps if fps and fps > 0 else 25.0
        area_region = (self.X_MAX_AREA - self.X_MIN_AREA) * self.ANCHO_CORREDOR  # 40.0 m^2

        # Conteo de peatones y velocidades en el área central por cada frame
        peatones_por_frame: dict[int, int] = {}
        vels_por_frame: dict[int, list[float]] = {}

        for trayectoria in experimento.trayectorias:
            obs = trayectoria.observaciones
            for i, p in enumerate(obs):
                if self.X_MIN_AREA <= p.x <= self.X_MAX_AREA:
                    peatones_por_frame[p.frame] = peatones_por_frame.get(p.frame, 0) + 1
                    if i > 0:
                        p_ant = obs[i - 1]
                        dt = (p.frame - p_ant.frame) / fps_val
                        if dt > 0:
                            v_i = math.sqrt((p.x - p_ant.x) ** 2 + (p.y - p_ant.y) ** 2) / dt
                            vels_por_frame.setdefault(p.frame, []).append(v_i)

        if not peatones_por_frame:
            return {
                "densidad_media": 0.0,
                "densidad_maxima": 0.0,
                "correlacion_densidad_velocidad": 0.0,
            }

        frames_ordenados = sorted(peatones_por_frame.keys())
        densidades = list(map(lambda fr: peatones_por_frame[fr] / area_region, frames_ordenados))

        densidad_media = sum(densidades) / len(densidades)
        densidad_maxima = max(densidades)

        # Relación (correlación de Pearson) entre densidad instantánea y velocidad media instantánea
        pares_rho_vel = [
            (peatones_por_frame[fr] / area_region, sum(vels_por_frame[fr]) / len(vels_por_frame[fr]))
            for fr in frames_ordenados
            if fr in vels_por_frame and len(vels_por_frame[fr]) > 0
        ]

        correlacion = 0.0
        if len(pares_rho_vel) >= 2:
            m_rho = sum(p[0] for p in pares_rho_vel) / len(pares_rho_vel)
            m_vel = sum(p[1] for p in pares_rho_vel) / len(pares_rho_vel)
            num = sum((r - m_rho) * (v - m_vel) for r, v in pares_rho_vel)
            den_r = math.sqrt(sum((r - m_rho) ** 2 for r, _ in pares_rho_vel))
            den_v = math.sqrt(sum((v - m_vel) ** 2 for _, v in pares_rho_vel))
            if den_r > 0 and den_v > 0:
                correlacion = num / (den_r * den_v)

        return {
            "area_referencia_m2": area_region,
            "densidad_media": densidad_media,
            "densidad_maxima": densidad_maxima,
            "correlacion_densidad_velocidad": correlacion,
        }

    def _calcular_flujo(
        self,
        experimento: Experimento,
        fps: float | None,
    ) -> dict[str, float]:
        fps_val = fps if fps and fps > 0 else 25.0
        x_linea = 0.0
        frames_cruce: list[int] = []

        for trayectoria in experimento.trayectorias:
            obs = trayectoria.observaciones
            for i in range(1, len(obs)):
                x1, x2 = obs[i - 1].x, obs[i].x
                # Detectar cruce de la línea transversal x = 0.0 en cualquier sentido
                if (x1 >= x_linea and x2 < x_linea) or (x1 <= x_linea and x2 > x_linea):
                    frames_cruce.append(obs[i].frame)
                    break

        if not frames_cruce:
            return {
                "peatones_cruzan_linea": 0.0,
                "intervalo_flujo_s": 0.0,
                "flujo_peatonal": 0.0,
                "flujo_especifico": 0.0,
            }

        frame_min = reduce(lambda a, b: a if a < b else b, frames_cruce)
        frame_max = reduce(lambda a, b: a if a > b else b, frames_cruce)
        delta_t = (frame_max - frame_min) / fps_val

        if delta_t <= 0 and experimento.observaciones:
            todos_frames = [o.frame for o in experimento.observaciones]
            delta_t = (max(todos_frames) - min(todos_frames)) / fps_val

        n_cruces = float(len(frames_cruce))
        flujo = (n_cruces / delta_t) if delta_t > 0 else 0.0
        flujo_especifico = flujo / self.ANCHO_CORREDOR

        return {
            "peatones_cruzan_linea": n_cruces,
            "intervalo_flujo_s": delta_t,
            "flujo_peatonal": flujo,
            "flujo_especifico": flujo_especifico
        }