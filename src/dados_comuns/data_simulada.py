import datetime
from contextvars import ContextVar

_data_simulada = ContextVar("data_simulada", default=None)


def definir_data_simulada(data):
    return _data_simulada.set(data)


def limpar_data_simulada(token):
    _data_simulada.reset(token)


def obter_data_atual():
    return _data_simulada.get() or datetime.date.today()
