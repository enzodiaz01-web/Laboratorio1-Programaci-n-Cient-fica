"""Modelo básico de una trayectoria peatonal."""
import math
from dataclasses import dataclass, field

from .observacion import Observacion


@dataclass
class Trayectoria:
    """Representa las observaciones y cálculos propios de un peatón."""

    id_peaton: int
    observaciones: list[Observacion] = field(default_factory=list)

    def calcular_distancia_total(self) -> float:
        """Calcula la distancia acumulada punto a punto en metros."""
        if len(self.observaciones) < 2:
            return 0.0

        distancia = 0.0
        for i in range(1, len(self.observaciones)):
            p1 = self.observaciones[i - 1]
            p2 = self.observaciones[i]
            # Teorema de Pitágoras directo: sqrt((x2 - x1)^2 + (y2 - y1)^2)
            distancia += math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2)

        return distancia

    def calcular_desplazamiento(self) -> float:
        """Calcula el desplazamiento (distancia en línea recta entre el inicio y el final)."""
        if len(self.observaciones) < 2:
            return 0.0

        inicio = self.observaciones[0]
        fin = self.observaciones[-1]

        return math.sqrt((fin.x - inicio.x) ** 2 + (fin.y - inicio.y) ** 2)

    def calcular_velocidad_media(self, fps: float) -> float:
        """Calcula la velocidad media (m/s) usando los fotogramas por segundo del experimento."""
        if len(self.observaciones) < 2 or fps <= 0:
            return 0.0

        delta_frames = self.observaciones[-1].frame - self.observaciones[0].frame
        if delta_frames <= 0:
            return 0.0

        tiempo_total_segundos = delta_frames / fps
        distancia_total = self.calcular_distancia_total()

        return distancia_total / tiempo_total_segundos
