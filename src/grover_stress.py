import pandas as pd
import matplotlib.pyplot as plt
import math
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeHanoiV2 # Librería actualizada

# --- 1. COMPONENTES DEL ALGORITMO (GROVER) ---

def get_iterations(n):
    """Número óptimo de iteraciones de Grover."""
    return max(1, int(round(math.pi / 4 * math.sqrt(2**n))))

def apply_mcz(qc, controls, target):
    """Multi-Controlled Z usando H-MCX-H."""
    qc.h(target)
    qc.mcx(controls, target)
    qc.h(target)

def apply_diffuser(qc, qubits, controls, target):
    """Operador de difusión de Grover."""
    qc.h(qubits)
    qc.x(qubits)
    apply_mcz(qc, controls, target)
    qc.x(qubits)
    qc.h(qubits)

def build_grover_circuit(n):
    """Construye el circuito lógico de Grover."""
    iters = get_iterations(n)
    qc = QuantumCircuit(n)
    qubits = range(n)
    controls = list(range(n - 1))
    target = n - 1

    qc.h(qubits)
    for _ in range(iters):
        apply_mcz(qc, controls, target)
        apply_diffuser(qc, qubits, controls, target)
    qc.measure_all()
    return qc, iters

# --- 2. CÁLCULO DE MÉTRICAS (STD vs QRASP) ---

def get_std_metrics(n, iters, basis_gates, opt_level):
    """Métricas del modelo estándar (circuitos transpilados o extrapolados)."""
    if n <= 8:
        qc, _ = build_grover_circuit(n)
        tr = transpile(qc, basis_gates=basis_gates, optimization_level=opt_level)
        cnots = tr.count_ops().get('cx', 0)
        depth = tr.depth()
    else:
        # Extrapolación O(2^n) basada en descomposición de MCX sin ancillas
        cnots = iters * 2 * (2**n - 2)
        depth = int(iters * 1.5 * 2**n)
    return cnots, depth, cnots * depth

def get_qrasp_metrics(n, iters):
    """Métricas del modelo QRASP (QRAM O(log N) + Control O(1))."""
    cnots = iters * 2 * n
    depth = iters * (n + 10) # n (dirección QRAM) + 10 (overhead de control reversible)
    return cnots, depth, cnots * depth

# --- 3. MODELO DE RUIDO Y FIDELIDAD ---

def get_average_error(backend):
    """Extrae el error promedio de CNOT (cx) del hardware de IBM."""
    props = backend.target
    errors = []
    for gate_name, inst_map in props.items():
        if gate_name == 'cx':
            for qargs, inst_prop in inst_map.items():
                if inst_prop is not None and inst_prop.error is not None:
                    errors.append(inst_prop.error)
    return np.mean(errors) if errors else 0.01

def test_fidelity_std(n, enable_noise, device, noise_model):
    """Mide la fidelidad real del modelo estándar (Simulación Ruidosa)."""
    qc, _ = build_grover_circuit(n)
    target_state = '1' * n
    shots = 1024
    sim_ideal = AerSimulator()
    
    # Referencia Ideal
    counts_ideal = sim_ideal.run(qc, shots=shots).result().get_counts()
    p_ideal = counts_ideal.get(target_state, 0) / shots
    
    # Prueba con Ruido
    if enable_noise and device and noise_model:
        tr_circuit = transpile(qc, device, optimization_level=1)
        result = noise_model.run(tr_circuit, shots=shots).result()
        counts_noise = result.get_counts()
        p_noise = counts_noise.get(target_state, 0) / shots
    else:
        p_noise = p_ideal
        
    return p_ideal, p_noise

# --- 4. BENCHMARKING PRINCIPAL ---

