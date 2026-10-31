"""Etapa de comparación de experimentos."""
import math
from functools import reduce
from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

FPS_POR_DEFECTO = 25.0
MIN_EXPERIMENTOS_CORRELACION = 3


def _media(valores: list[float]) -> float:
    """Media aritmética; 0.0 si no hay valores."""
    return sum(valores) / len(valores) if valores else 0.0


def _pearson(xs: list[float], ys: list[float]) -> float:
    """Coeficiente de correlación de Pearson; 0.0 si no es calculable."""
    if len(xs) < MIN_EXPERIMENTOS_CORRELACION:
        return 0.0
    mx, my = _media(xs), _media(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = math.sqrt(sum((x - mx) ** 2 for x in xs)) * math.sqrt(
        sum((y - my) ** 2 for y in ys)
    )
    return num / den if den > 0 else 0.0


def _pendiente(xs: list[float], ys: list[float]) -> float:
    """Pendiente de la recta de mínimos cuadrados y = a*x + b."""
    if len(xs) < MIN_EXPERIMENTOS_CORRELACION:
        return 0.0
    mx, my = _media(xs), _media(ys)
    varianza = sum((x - mx) ** 2 for x in xs)
    if varianza == 0:
        return 0.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / varianza


class ComparacionExperimentos(
    EtapaPipeline[list[Experimento], ResultadoAnalisis]
):
    """Compara resultados de varios experimentos."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> ResultadoAnalisis:
        """Retorna los experimentos junto con sus resultados comparativos."""
        for experimento in experimentos:
            fps = self._obtener_fps(experimento, contexto)
            experimento.resultados_colectivos.update(
                self._resumir_experimento(experimento, fps)
            )
        return ResultadoAnalisis(
            experimentos=experimentos,
            comparacion=self._comparar(experimentos),
        )

    def _obtener_fps(
        self,
        experimento: Experimento,
        contexto: ContextoPipeline,
    ) -> float:
        """Obtiene el fps del experimento (mismo criterio que AnalisisEspacial)."""
        resultados = experimento.resultados_colectivos
        candidatos = (
            resultados.get("fps_usado"),
            contexto.fps,
            resultados.get("fps_archivo"),
        )
        return next((float(c) for c in candidatos if c and c > 0), FPS_POR_DEFECTO)

    def _resumir_experimento(
        self,
        experimento: Experimento,
        fps: float,
    ) -> dict[str, float]:
        """Calcula el resumen de un experimento (requisito 5.7)."""
        trayectorias = experimento.trayectorias
        distancias = list(map(Trayectoria.calcular_distancia_total, trayectorias))
        velocidades = [t.calcular_velocidad_media(fps) for t in trayectorias]
        tiempos = [
            (t.observaciones[-1].frame - t.observaciones[0].frame) / fps
            for t in trayectorias
            if len(t.observaciones) >= 2
        ]

        eficiencias = [t.calcular_eficiencia_espacial() for t in trayectorias]

        velocidad_media = _media(velocidades)
        densidad_media = experimento.resultados_colectivos.get("densidad_media", 0.0)

        return {
            "num_peatones": float(len(trayectorias)),
            "velocidad_media": velocidad_media,
            "distancia_media": _media(distancias),
            "tiempo_medio": _media(tiempos),
            "eficiencia_media": _media(eficiencias),
            # Relación fundamental J_s = rho * v (aproximada con la velocidad
            # media global del experimento); se contrasta con el flujo medido.
            "flujo_especifico_teorico": densidad_media * velocidad_media,
        }

    def _comparar(self, experimentos: list[Experimento]) -> dict[str, float]:
        """Compara los experimentos entre sí."""
        if not experimentos:
            return {"num_experimentos": 0.0}

        res = [e.resultados_colectivos for e in experimentos]
        densidades = [r.get("densidad_media", 0.0) for r in res]
        velocidades = [r.get("velocidad_media", 0.0) for r in res]
        flujos = [r.get("flujo_peatonal", 0.0) for r in res]

        return {
            "num_experimentos": float(len(experimentos)),
            "num_peatones_total": reduce(
                lambda acc, r: acc + r.get("num_peatones", 0.0), res, 0.0
            ),
            "velocidad_media_global": _media(velocidades),
            "densidad_media_global": _media(densidades),
            "flujo_medio_global": _media(flujos),
            # Con menos de 3 experimentos estos tres valores quedan en 0.0.
            "correlacion_densidad_velocidad_entre_experimentos": _pearson(
                densidades, velocidades
            ),
            "pendiente_velocidad_vs_densidad": _pendiente(densidades, velocidades),
            "correlacion_densidad_flujo_entre_experimentos": _pearson(
                densidades, flujos
            ),
            # Posición (0, 1, 2...) en la lista de experimentos.
            "indice_experimento_mas_denso": float(
                max(range(len(res)), key=densidades.__getitem__)
            ),
            "indice_experimento_mas_lento": float(
                min(range(len(res)), key=velocidades.__getitem__)
            ),
        }