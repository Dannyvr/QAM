import math
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

# --- PASO A: MEMORIA CLÁSICA (VIRTUAL QRAM) ---

class VirtualQRAM:
    def __init__(self, data_dict):
        """
        data_dict: {int: str} ej. {0: '101', 1: '011'}
        Asegúrate de que todos los bitstrings tengan la misma longitud.
        """
        self.memory = data_dict
        self.num_addresses = len(data_dict)
        self.address_width = math.ceil(math.log2(self.num_addresses))
        self.data_width = len(list(data_dict.values())[0])

    def get_data(self, address):
        return self.memory.get(address, '0' * self.data_width)

# --- PASO B & C: LA INSTRUCCIÓN QLOAD ---

def qload(circuit, address_reg, data_reg, qram):
    """
    Implementación lógica de QLOAD mediante decodificación de direcciones.
    Aplica una operación controlada: si address == i, entonces data ^= D_i
    """
    # Iteramos sobre cada dirección física de la memoria
    for addr_idx, bitstring in qram.memory.items():
        # 1. Convertimos addr_idx a binario para saber qué qubits de dirección activar
        binary_addr = format(addr_idx, f'0{qram.address_width}b')
        
        # 2. "Pre-acondicionamiento": Aplicamos X donde la dirección tiene un '0'
        # Esto hace que el estado buscado se convierta temporalmente en |11...1>
        for i, bit in enumerate(binary_addr):
            if bit == '0':
                circuit.x(address_reg[i])
        
        # 3. Transferencia de Datos: Por cada '1' en el dato, aplicamos un Multi-Controlled X (MCX)
        for j, data_bit in enumerate(bitstring):
            if data_bit == '1':
                # El registro de datos se activa solo si el registro de dirección coincide
                circuit.mcx(address_reg, data_reg[j])
        
        # 4. "Post-acondicionamiento": Revertimos las X para mantener el estado original
        for i, bit in enumerate(binary_addr):
            if bit == '0':
                circuit.x(address_reg[i])
        
        # Barrera lógica para visualización (opcional)
        circuit.barrier()

# --- EJECUCIÓN DEL PROTOTIPO ---

if __name__ == "__main__":
    # 1. Definir Memoria (4 datos de 3 bits cada uno)
    # Dirección 0 -> 101, 1 -> 011, 2 -> 110, 3 -> 001
    mem_data = {0: '101', 1: '011', 2: '110', 3: '001'}
    qram = VirtualQRAM(mem_data)
    
    # 2. Configurar Circuito
    qc = QuantumCircuit(qram.address_width + qram.data_width)
    addr_qubits = list(range(qram.address_width))
    data_qubits = list(range(qram.address_width, qram.address_width + qram.data_width))
    
    # 3. Preparar Dirección en Superposición Total (Hadamard)
    # Buscamos leer todas las direcciones al mismo tiempo
    qc.h(addr_qubits)
    qc.barrier()
    
    # 4. Llamar a QLOAD
    print(f"Ejecutando QLOAD para {len(mem_data)} direcciones...")
    qload(qc, addr_qubits, data_qubits, qram)
    
    # Imprimir el circuito antes de la medición
    print("\n" + "="*60)
    print("CIRCUITO CUÁNTICO (antes de medición)")
    print("="*60)
    print(qc.draw())
    
    # Guardar el circuito como PNG
    print("\nGuardando circuito como 'qram_circuit.png'...")
    qc.draw('mpl', filename='qram_circuit.png')
    print("Circuito guardado exitosamente.")
    
    # 5. Medición y Análisis
    qc.measure_all()
    
    # Simulación
    sim = AerSimulator()
    # Transpilamos a puertas base para medir el costo real
    tr_qc = transpile(qc, basis_gates=['u', 'cx'], optimization_level=1)
    
    # Imprimir el circuito transpilado
    print("\n" + "="*60)
    print("CIRCUITO TRANSPILADO (puertas base: u, cx)")
    print("="*60)
    print(tr_qc.draw())
    
    counts = sim.run(tr_qc, shots=2048).result().get_counts()
    
    print("\n" + "="*30)
    print("RESULTADOS DEL PROTOTIPO QLOAD")
    print("="*30)
    print(f"Profundidad del Circuito: {tr_qc.depth()}")
    print(f"Conteo de CNOTs: {tr_qc.count_ops().get('cx', 0)}")
    print("-" * 30)
    print("Estado Final (Dirección | Dato):")
    # Los resultados de Qiskit se leen de derecha a izquierda
    for state, freq in sorted(counts.items()):
        # Separamos el bitstring en Parte de Dirección y Parte de Dato
        data_part = state[:qram.data_width]
        addr_part = state[qram.data_width:]
        print(f"Dirección: |{addr_part}> -> Dato cargado: |{data_part}> (Frec: {freq})")