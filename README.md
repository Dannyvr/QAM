# QRASP Algorithm - Grover + QRAM Benchmarks

Este repositorio contiene prototipos y benchmarks para comparar la arquitectura QRASP contra el modelo estandar, usando variantes del algoritmo de Grover y modelos de QRAM.

## Descripción

Incluye tres componentes principales:

- **Demo de Grover (2 qubits)**: Analiza la profundidad del circuito y CNOTs por iteraciones
- **Benchmark QRASP vs STD**: Mide CNOTs, profundidad y fidelidad con ruido simulado
- **Benchmark QRAM**: Compara QLOAD lineal vs bucket brigade con metrica Z

## Requisitos

- Python 3.8 o superior
- Qiskit
- Qiskit Aer
- Qiskit IBM Runtime (fake providers)

## Instalación

1. Clona o descarga este repositorio
2. Crea un entorno virtual (recomendado):
   ```bash
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Ejecuta los scripts principales:

```bash
python src/grover_demo.py
python src/grover_stress.py
python src/qrasp_prototype.py
```

## Resultados Esperados

Los programas generan reportes por consola y archivos CSV/PNG con los resultados:

- grover_demo: profundidad y CNOTs para varias iteraciones
- grover_stress: resultados en resultados_investigacion_etapa1.csv y analisis_superioridad_qrasp_final.png
- qrasp_prototype: resultados en benchmarking_qram_etapa2.csv y qram_analysis_with_z.png

## Estructura del Proyecto

```
qrasp-algorithm/
├── README.md           # Este archivo
├── requirements.txt    # Dependencias del proyecto
├── resultados_investigacion_etapa1.csv
├── benchmarking_qram_etapa2.csv
└── src/
   ├── grover_demo.py       # Demo Grover 2 qubits
   ├── grover_stress.py     # Benchmark QRASP vs STD (ruido simulado)
   └── qrasp_prototype.py   # Benchmark QRAM (lineal vs bucket brigade)
```

## Autor

Proyecto de tesis - Demostración del algoritmo de Grover
