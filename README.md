#Laboratorio 1: Análisis de Trayectorias Peatonales

#Asignatura: Programación Científica  
#Integrantes: Enzo Díaz, Matías Alquinta y Daniel Robles

#Descripción del Proyecto
```
Pipeline modular y reproducible en Python para el procesamiento y análisis de trayectorias peatonales en un corredor unidireccional (`uni_corr_500_01` a `uni_corr_500_09`). El sistema carga las observaciones crudas, valida y reconstruye las trayectorias individuales, calcula indicadores cinemáticos individuales y colectivos (zonas espaciales, densidad peatonal y flujo), compara los experimentos y exporta los resultados en formatos CSV y JSON.

# Estructura del Proyecto
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