def run_benchmarks(config):
    backend_real = FakeHanoiV2()
    noise_model = AerSimulator.from_backend(backend_real) if config['ENABLE_NOISE'] else None
    avg_cx_error = get_average_error(backend_real)
    
    print(f"Hardware: {backend_real.name} | Error Promedio CX: {avg_cx_error:.4f}")
    print(f"Modo: {config['RUN_MODE']} | Ruido: {config['ENABLE_NOISE']}")
    print("-" * 100)

    results = []
    mode = config['RUN_MODE']
    
    for n in range(2, config['MAX_QUBITS'] + 1):
        iters = get_iterations(n)
        row = {'n': n, 'iters': iters}
        
        # Lógica de Arquitecturas
        if mode in ['STD', 'BOTH']:
            c, d, z = get_std_metrics(n, iters, config['BASIS_GATES'], config['OPT_LEVEL'])
            row.update({'std_cnots': c, 'std_depth': d, 'std_z': z})
            
        if mode in ['QRASP', 'BOTH']:
            c, d, z = get_qrasp_metrics(n, iters)
            row.update({'qrasp_cnots': c, 'qrasp_depth': d, 'qrasp_z': z})

        # Medición de Fidelidad (Muro del Ruido vs Proyección QRASP)
        if n <= config['NOISE_LIMIT']:
            p_ideal, p_noisy_std = test_fidelity_std(n, config['ENABLE_NOISE'], backend_real, noise_model)
        else:
            p_ideal, p_noisy_std = 1.0, (0.0 if config['ENABLE_NOISE'] else 1.0)
            
        row.update({'p_ideal': p_ideal, 'p_noisy_std': p_noisy_std})

        # Aplicación de la Fórmula de Proyección (Layered Error Model)
        if mode in ['QRASP', 'BOTH']:
            row['p_qrasp_proj'] = p_ideal * (1 - avg_cx_error)**row['qrasp_cnots']
            
        results.append(row)
        print(f"n={n} completado.")

    return pd.DataFrame(results)

def plot_analysis(df, config):
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    mode = config['RUN_MODE']

    # Función auxiliar para graficar
    def smart_plot(ax, std_col, qrasp_col, title, ylabel):
        if mode in ['STD', 'BOTH']:
            ax.plot(df['n'], df[std_col], 'ro-', label='Estándar')
        if mode in ['QRASP', 'BOTH']:
            ax.plot(df['n'], df[qrasp_col], 'gs--', label='QRASP')
        ax.set_yscale('log')
        ax.set_title(title, fontweight='bold')
        ax.set_ylabel(ylabel); ax.legend()

    smart_plot(ax1, 'std_cnots', 'qrasp_cnots', 'Métrica A: Cantidad de CNOTs', 'Log(CNOTs)')
    smart_plot(ax2, 'std_depth', 'qrasp_depth', 'Métrica B: Profundidad', 'Log(Depth)')
    smart_plot(ax3, 'std_z', 'qrasp_z', 'Métrica C: Costo Unificado Z', 'Log(Z)')

    # Gráfico D: Fidelidad y Muro del Ruido
    ax4.plot(df['n'], df['p_ideal'], 'gray', linestyle=':', label='Ideal (Teórico)')
    if mode in ['STD', 'BOTH']:
        ax4.plot(df['n'], df['p_noisy_std'], 'ro-', label='STD (Ruido Real)')
    if mode in ['QRASP', 'BOTH']:
        ax4.plot(df['n'], df['p_qrasp_proj'], 'gs--', label='QRASP (Proyectada)')
    
    ax4.set_title('Métrica D: Fidelidad (Muro del Ruido vs QRASP)', fontweight='bold', color='darkblue')
    ax4.set_ylabel('Success Probability'); ax4.set_ylim(-0.05, 1.05); ax4.legend()

    plt.suptitle(f"Benchmarking Arquitectónico QRASP - Etapa 1\nModo: {mode} | Hardware: FakeHanoiV2", fontsize=16)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(config['OUT_IMG'], dpi=300)
    plt.show()

# --- 5. MAIN (CONFIGURACIÓN FINAL) ---

if __name__ == "__main__":
    CONFIG = {
        'RUN_MODE': 'BOTH',           # 'STD', 'QRASP', 'BOTH'
        'ENABLE_NOISE': True,         # Simulación ruidosa real para la línea base
        'MAX_QUBITS': 15,
        'NOISE_LIMIT': 9,             # Máximo n para simulación de ruido directa
        'BASIS_GATES': ['u', 'cx'],
        'OPT_LEVEL': 1,
        'OUT_IMG': 'analisis_superioridad_qrasp_final.png'
    }

    data_df = run_benchmarks(CONFIG)
    plot_analysis(data_df, CONFIG)
    data_df.to_csv("resultados_investigacion_etapa1.csv", index=False)