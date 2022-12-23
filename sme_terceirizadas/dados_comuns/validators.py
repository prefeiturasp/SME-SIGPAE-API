import calendar
import datetime

from django.db import models
from rest_framework import serializers
from workalendar.america import BrazilSaoPauloCity

from ..cardapio.models import (
    AlteracaoCardapio,
    AlteracaoCardapioCEI,
    AlteracaoCardapioCEMEI,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
)
from .constants import obter_dias_uteis_apos_hoje
from .utils import eh_dia_util

calendario = BrazilSaoPauloCity()


def nao_pode_ser_no_passado(data: datetime.date):
    if data < datetime.date.today():
        raise serializers.ValidationError('Não pode ser no passado')
    return True


def deve_ser_no_passado(data: datetime.date):
    if data > datetime.date.today():
        raise serializers.ValidationError('Deve ser data anterior a hoje')
    return True


def deve_pedir_com_antecedencia(dia: datetime.date, dias: int = 2):
    prox_dia_util = obter_dias_uteis_apos_hoje(quantidade_dias=dias)
    if dia < prox_dia_util:
        raise serializers.ValidationError(f'Deve pedir com pelo menos {dias} dias úteis de antecedência')
    return True


def valida_duplicidade_solicitacoes(attrs):
    status_permitidos = ['ESCOLA_CANCELOU', 'DRE_NAO_VALIDOU_PEDIDO_ESCOLA',
                         'CODAE_NEGOU_PEDIDO', 'RASCUNHO']
    periodos_uuids = [sub['periodo_escolar'].uuid for sub in attrs['substituicoes']]
    motivo = attrs['motivo'].uuid

    data_inicial_mes = attrs['data_inicial'].month
    data_inicial_ano = attrs['data_inicial'].year
    menor_data = datetime.datetime(data_inicial_ano, data_inicial_mes, 1)

    data_final_mes = attrs['data_final'].month
    data_final_ano = attrs['data_final'].year
    ultimo_dia_do_mes = calendar.monthrange(data_final_ano, data_final_mes)[1]
    maior_data = datetime.datetime(data_final_ano, data_final_mes, ultimo_dia_do_mes)

    substituicoes = SubstituicaoAlimentacaoNoPeriodoEscolar.objects.filter(periodo_escolar__uuid__in=periodos_uuids)
    alteracoes_pks = substituicoes.values_list('alteracao_cardapio', flat=True)
    solicitacoes = AlteracaoCardapio.objects.filter(motivo__uuid=motivo, pk__in=alteracoes_pks, escola=attrs['escola'])

    solicitacoes = solicitacoes.filter(data_inicial__gte=menor_data, data_final__lte=maior_data)
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)

    if solicitacoes:
        raise serializers.ValidationError(f'Já existe uma solicitação de RPL para o mês e período selecionado!')
    return True


def valida_duplicidade_solicitacoes_cei(attrs, data):
    status_permitidos = ['ESCOLA_CANCELOU', 'DRE_NAO_VALIDOU_PEDIDO_ESCOLA',
                         'CODAE_NEGOU_PEDIDO', 'RASCUNHO']
    periodos_uuids = [sub['periodo_escolar'] for sub in attrs['substituicoes']]
    motivo = attrs['motivo']

    mes = data.month
    ano = data.year
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    menor_data = datetime.datetime(ano, mes, 1)
    maior_data = datetime.datetime(ano, mes, ultimo_dia_do_mes)
    substituicoes = SubstituicaoAlimentacaoNoPeriodoEscolarCEI.objects.filter(periodo_escolar__uuid__in=periodos_uuids)
    alteracoes_pks = substituicoes.values_list('alteracao_cardapio', flat=True)
    solicitacoes = AlteracaoCardapioCEI.objects.filter(motivo__uuid=motivo, pk__in=alteracoes_pks,
                                                       escola__uuid=attrs['escola'])
    solicitacoes = solicitacoes.filter(data__gte=menor_data, data__lte=maior_data)
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)

    if solicitacoes:
        raise serializers.ValidationError(f'Já existe uma solicitação de RPL para o mês e período selecionado!')
    return True


