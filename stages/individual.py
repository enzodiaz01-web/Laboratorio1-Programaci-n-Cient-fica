"""Etapa de análisis individual de los experimentos."""

import math
from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class AnalisisIndividual(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Coordina el análisis de múltiples trayectorias y reúne sus indicadores."""
    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Analiza las trayectorias de cada experimento."""
        
        for experimento in experimentos:
            # Revisa los FPS desde el contexto o el archivo según la lógica del equipo
            fps_EXP = (
                contexto.fps
                if (hasattr(contexto, "fps") and contexto.fps and contexto.fps > 0)
                else experimento.resultados_colectivos.get("fps_archivo", 25.0)
            )
            dt = 1.0 / fps_EXP
            
            for trayectoria in experimento.trayectorias:
                # 1. Obtener indicadores base usando los métodos del modelo
                indicadores = self._calcular_indicadores(trayectoria, fps_EXP)
                if not indicadores:
                    continue
                    
                # 2. Detectar intervalos de detención
                detenciones = self._detectar_detenciones(trayectoria, fps_EXP)
                tiempo_detenido = sum((fin - ini + 1) * dt for ini, fin in detenciones)
                tiempo_total = indicadores.get("tiempo_total", 0.0)
                porcentaje_detenido = (
                    (tiempo_detenido / tiempo_total * 100.0) 
                    if tiempo_total > 0 
                    else 0.0
                )
                
                indicadores["cant_detenciones"] = float(len(detenciones))
                indicadores["tiempo_detenido_s"] = tiempo_detenido
                indicadores["porcentaje_detenido"] = porcentaje_detenido
                
                # Guardar en el diccionario de resultados del experimento
                experimento.resultados_individuales[trayectoria.id_peaton] = indicadores

        return experimentos

    def _calcular_indicadores(
        self,
        trayectoria: Trayectoria,
        fps: float | None,
    ) -> dict[str, float]:
        """Calcula los indicadores individuales reutilizando los métodos de Trayectoria."""
        obs = trayectoria.observaciones
        if not obs:
            return {}

        fps_val = fps if fps and fps > 0 else 25.0

        # Posiciones inicial y final
        x_ini, y_ini = obs[0].x, obs[0].y
        x_fin, y_fin = obs[-1].x, obs[-1].y

        # Tiempo total
        delta_frames = obs[-1].frame - obs[0].frame
        tiempo_total = delta_frames / fps_val

        # REUTILIZACIÓN DE MÉTODOS DE LA CLASE TRAYECTORIA
        distancia_total = trayectoria.calcular_distancia_total()
        desplazamiento = trayectoria.calcular_desplazamiento()
        velocidad_media = trayectoria.calcular_velocidad_media(fps_val)

        # Eficiencia E = D / Dr (Sección 5.2 de la pauta)
        eficiencia = (desplazamiento / distancia_total) if distancia_total > 0 else 0.0

        # Cálculo de la velocidad máxima instantánea
        vel_maxima = 0.0
        for i in range(1, len(obs)):
            dx = obs[i].x - obs[i - 1].x
            dy = obs[i].y - obs[i - 1].y
            d_i = math.sqrt(dx**2 + dy**2)
            dt_i = (obs[i].frame - obs[i - 1].frame) / fps_val
            if dt_i > 0:
                v_i = d_i / dt_i
                if v_i > vel_maxima:
                    vel_maxima = v_i

        return {
            "x_inicial": x_ini,
            "y_inicial": y_ini,
            "x_final": x_fin,
            "y_final": y_fin,
            "tiempo_total": tiempo_total,
            "distancia_total": distancia_total,
            "desplazamiento": desplazamiento,
            "velocidad_media": velocidad_media,
            "eficiencia": eficiencia,
            "velocidad_maxima": vel_maxima
        }
