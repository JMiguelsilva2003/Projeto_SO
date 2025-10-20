import threading
import time
import random
from resources import HospitalResourceManager

def thread_consulta(id_paciente: int, manager: HospitalResourceManager, evento_sucesso: threading.Event):
    """
    Simula a atividade de consulta.
    Requer: 1 médico.
    """
    print(f"[Paciente {id_paciente}] -- Aguardando médico para consulta...")
    
    # Tenta alocar um médico
    medico_id = manager.alocar_medico()
    
    if medico_id:
        print(f"[Paciente {id_paciente}] >> Iniciou consulta com {medico_id}.")
        time.sleep(random.uniform(1, 3)) # Simula o tempo da consulta
        print(f"[Paciente {id_paciente}] << Finalizou consulta com {medico_id}.")
        manager.liberar_medico(medico_id)
        evento_sucesso.set() # Sinaliza que a consulta foi um sucesso
    else:
        print(f"[Paciente {id_paciente}] !! DESISTIU (sem médico para consulta).")

def thread_exames(id_paciente: int, manager: HospitalResourceManager):
    """
    [cite_start]Simula a atividade de exames. [cite: 12]
    Requer: Nenhum recurso partilhado (conforme descrição).
    """
    print(f"[Paciente {id_paciente}] >> Iniciou exames.")
    time.sleep(random.uniform(2, 4)) # Simula o tempo dos exames
    print(f"[Paciente {id_paciente}] << Finalizou exames.")

def thread_cirurgia(id_paciente: int, manager: HospitalResourceManager, evento_sucesso: threading.Event):
    """
    Simula a atividade de cirurgia.
    [cite_start]Requer: 1 médico E 1 sala de cirurgia. [cite: 13]
    """
    print(f"[Paciente {id_paciente}] -- Aguardando recursos para CIRURGIA...")
    
    # Tenta alocar um médico
    medico_id = manager.alocar_medico()
    if not medico_id:
        print(f"[Paciente {id_paciente}] !! FALHA CIRURGIA (sem médico disponível).")
        return # Falha

    # Tenta alocar uma sala
    sala_id = manager.alocar_sala_cirurgia()
    if not sala_id:
        print(f"[Paciente {id_paciente}] !! FALHA CIRURGIA (sem sala disponível). Liberando {medico_id}.")
        manager.liberar_medico(medico_id) # Devolve o médico, já que a sala falhou
        return # Falha

    # Se chegou aqui, conseguiu os dois recursos
    print(f"[Paciente {id_paciente}] >> Iniciou cirurgia na {sala_id} com {medico_id}.")
    time.sleep(random.uniform(5, 10)) # Simula o tempo da cirurgia
    print(f"[Paciente {id_paciente}] << Finalizou cirurgia. Liberando {sala_id} e {medico_id}.")
    
    manager.liberar_sala_cirurgia(sala_id)
    manager.liberar_medico(medico_id)
    
    # Sinaliza para o processo principal que a cirurgia foi um sucesso
    evento_sucesso.set()

def thread_leito(id_paciente: int, manager: HospitalResourceManager):
    """
    Simula a atividade de recuperação no leito.
    [cite_start]Requer: 1 leito. [cite: 13]
    """
    print(f"[Paciente {id_paciente}] -- Aguardando leito para recuperação...")
    
    # Tenta alocar um leito
    leito_id = manager.alocar_leito()
    
    if leito_id:
        print(f"[Paciente {id_paciente}] >> Ocupou {leito_id}.")
        time.sleep(random.uniform(3, 6)) # Simula o tempo no leito
        print(f"[Paciente {id_paciente}] << Liberou {leito_id}.")
        manager.liberar_leito(leito_id)
    else:
        print(f"[Paciente {id_paciente}] !! ALTA SEM LEITO (sem leito disponível para recuperação).")