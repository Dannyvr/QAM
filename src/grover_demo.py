"""
Grover Algorithm - Depth Explosion Demo

Este script implementa el algoritmo de Grover para buscar el estado |11⟩
y analiza cómo la profundidad del circuito aumenta con las iteraciones.
"""

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def grover_circuit(iterations=1):
    """

    """
    qc = QuantumCircuit(2)
    
    # Inicialización (Superposición)
    qc.h([0, 1])
    
    for _ in range(iterations):
        # --- EL ORÁCULO (Opción A) ---
        # Marca el estado |11⟩
        qc.cz(0, 1)
        
        # --- EL DIFUSOR (Opción B) ---
        # Amplifica la amplitud del estado marcado
        qc.h([0, 1])
        qc.z([0, 1])
        qc.cz(0, 1)
        qc.h([0, 1])
    
    # Medición de todos los qubits
    qc.measure_all()
    return qc


def analyze_circuit_depth():
    """
    Analiza la profundidad del circuito y el número de compuertas CNOT
    para diferentes números de iteraciones.
    """
    print("=" * 70)
    print("Análisis de Profundidad del Circuito - Algoritmo de Grover")
    print("=" * 70)
    print()
    
    for i in [1, 3, 5, 10]:
        circuit = grover_circuit(i)
        transpiled = transpile(circuit, basis_gates=['u', 'cx'])
        
        depth = transpiled.depth()
        cnot_count = transpiled.count_ops().get('cx', 0)
        
        print(f"Iteraciones: {i}")
        print(f"  - Profundidad del circuito: {depth}")
        print(f"  - Número de CNOTs: {cnot_count}")
        print("  - Circuito original:")
        print(circuit.draw(output='text'))
        print("  - Circuito transpiled (basis: u, cx):")
        print(transpiled.draw(output='text'))
        print()
    
    print("=" * 70)
    print("Conclusión: La profundidad aumenta linealmente con las iteraciones")
    print("=" * 70)


if __name__ == "__main__":
    analyze_circuit_depth()
