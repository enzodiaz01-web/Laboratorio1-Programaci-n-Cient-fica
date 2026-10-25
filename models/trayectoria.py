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
        """Calcula la distancia total recorrida por el peatón."""
        if len(self.observaciones)<2:
            return 0.0
        distancia = 0.0
        for i in range(1, len(self.observaciones)):
            p1 = self.observaciones[i-1]
            p2 = self.observaciones[i]
            distancia+= math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
        return distancia

    def calcular_desplazamiento(self) -> float:
        """Calcula el desplazamiento entre el inicio y el final."""
        if len(self.observaciones) <2:
            return 0.0
        inicio = self.observaciones[0]
        fin = self.observaciones[-1]
        return math.sqrt((fin.x - inicio.x) ** 2 + (fin.y - inicio.y) ** 2)

    def calcular_velocidad_media(self, fps: float) -> float:
        """Calcula la velocidad media usando la frecuencia del experimento."""
        if len(self.observaciones)<2 or fps <=0:
            return 0.0
        delta_frames = self.observaciones[-1].frame - self.observaciones[0].frame
        if delta_frames <=0:
            return 0.0
        tiempo_total_segundo = delta_frames/fps
        distancia_total = self.calcular_distancia_total()
        return distancia_total/tiempo_total_segundo

