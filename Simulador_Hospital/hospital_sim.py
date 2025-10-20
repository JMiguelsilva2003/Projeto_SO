import multiprocessing
import threading
import time
import random

# Importa o gestor de recursos
from resources import HospitalResourceManager 

# Importa as threads de atividades
from atividades import thread_consulta, thread_exames, thread_cirurgia, thread_leito

def fluxo_paciente(id_paciente: int, manager: HospitalResourceManager):
    """
    Representa o processo de um único paciente e seu fluxo no hospital.
    [cite_start]Este é o "processo" paciente. [cite: 10]
    """
    print(f"[Paciente {id_paciente}] *** Deu entrada no hospital. ***")

    # 1. Todo paciente realiza uma consulta
    # Usamos um Evento para saber se a consulta foi bem-sucedida
    consulta_ok_evento = threading.Event()
    t_consulta = threading.Thread(
        target=thread_consulta, 
        args=(id_paciente, manager, consulta_ok_evento)
    )
    t_consulta.start()
    t_consulta.join() 

    # Se a consulta falhou (ex: sem médico), o paciente vai embora
    if not consulta_ok_evento.is_set():
        print(f"[Paciente {id_paciente}] *** Deixou o hospital (consulta falhou). ***")
        return # Termina o processo deste paciente

    # 2. Todo paciente faz exames após a consulta
    t_exames = threading.Thread(target=thread_exames, args=(id_paciente, manager))
    t_exames.start()
    t_exames.join() 

    # 3. Decide aleatoriamente se o paciente precisa de cirurgia
    precisa_cirurgia = random.choice([True, False])

    if precisa_cirurgia:
        print(f"[Paciente {id_paciente}] --- Diagnóstico: Precisa de cirurgia. ---")

        cirurgia_ok_evento = threading.Event()
        
        # 4. Paciente faz cirurgia
        t_cirurgia = threading.Thread(
            target=thread_cirurgia, 
            args=(id_paciente, manager, cirurgia_ok_evento)
        )
        t_cirurgia.start()
        t_cirurgia.join()

        # 5. Após a cirurgia, vai para um leito (SE a cirurgia teve sucesso)
        if cirurgia_ok_evento.is_set():
            t_leito = threading.Thread(target=thread_leito, args=(id_paciente, manager))
            t_leito.start()
            t_leito.join()
            print(f"[Paciente {id_paciente}] *** Recebeu alta (pós-cirurgia). ***")
        else:
            print(f"[Paciente {id_paciente}] *** Recebeu alta (cirurgia falhou ou foi cancelada). ***")
    
    else:
        # Paciente que não precisa de cirurgia
        print(f"[Paciente {id_paciente}] --- Diagnóstico: Não precisa de cirurgia. ---")
        print(f"[Paciente {id_paciente}] *** Recebeu alta (pós-exames). ***")


def iniciar_simulacao(num_pacientes: int, manager: HospitalResourceManager):
    """
    Cria e inicia os processos dos pacientes.
    """
    print(f"--- Iniciando simulação com {num_pacientes} pacientes. ---")
    processos_pacientes = []

    for i in range(num_pacientes):
        # Cada paciente é um processo
        p = multiprocessing.Process(target=fluxo_paciente, args=(i + 1, manager))
        processos_pacientes.append(p)
        p.start()
        time.sleep(random.uniform(0, 0.5)) # Simula pacientes chegando em momentos diferentes

    # Espera todos os pacientes terminarem seus fluxos
    for p in processos_pacientes:
        p.join()

    print("--- Simulação finalizada. Todos os pacientes foram atendidos. ---")