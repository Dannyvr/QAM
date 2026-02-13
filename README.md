# Grover Algorithm - Depth Explosion Demo

Este proyecto implementa una demostración simple del algoritmo de Grover usando Qiskit, mostrando cómo la profundidad del circuito aumenta con las iteraciones.

## Descripción

El código implementa el algoritmo de Grover para buscar el estado |11⟩ en un sistema de 2 qubits. Incluye:

- **Oráculo**: Marca el estado objetivo |11⟩ usando una compuerta CZ
- **Difusor**: Amplifica la amplitud del estado marcado
- **Análisis**: Muestra la profundidad del circuito y el número de compuertas CNOT para diferentes iteraciones

## Requisitos

- Python 3.8 o superior
- Qiskit
- Qiskit Aer

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

Ejecuta el script principal:

```bash
python src/grover_demo.py
```

## Resultados Esperados

El programa mostrará la profundidad del circuito y el número de compuertas CNOT para 1, 3 y 5 iteraciones del algoritmo de Grover, demostrando cómo aumenta la complejidad del circuito.

## Estructura del Proyecto

```
grover-algorithm/
├── README.md           # Este archivo
├── requirements.txt    # Dependencias del proyecto
└── src/
    └── grover_demo.py  # Script principal con la implementación de Grover
```

## Autor

Proyecto de tesis - Demostración del algoritmo de Grover
