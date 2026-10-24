"""Etapa de carga de varios experimentos."""

from pathlib import Path

from models.experimento import Experimento
from models.observacion import Observacion
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline


class CargaExperimentos(EtapaPipeline[None, list[Experimento]]):
    """Carga una colección de experimentos desde la ruta configurada."""

    def ejecutar(
        self,
        entrada: None,
        contexto: ContextoPipeline,
    ) -> list[Experimento]:
        """Carga los experimentos indicados por la configuración del contexto."""
        # Obtener la ruta de entrada configurada en el contexto (Path)
        ruta_datos = Path(contexto.ruta_entrada)
        return self._cargar_experimentos(ruta_datos)

    def _cargar_experimentos(self, ruta_entrada: Path) -> list[Experimento]:
        """Carga los experimentos disponibles (.txt) en la ruta recibida."""
        experimentos: list[Experimento] = []

        if not ruta_entrada.exists():
            raise FileNotFoundError(f"La ruta especificada no existe: {ruta_entrada}")

        # Buscar y ordenar todos los archivos .txt dentro del directorio
        archivos_txt = sorted(list(ruta_entrada.glob("*.txt")))

        for archivo in archivos_txt:
            # Asignar el nombre del archivo (sin extensión) como nombre del experimento
            nombre_exp = archivo.stem
            experimento = Experimento(nombre=nombre_exp)

            with open(archivo, "r", encoding="utf-8") as f:
                for linea in f:
                    linea_limpia = linea.strip()
                    
                    # Omitir líneas vacías o encabezados que inician con '#'
                    if not linea_limpia or linea_limpia.startswith("#"):
                        continue

                    partes = linea_limpia.split()
                    if len(partes) < 5:
                        continue  # Validación básica de número de columnas

                    # Formato del archivo traj_*.txt: id, frame, x, y, z
                    obs = Observacion(
                        id_peaton=int(partes[0]),
                        frame=int(partes[1]),
                        x=float(partes[2]),
                        y=float(partes[3]),
                        z=float(partes[4]),
                    )
                    experimento.observaciones.append(obs)

            experimentos.append(experimento)

        return experimentos