# Laboratorio 1: Análisis de Trayectorias Peatonales

## Asignatura: Programación Científica  

## Integrantes: 
- Enzo Díaz
- Matías Alquinta
- Daniel Robles

# Descripción del Proyecto

Pipeline modular y reproducible en Python para el procesamiento y análisis de trayectorias peatonales en un corredor unidireccional (`uni_corr_500_01` a `uni_corr_500_09`). El sistema carga las observaciones crudas, valida y reconstruye las trayectorias individuales, calcula indicadores cinemáticos individuales y colectivos (zonas espaciales, densidad peatonal y flujo), compara los experimentos y exporta los resultados en formatos CSV y JSON.

# Estructura del Proyecto
```
├── graficos/                   # Graficos de resultados
├── data/                       # Archivos de entrada (.txt) con observaciones peatonales
├── models/                     # Entidades del dominio (POO)
│   ├── observacion.py          # Representación de una observación (id, frame, x, y, z)
│   ├── trayectoria.py          # Reconstrucción y métricas base de una trayectoria
│   ├── experimento.py          # Agrupación de datos y resultados de un experimento
│   └── resultado_analisis.py   # Contenedor de resultados globales y comparativos
├── pipeline/                   # Infraestructura de ejecución secuencial
│   ├── contexto.py             # Opciones de configuración (input, output, fps)
│   ├── etapa.py                # Interfaz genérica abstracta EtapaPipeline
│   └── pipeline.py             # Coordinador de ejecución de etapas
├── stages/                     # Etapas de procesamiento del pipeline
│   ├── carga.py                # Lectura de archivos .txt y extracción de metadatos (FPS)
│   ├── preparacion.py          # Validación, ordenamiento temporal y armado de trayectorias
│   ├── individual.py           # Indicadores por peatón, eficiencia y detección de detenciones
│   ├── espacial.py             # Análisis por zonas, densidad instantánea y flujo transversal
│   ├── colectivo.py            # Resumen por experimento y correlaciones inter-experimento
│   └── exportacion.py          # Generación de archivos CSV y JSON en el directorio de salida
├── results/                    # Archivos de salida generados por el pipeline
└── main.py                     # Punto de entrada por línea de comandos (CLI)
```
# Instrucciones de ejecución 
Para poder ejecutar este proyecto es necesario contar con los siguientes componentes:

- **Sistema Operativo:** Linux o un entorno virtual Linux.
- **Lenguaje:** Python 3.10 o superior (`python3 --version`).
- **Dependencias:** Biblioteca estándar de Python (`math`, `functools`, `argparse`, `dataclasses`, `json`, `csv`, `pathlib`). No se requieren paquetes externos adicionales para la ejecución del núcleo del pipeline.

## Instrucciones de ejecución por consola
Para su correcto funcionamiento, es necesario posicionarse en el directorio del proyecto y asegurar que se encuentre la carpeta `data/` con sus respectivos archivos.

El proyecto se ejecuta mediante una interfaz de línea de comandos parametrizada con `argparse`. Para ejecutar el script principal `main.py`, se utiliza la bandera `--input` para especificar la carpeta de entrada y `--output` para la carpeta de resultados:

```bash
python3 main.py --input data --output results
```
También es posible forzar una frecuencia de muestreo específica mediante la opción `--fps`:
```bash
python3 main.py --input ./data --output ./results --fps 25
```

En caso de no especificar la frecuencia de muestreo, el sistema asignará por defecto el valor de 25 FPS.