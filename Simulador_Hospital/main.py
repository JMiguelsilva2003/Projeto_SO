import time
import logging

from resources import ResourceConfig, HospitalResourceManager

# Importa a função de simulação
from hospital_sim import iniciar_simulacao


if __name__ == "__main__":
    
    # 1. Configura os recursos
    config_hospital = ResourceConfig(
        medicos=5,        
        salas_cirurgia=2,
        leitos=10       
    )
    # Cria o gestor de recursos
    recursos_manager = HospitalResourceManager(config_hospital)
    
    # 2. Define o número de pacientes e inicia a simulação
    NUM_PACIENTES = 25
    
    print(">>> SIMULADOR DE HOSPITAL INICIADO <<<")
    tempo_inicio = time.time()
    
    # Chama a função principal do ficheiro hospital_sim.py
    iniciar_simulacao(NUM_PACIENTES, recursos_manager)
    
    tempo_fim = time.time()
    
    print("\n--- Estatísticas Finais ---")
    print(f"Tempo total de simulação: {tempo_fim - tempo_inicio:.2f} segundos")
    print("Status final dos recursos:", recursos_manager.status())
    print(">>> SIMULADOR DE HOSPITAL FINALIZADO <<<")