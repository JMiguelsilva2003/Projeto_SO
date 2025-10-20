import multiprocessing as mp
import time
import random
from resources import HospitalResourceManager, ResourceConfig

def paciente(recursos: HospitalResourceManager, nome: str, precisa_cirurgia: bool, precisa_exames: bool):
    """
    Executa o fluxo de um paciente:

    1) Consulta (aloca um médico -> realiza -> libera o médico)
    2) Exames (simulados sem recursos compartilhados; apenas tempo de execução)
    3) Cirurgia (aloca médico e sala -> realiza -> libera os dois)
    4) Recuperação (aloca um leito pós-cirurgia -> realiza -> libera o leito)

    - Usa timeouts para simular fila/espera e desistência caso falte recurso
    - Em caso de falha ao alocar a sala, o médico é liberado imediatamente
    """
    # Consulta (paciente + médico)
    medico = recursos.alocar_medico(timeout=3)
    if not medico:
        print(f"{nome}: desistiu (sem médico para consulta).")
        return
    print(f"{nome}: consulta com {medico}")
    time.sleep(random.uniform(0.2, 0.5))
    recursos.liberar_medico(medico)

    # Exames (sem recursos compartilhados aqui, apenas simulação)
    if precisa_exames:
        print(f"{nome}: realizando exames")
        time.sleep(random.uniform(0.1, 0.3))

    # Cirurgia (sala + médico)
    if precisa_cirurgia:
        medico = recursos.alocar_medico(timeout=5)
        if not medico:
            print(f"{nome}: sem médico para cirurgia.")
            return
        sala = recursos.alocar_sala_cirurgia(timeout=5)
        if not sala:
            print(f"{nome}: sem sala para cirurgia (liberando médico).")
            recursos.liberar_medico(medico)
            return

        print(f"{nome}: cirurgia na {sala} com {medico}")
        time.sleep(random.uniform(0.3, 0.7))
        recursos.liberar_sala_cirurgia(sala)
        recursos.liberar_medico(medico)

        # Leito (leito + médico não é necessário se médico já foi liberado; aqui só leito)
        leito = recursos.alocar_leito(timeout=5)
        if not leito:
            print(f"{nome}: sem leito após cirurgia.")
            return
        print(f"{nome}: recuperação no {leito}")
        time.sleep(random.uniform(0.2, 0.5))
        recursos.liberar_leito(leito)
    else:
        print(f"{nome}: alta sem cirurgia.")

if __name__ == "__main__":
    # Ponto de entrada (necessário no Windows para multiprocessing):
    # - Evita que processos filhos reinicializem o módulo ao spawn
    #
    # Configuração de recursos do hospital:
    # - 5 médicos, 2 salas de cirurgia, 10 leitos
    #
    # Criação do gerente de recursos compartilhados que será passado a cada paciente
    config = ResourceConfig(medicos=5, salas_cirurgia=2, leitos=10)
    recursos = HospitalResourceManager(config)

    processos = []
    for i in range(25):
        nome = f"Paciente-{i+1}"
        precisa_cirurgia = random.random() < 0.4
        precisa_exames = random.random() < 0.7
        p = mp.Process(target=paciente, args=(recursos, nome, precisa_cirurgia, precisa_exames))
        processos.append(p)
        p.start()

    for p in processos:
        p.join()

    print("Status final:", recursos.status())