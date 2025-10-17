# 5 médicos
# 2 salas de Cirurgia
# 10 Leitos
# 25 pacientes

leitos = 10
salas = 2
medicos = 5

import threading, time

# Consulta precisa de 1 paciente e 1 médico
def consulta():
    print(f"Foi iniciada uma consulta.")
    time.sleep(8)
    print(f"Foi terminada a consulta.")

def exame():
    print(f"Um exame foi iniciado.")
    time.sleep(6)
    print(f"Um exame foi terminado.")


def cirurgia():
    print(f"Foi iniciada uma cirurgia.")
    time.sleep(12)
    print(f"Foi encerrada a cirurgia.")

def leito():
    print(f"Um leito está sendo ocupado.")