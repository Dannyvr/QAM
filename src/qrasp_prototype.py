import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np
from qiskit import QuantumCircuit, transpile, QuantumRegister, AncillaRegister
from qiskit_aer import AerSimulator

# --- CLASE DE MEMORIA ---
class VirtualQRAM:
    def __init__(self, n_addr, data_width=3):
        self.address_width = n_addr
        self.data_width = data_width
        self.num_addresses = 2**n_addr
        # Memoria con datos aleatorios para testing
        self.memory = {i: format(np.random.randint(0, 2**data_width), f'0{data_width}b') 
                       for i in range(self.num_addresses)}

    def get_data(self, address):
        return self.memory.get(address, '0' * self.data_width)

# --- ARQUITECTURA 1: LINEAR (QLOAD PLANA) ---
def qload_linear(qc, addr_reg, data_reg, qram):
    for addr_idx, bitstring in qram.memory.items():
        binary_addr = format(addr_idx, f'0{qram.address_width}b')
        for i, bit in enumerate(binary_addr):
            if bit == '0': qc.x(addr_reg[i])
        for j, data_bit in enumerate(bitstring):
            if data_bit == '1':
                qc.mcx(addr_reg, data_reg[j])
        for i, bit in enumerate(binary_addr):
            if bit == '0': qc.x(addr_reg[i])
        qc.barrier()

# --- ARQUITECTURA 2: BUCKET BRIGADE (QLOAD EN ÁRBOL) ---
def build_routing_tree(n_addr, aux_reg):
    addr_q = QuantumRegister(n_addr, 'addr')
    tree_qc = QuantumCircuit(addr_q, aux_reg)
    tree_qc.x(aux_reg[0]) # Raíz activada
    
    current_idx = 1
    current_layer_nodes = [aux_reg[0]]
    for depth in range(n_addr):
        ctrl = addr_q[n_addr - 1 - depth]
        next_layer = []
        for parent in current_layer_nodes:
            left = aux_reg[current_idx]; right = aux_reg[current_idx+1]
            current_idx += 2
            # Ruteo: Si Control=1 -> Right, Si Control=0 -> Left
            tree_qc.ccx(parent, ctrl, right)
            tree_qc.x(ctrl); tree_qc.ccx(parent, ctrl, left); tree_qc.x(ctrl)
            next_layer.extend([left, right])
        current_layer_nodes = next_layer
    return tree_qc, current_layer_nodes

def qload_bucket_brigade(qc, addr_reg, data_reg, aux_reg, qram):
    routing_circuit, leaves = build_routing_tree(qram.address_width, aux_reg)
    routing_instr = routing_circuit.to_instruction(label="RoutingTree")
    
    # 1. Forward Pass (Routing)
    qc.append(routing_instr, list(addr_reg) + list(aux_reg))
    
    # 2. Data Load (Sándwich)
    leaf_offset = 2**qram.address_width - 1
    for i in range(len(leaves)):
        data_val = qram.get_data(i)
        for bit_idx, bit in enumerate(data_val):
            if bit == '1':
                qc.cx(aux_reg[leaf_offset + i], data_reg[bit_idx])
    
    # 3. Uncomputation (Reverse)
    qc.append(routing_instr.inverse(), list(addr_reg) + list(aux_reg))

# --- MOTOR DE BENCHMARKING CON MÉTRICA Z ---

def run_benchmarks(max_n=5):
    results = []
    print(f"{'n':<4} | {'Modo':<10} | {'CNOTs':<8} | {'Depth':<8} | {'Costo Z':<12}")
    print("-" * 55)

    for n in range(2, max_n + 1):
        qram = VirtualQRAM(n_addr=n)
        for mode in ['LINEAR', 'BUCKET']:
            addr_reg = QuantumRegister(n, 'addr')
            data_reg = QuantumRegister(qram.data_width, 'data')
            
            if mode == 'LINEAR':
                qc = QuantumCircuit(addr_reg, data_reg)
                qload_linear(qc, addr_reg, data_reg, qram)
            else:
                num_aux = 2**(n + 1) - 1
                aux_reg = AncillaRegister(num_aux, 'aux')
                qc = QuantumCircuit(addr_reg, data_reg, aux_reg)
                qload_bucket_brigade(qc, addr_reg, data_reg, aux_reg, qram)
            
            # Transpilación para obtener métricas reales
            tr_qc = transpile(qc, basis_gates=['u', 'cx'], optimization_level=1)
            
            depth = tr_qc.depth()
            cnots = tr_qc.count_ops().get('cx', 0)
            z_cost = depth * cnots  # <--- CÁLCULO DE MÉTRICA Z
            
            metrics = {
                'n': n,
                'mode': mode,
                'cnots': cnots,
                'depth': depth,
                'z_cost': z_cost,
                'qubits': tr_qc.num_qubits
            }
            results.append(metrics)
            print(f"{n:<4} | {mode:<10} | {cnots:<8} | {depth:<8} | {z_cost:<12.1e}")
            
    return pd.DataFrame(results)

def plot_comprehensive_analysis(df):
    plt.style.use('ggplot')
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 6))

    for mode, color in zip(['LINEAR', 'BUCKET'], ['red', 'blue']):
        subset = df[df['mode'] == mode]
        ax1.plot(subset['n'], subset['depth'], marker='o', color=color, label=f'{mode} Depth')
        ax2.plot(subset['n'], subset['cnots'], marker='s', color=color, label=f'{mode} CNOTs')
        ax3.plot(subset['n'], subset['z_cost'], marker='^', color=color, label=f'{mode} Unified Z')

    ax1.set_title('Profundidad (Tiempo)'); ax1.set_yscale('log'); ax1.legend()
    ax2.set_title('Conteo de CNOTs'); ax2.set_yscale('log'); ax2.legend()
    ax3.set_title('Costo Unificado Z (Volumen Espacio-Tiempo)'); ax3.set_yscale('log'); ax3.legend()
    
    plt.suptitle('Análisis de Eficiencia QRASP: QRAM Linear vs Bucket Brigade', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('qram_analysis_with_z.png')
    plt.show()

if __name__ == "__main__":
    df_results = run_benchmarks(max_n=5)
    plot_comprehensive_analysis(df_results)
    df_results.to_csv('benchmarking_qram_etapa2.csv', index=False)