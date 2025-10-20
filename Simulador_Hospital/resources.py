import multiprocessing as mp
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
import logging
import queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class ResourceType(Enum):
    """
    Enumera os tipos de recursos compartilhados no hospital:
    - MEDICO: profissionais que atendem consultas e cirurgias
    - SALA_CIRURGIA: salas onde são realizadas cirurgias
    - LEITO: leitos utilizados para recuperação pós-cirurgia
    """
    MEDICO = "medico"
    SALA_CIRURGIA = "sala_cirurgia"
    LEITO = "leito"


@dataclass
class ResourceConfig:
    """
    Configuração de capacidades por tipo de recurso.

    Atributos:
    - medicos: quantidade de médicos disponíveis simultaneamente
    - salas_cirurgia: número de salas de cirurgia disponíveis
    - leitos: número de leitos de recuperação disponíveis
    """
    medicos: int = 5
    salas_cirurgia: int = 2
    leitos: int = 10


@dataclass
class ResourcePool:
    """
    Estrutura interna que representa o pool de um tipo de recurso.

    Atributos:
    - nome: prefixo textual para identificar o recurso (ex.: 'medico-1')
    - capacidade: quantidade máxima de recursos simultâneos
    - semaforo: limita concorrência ao tamanho da capacidade
    - fila: Queue FIFO contendo IDs concretos dos recursos disponíveis
    """
    nome: str
    capacidade: int
    semaforo: mp.BoundedSemaphore
    fila: mp.Queue