def valida_duplicidade_solicitacoes_cemei(attrs):
    status_permitidos = ['ESCOLA_CANCELOU', 'DRE_NAO_VALIDOU_PEDIDO_ESCOLA',
                         'CODAE_NEGOU_PEDIDO', 'RASCUNHO']
    periodos_uuids = [sub['periodo_escolar'].uuid for sub in attrs['substituicoes_cemei_cei_periodo_escolar']]
    motivo = attrs['motivo'].uuid
    data = attrs['alterar_dia']
    mes = data.month
    ano = data.year
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    menor_data = datetime.datetime(ano, mes, 1)
    maior_data = datetime.datetime(ano, mes, ultimo_dia_do_mes)
    modelo_substituitos = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI
    substituicoes = modelo_substituitos.objects.filter(periodo_escolar__uuid__in=periodos_uuids)
    alteracoes_pks = substituicoes.values_list('alteracao_cardapio', flat=True)
    solicitacoes = AlteracaoCardapioCEMEI.objects.filter(motivo__uuid=motivo, pk__in=alteracoes_pks,
                                                         escola__uuid=attrs['escola'].uuid)
    solicitacoes = solicitacoes.filter(alterar_dia__gte=menor_data, alterar_dia__lte=maior_data)
    solicitacoes = solicitacoes.exclude(status__in=status_permitidos)
    if solicitacoes:
        raise serializers.ValidationError(f'Já existe uma solicitação de RPL para o mês e período selecionado!')
    return True


def deve_existir_cardapio(escola, data: datetime.date):
    if not escola.get_cardapio(data):
        raise serializers.ValidationError(f'Escola não possui cardápio para esse dia: {data.strftime("%d-%m-%Y")}')
    return True


def deve_ser_dia_letivo(escola, data: datetime.date):
    if not escola.calendario.get(data=data).dia_letivo:
        raise serializers.ValidationError(f'O dia {data.strftime("%d-%m-%Y")} não é dia letivo')
    return True


def datas_alteracao_cardapio_devem_ser_diferentes(datas_1, datas_2):
    for data_1 in datas_1:
        for data_2 in datas_2:
            if data_1 == data_2:
                raise serializers.ValidationError(f'As datas não podem ser repetidas')
    return True


def dia_util(data: datetime.date):
    if not eh_dia_util(data):
        raise serializers.ValidationError('Não é dia útil em São Paulo')
    return True


def verificar_se_existe(obj_model, **kwargs) -> bool:
    try:
        if not issubclass(obj_model, models.Model):
            raise TypeError('obj_model deve ser um "django models class"')
    except TypeError:
        raise TypeError('obj_model deve ser um "django models class"')
    existe = obj_model.objects.filter(**kwargs).exists()
    return existe


def objeto_nao_deve_ter_duplicidade(obj_model, mensagem='Objeto já existe', **kwargs, ):
    qtd = obj_model.objects.filter(**kwargs).count()
    if qtd:
        raise serializers.ValidationError(mensagem)


def nao_pode_ser_feriado(data: datetime.date, mensagem='Não pode ser no feriado'):
    if calendario.is_holiday(data):
        raise serializers.ValidationError(mensagem)


def campo_nao_pode_ser_nulo(valor, mensagem='Não pode ser nulo'):
    if not valor:
        raise serializers.ValidationError(mensagem)


def campo_deve_ser_deste_tipo(valor, tipo=str, mensagem='Deve ser do tipo texto'):
    if type(valor) is not tipo:
        raise serializers.ValidationError(mensagem)


def deve_ser_no_mesmo_ano_corrente(data_inversao: datetime.date):
    ano_corrente = datetime.date.today().year
    mes_corrente = datetime.date.today().month
    if ano_corrente != data_inversao.year and mes_corrente != 12:
        raise serializers.ValidationError(
            'Solicitação deve ser solicitada no ano corrente'
        )
    return True


def deve_ter_extensao_valida(nome: str):
    if nome.split('.')[len(nome.split('.')) - 1].lower() not in ['doc', 'docx', 'pdf', 'png', 'jpg', 'jpeg']:
        raise serializers.ValidationError('Extensão inválida')
    return nome


def deve_ter_extensao_xls_xlsx_pdf(nome: str):
    if nome.split('.')[len(nome.split('.')) - 1].lower() not in ['xls', 'xlsx', 'pdf']:
        raise serializers.ValidationError('Extensão inválida')
    return nome
