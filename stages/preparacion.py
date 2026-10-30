"""Etapa de preparación de observaciones y trayectorias."""
import math
from models.experimento import Experimento
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class PreparacionTrayectorias(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Agrupa validación, organización y reconstrucción de trayectorias."""

    def ejecutar(
        self,
        experimentos: list[Experimento],
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Prepara las observaciones y trayectorias de cada experimento."""
        for experimento in experimentos:
            obs_validas = self._validar_observaciones(experimento.observaciones)
            experimento.observaciones = obs_validas
            obs_organizadas = self._organizar_observaciones(obs_validas)
            experimento.trayectorias = self._reconstruir_trayectorias(obs_organizadas)
        return experimentos
       

    def _validar_observaciones(
        self,
        observaciones: list[Observacion],
    ) -> list[Observacion]:
        """Valida y retorna las observaciones de un experimento."""
        return list(
            filter(
                lambda o: (
                    o.id_peaton > 0
                    and o.frame >= 0
                    and not (math.isnan(o.x) or math.isnan(o.y) or math.isnan(o.z))
                    and not (math.isinf(o.x) or math.isinf(o.y) or math.isinf(o.z))
                ),
                observaciones,
            )
        )
       
    def _organizar_observaciones(
        self,
        observaciones: list[Observacion],
    ) -> dict[int, list[Observacion]]:
        """Organiza las observaciones por identificador de peatón."""
        agrupadas: dict[int, dict[int, Observacion]] = {}
        for obs in observaciones:
            agrupadas.setdefault(obs.id_peaton, {})[obs.frame] = obs

        return {
            id_p: sorted(frames_dict.values(), key=lambda o: o.frame)
            for id_p, frames_dict in sorted(agrupadas.items())
        }
       

    def _reconstruir_trayectorias(
        self,
        observaciones_organizadas: dict[int, list[Observacion]],
    ) -> list[Trayectoria]:
        """Construye trayectorias desde las observaciones organizadas."""
        return [
            Trayectoria(id_peaton=id_p, observaciones=lista_obs)
            for id_p, lista_obs in observaciones_organizadas.items()
            if len(lista_obs) >= 2]


       
