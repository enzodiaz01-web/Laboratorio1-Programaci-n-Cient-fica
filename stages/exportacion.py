"""Etapa de exportación de resultados."""

import csv
import json
import re
from pathlib import Path
from typing import Any

from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

CLAVES_RESUMEN = (
    "num_peatones",
    "velocidad_media",
    "densidad_media",
    "flujo_peatonal",
    "distancia_media",
    "tiempo_medio",
    "eficiencia_media",
    "flujo_especifico_teorico",
    "fps_usado",
)
CLAVES_DENSIDAD_FLUJO = (
    "area_referencia_m2",
    "densidad_media",
    "densidad_maxima",
    "correlacion_densidad_velocidad",
    "peatones_cruzan_linea",
    "intervalo_flujo_s",
    "flujo_peatonal",
    "flujo_especifico",
)
# Claves de zonas: "<zona>_peatones", "<zona>_velocidad_media", "<zona>_tiempo_medio"
PATRON_ZONA = re.compile(r"^(zona_.+)_(peatones|velocidad_media|tiempo_medio)$")

Fila = dict[str, Any]


class ExportacionResultados(EtapaPipeline[ResultadoAnalisis, None]):
    """Exporta los resultados de los experimentos y su comparación."""

    def ejecutar(
        self,
        resultados: ResultadoAnalisis,
        contexto: ContextoPipeline,
    ) -> None:
        """Guarda los resultados en la ruta de salida configurada."""
        self._exportar(resultados, contexto.ruta_salida)
        print(f"Resultados exportados en: {contexto.ruta_salida}")

    def _exportar(self, resultados: ResultadoAnalisis, ruta_salida: Path) -> None:
        """Exporta los resultados a la ruta indicada."""
        ruta_salida.mkdir(parents=True, exist_ok=True)
        experimentos = resultados.experimentos

        tablas: dict[str, tuple[list[str], list[Fila]]] = {
            "resultados_individuales.csv": self._tabla_individual(experimentos),
            "resumen_experimentos.csv": self._tabla_por_claves(
                experimentos, CLAVES_RESUMEN
            ),
            "resultados_zonas.csv": self._tabla_zonas(experimentos),
            "densidad_flujo.csv": self._tabla_por_claves(
                experimentos, CLAVES_DENSIDAD_FLUJO
            ),
        }
        for nombre, (columnas, filas) in tablas.items():
            self._escribir_csv(ruta_salida / nombre, columnas, filas)

        self._escribir_json(ruta_salida / "comparacion.json", resultados.comparacion)

    # ----- construcción de tablas -----

    def _tabla_individual(
        self, experimentos: list[Experimento]
    ) -> tuple[list[str], list[Fila]]:
        """Una fila por peatón con todos sus indicadores individuales."""
        filas = [
            {"experimento": e.nombre, "id_peaton": id_p, **indicadores}
            for e in experimentos
            for id_p, indicadores in e.resultados_individuales.items()
        ]
        base = ("experimento", "id_peaton")
        extras = dict.fromkeys(k for f in filas for k in f if k not in base)
        return [*base, *extras], filas

    def _tabla_por_claves(
        self, experimentos: list[Experimento], claves: tuple[str, ...]
    ) -> tuple[list[str], list[Fila]]:
        """Una fila por experimento con las claves colectivas indicadas."""
        filas = [
            {
                "experimento": e.nombre,
                **{k: e.resultados_colectivos.get(k) for k in claves},
            }
            for e in experimentos
        ]
        return ["experimento", *claves], filas

    def _tabla_zonas(
        self, experimentos: list[Experimento]
    ) -> tuple[list[str], list[Fila]]:
        """Una fila por (experimento, zona), con la velocidad relativa a la media."""
        filas: list[Fila] = []
        for experimento in experimentos:
            zonas: dict[str, dict[str, float]] = {}
            for clave, valor in experimento.resultados_colectivos.items():
                coincidencia = PATRON_ZONA.match(clave)
                if coincidencia:
                    zonas.setdefault(coincidencia.group(1), {})[
                        coincidencia.group(2)
                    ] = valor

            velocidades = [
                z["velocidad_media"]
                for z in zonas.values()
                if z.get("velocidad_media", 0.0) > 0
            ]
            referencia = sum(velocidades) / len(velocidades) if velocidades else 0.0

            filas.extend(
                {
                    "experimento": experimento.nombre,
                    "zona": nombre,
                    "peatones": datos.get("peatones"),
                    "velocidad_media": datos.get("velocidad_media"),
                    "tiempo_medio": datos.get("tiempo_medio"),
                    "velocidad_relativa": (
                        datos.get("velocidad_media", 0.0) / referencia
                        if referencia > 0
                        else None
                    ),
                }
                for nombre, datos in zonas.items()
            )
        columnas = [
            "experimento",
            "zona",
            "peatones",
            "velocidad_media",
            "tiempo_medio",
            "velocidad_relativa",
        ]
        return columnas, filas

    # ----- escritura de archivos -----

    def _escribir_csv(
        self, ruta: Path, columnas: list[str], filas: list[Fila]
    ) -> None:
        with ruta.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(
                archivo,
                fieldnames=columnas,
                restval="",
                extrasaction="ignore",
                lineterminator="\n",
            )
            escritor.writeheader()
            escritor.writerows(filas)

    def _escribir_json(self, ruta: Path, datos: dict[str, float]) -> None:
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, indent=2, ensure_ascii=False)