class HospitalResourceManager:
    """
    Gerente de recursos do hospital.

    Responsabilidades:
    - Criar e manter pools de 'médicos', 'salas de cirurgia' e 'leitos'
    - Fornecer funções públicas para alocar/liberar cada tipo de recurso
    - Garantir fairness com distribuição FIFO de IDs
    - Suportar bloqueio e timeout ao tentar alocar recursos

    Implementação:
    - Semáforo (mp.BoundedSemaphore): controla a contagem máxima de alocações simultâneas
    - Fila (mp.Queue): distribui IDs concretos e evita condição de corrida
    """
    def __init__(self, config: ResourceConfig):
        """
        Inicializa os pools de recursos com base na configuração informada.

        - Cria logger e dicionário interno de pools
        - Invoca '_criar_pool' para 'MEDICO', 'SALA_CIRURGIA' e 'LEITO'
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._pools: Dict[ResourceType, ResourcePool] = {}

        self._criar_pool(ResourceType.MEDICO, config.medicos, "medico")
        self._criar_pool(ResourceType.SALA_CIRURGIA, config.salas_cirurgia, "sala")
        self._criar_pool(ResourceType.LEITO, config.leitos, "leito")

    def _criar_pool(self, tipo: ResourceType, capacidade: int, prefixo: str):
        """
        Cria pool para um tipo de recurso específico.

        - Instancia um BoundedSemaphore limitado por 'capacidade'
        - Preenche a Queue com IDs nomeados (prefixo-1 ... prefixo-N)
        - Armazena no dicionário interno e registra a criação em log
        """
        sem = mp.BoundedSemaphore(capacidade)
        fila = mp.Queue(maxsize=capacidade)
        for i in range(1, capacidade + 1):
            fila.put(f"{prefixo}-{i}")
        self._pools[tipo] = ResourcePool(nome=prefixo, capacidade=capacidade, semaforo=sem, fila=fila)
        self._logger.info(f"Pool criado: {prefixo} x{capacidade}")

    # --------- API pública: funções simples de alocar/liberar ---------
    def alocar_medico(self, blocking: bool = True, timeout: Optional[float] = None) -> Optional[str]:
        """
        Tenta alocar um médico e retorna o ID (ex.: 'medico-3').

        Parâmetros:
        - blocking: se True, espera pelo recurso; se False, tenta imediato
        - timeout: tempo máximo de espera (em segundos), se aplicável

        Retorno:
        - ID do médico alocado ou None em caso de timeout/falta de recurso
        """
        return self._alocar(ResourceType.MEDICO, blocking, timeout)

    def liberar_medico(self, id_recurso: str) -> None:
        """
        Libera o ID de médico previamente alocado.

        - Devolve o ID à fila e libera uma unidade no semáforo
        """
        self._liberar(ResourceType.MEDICO, id_recurso)

    def alocar_sala_cirurgia(self, blocking: bool = True, timeout: Optional[float] = None) -> Optional[str]:
        """
        Tenta alocar uma sala de cirurgia e retorna o ID (ex.: 'sala-1').

        Parâmetros e retorno seguem o mesmo contrato de 'alocar_medico'.
        """
        return self._alocar(ResourceType.SALA_CIRURGIA, blocking, timeout)

    def liberar_sala_cirurgia(self, id_recurso: str) -> None:
        """
        Libera o ID de sala de cirurgia previamente alocado.
        """
        self._liberar(ResourceType.SALA_CIRURGIA, id_recurso)

    def alocar_leito(self, blocking: bool = True, timeout: Optional[float] = None) -> Optional[str]:
        """
        Tenta alocar um leito e retorna o ID (ex.: 'leito-7').

        Parâmetros e retorno seguem o mesmo contrato de 'alocar_medico'.
        """
        return self._alocar(ResourceType.LEITO, blocking, timeout)

    def liberar_leito(self, id_recurso: str) -> None:
        """
        Libera o ID de leito previamente alocado.
        """
        self._liberar(ResourceType.LEITO, id_recurso)

    # --------- Utilidades ---------
    def status(self) -> Dict[str, Dict[str, int]]:
        """
        Retorna um snapshot aproximado do estado de cada pool.

        Saída:
        - dict com chaves 'medico', 'sala_cirurgia', 'leito'
        - para cada, um dict com:
          - 'disponiveis': tamanho atual da fila (aproximado em alguns SOs)
          - 'capacidade': capacidade máxima configurada
        """
        def _disp(tipo: ResourceType) -> int:
            try:
                return self._pools[tipo].fila.qsize()
            except NotImplementedError:
                return -1  # não suportado nesse SO

        return {
            ResourceType.MEDICO.value: {"disponiveis": _disp(ResourceType.MEDICO),
                                        "capacidade": self._pools[ResourceType.MEDICO].capacidade},
            ResourceType.SALA_CIRURGIA.value: {"disponiveis": _disp(ResourceType.SALA_CIRURGIA),
                                        "capacidade": self._pools[ResourceType.SALA_CIRURGIA].capacidade},
            ResourceType.LEITO.value: {"disponiveis": _disp(ResourceType.LEITO),
                                        "capacidade": self._pools[ResourceType.LEITO].capacidade},
        }

    # --------- Implementação interna ---------
    def _alocar(self, tipo: ResourceType, blocking: bool, timeout: Optional[float]) -> Optional[str]:
        """
        Implementação genérica de alocação usada pelos métodos públicos.

        Passos:
        1) Adquire o semáforo (usa 'block' e 'timeout' do multiprocessing)
        2) Consome um ID da fila de forma bloqueante (com timeout, se informado)
        3) Em caso de timeout na fila, reverte o semáforo e retorna None
        4) Loga o ID alocado e devolve-o ao chamador
        """
        pool = self._pools[tipo]
        # Adquire semáforo (controle de capacidade)
        ok = pool.semaforo.acquire(block=blocking, timeout=timeout)
        if not ok:
            self._logger.debug(f"Timeout ao alocar {pool.nome}.")
            return None
        try:
            # Consome ID da fila de forma bloqueante (sem janela de corrida)
            if blocking:
                if timeout is not None:
                    id_recurso = pool.fila.get(block=True, timeout=timeout)
                else:
                    id_recurso = pool.fila.get(block=True)
            else:
                id_recurso = pool.fila.get_nowait()
        except queue.Empty:
            # Se a fila estiver vazia, reverte o semáforo
            pool.semaforo.release()
            self._logger.debug(f"Timeout ao consumir ID de {pool.nome}.")
            return None
        self._logger.info(f"Alocado {pool.nome}: {id_recurso}")
        return id_recurso

    def _liberar(self, tipo: ResourceType, id_recurso: str) -> None:
        """
        Implementação genérica de liberação.

        Passos:
        1) Devolve o ID à fila (fica disponível para outro processo)
        2) Libera uma unidade no semáforo (incrementa a capacidade disponível)
        3) Loga o ID liberado
        """
        pool = self._pools[tipo]
        # Devolve ID à fila primeiro, depois libera semáforo
        pool.fila.put(id_recurso)
        pool.semaforo.release()
        self._logger.info(f"Liberado {pool.nome}: {id_recurso}")