from unicodedata import normalize

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, Value, When
from django.db.models.fields import CharField
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND
from xworkflows.base import InvalidTransitionError

from sme_terceirizadas.dados_comuns.fluxo_status import GuiaRemessaWorkFlow, SolicitacaoRemessaWorkFlow
from sme_terceirizadas.escola.models import Escola
from sme_terceirizadas.logistica.api.serializers.serializers import (
    GuiaDaRemessaComAlimentoSerializer,
    GuiaDaRemessaSerializer
)
from sme_terceirizadas.logistica.models import Guia
from sme_terceirizadas.logistica.models.guia import ConferenciaIndividualPorAlimento, InsucessoEntregaGuia

status_invalidos_para_conferencia = (
    GuiaRemessaWorkFlow.CANCELADA,
    GuiaRemessaWorkFlow.AGUARDANDO_ENVIO,
    GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO
)

status_alimento_recebido = ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_RECEBIDO
status_alimento_nao_recebido = ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_NAO_RECEBIDO
status_alimento_parcial = ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_PARCIAL
ocorrencia_em_atraso = ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA


def remove_acentos_de_strings(nome: str) -> str:
    return normalize('NFKD', nome).encode('ASCII', 'ignore').decode('ASCII')


def retorna_status_das_requisicoes(status_list: list) -> list:  # noqa C901
    lista_com_status = []
    todos_status = [SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO,
                    SolicitacaoRemessaWorkFlow.DILOG_ENVIA,
                    SolicitacaoRemessaWorkFlow.PAPA_CANCELA,
                    SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA,
                    SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_SOLICITA_ALTERACAO]
    if len(status_list) == 0:
        return todos_status
    elif len(status_list) == 1:
        if status_list[0] == ' ' or status_list[0] == '':
            return todos_status
    for status in status_list:
        if status == 'Todos':
            return todos_status
        elif status == 'Aguardando envio':
            lista_com_status.append(
                SolicitacaoRemessaWorkFlow.AGUARDANDO_ENVIO
            )
        elif status == 'Enviada':
            lista_com_status.append(
                SolicitacaoRemessaWorkFlow.DILOG_ENVIA
            )
        elif status == 'Cancelada':
            lista_com_status.append(
                SolicitacaoRemessaWorkFlow.PAPA_CANCELA
            )
        elif status == 'Confirmada':
            lista_com_status.append(
                SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_CONFIRMA
            )
        elif status == 'Em análise':
            lista_com_status.append(
                SolicitacaoRemessaWorkFlow.DISTRIBUIDOR_SOLICITA_ALTERACAO
            )
    return lista_com_status


def retorna_status_para_usuario(status_evento: str) -> str:  # noqa C901
    if status_evento == 'Papa enviou a requisição':
        return 'Aguardando envio'
    elif status_evento == 'Dilog Enviou a requisição':
        return 'Enviada'
    elif status_evento == 'Distribuidor confirmou requisição':
        return 'Confirmada'
    elif status_evento == 'Distribuidor pede alteração da requisição':
        return 'Em análise'
    else:
        return 'Cancelada'


def retorna_dados_normalizados_excel_visao_distribuidor(queryset):
    requisicoes = queryset.annotate(status_requisicao=Case(
        When(status='AGUARDANDO_ENVIO', then=Value('Aguardando envio')),
        When(status='DILOG_ENVIA', then=Value('Recebida')),
        When(status='CANCELADA', then=Value('Cancelada')),
        When(status='DISTRIBUIDOR_CONFIRMA', then=Value('Confirmada')),
        When(status='DISTRIBUIDOR_SOLICITA_ALTERACAO', then=Value('Em análise')),
        When(status='DILOG_ACEITA_ALTERACAO', then=Value('Alterada')),
        output_field=CharField(),
    )).values(
        'numero_solicitacao', 'status_requisicao', 'quantidade_total_guias', 'guias__numero_guia',
        'guias__data_entrega', 'guias__codigo_unidade', 'guias__nome_unidade', 'guias__endereco_unidade',
        'guias__endereco_unidade', 'guias__numero_unidade', 'guias__bairro_unidade', 'guias__cep_unidade',
        'guias__cidade_unidade', 'guias__estado_unidade', 'guias__contato_unidade', 'guias__telefone_unidade',
        'guias__alimentos__nome_alimento', 'guias__alimentos__codigo_suprimento', 'guias__alimentos__codigo_papa',
        'guias__alimentos__embalagens__tipo_embalagem', 'guias__alimentos__embalagens__descricao_embalagem',
        'guias__alimentos__embalagens__capacidade_embalagem', 'guias__alimentos__embalagens__unidade_medida',
        'guias__alimentos__embalagens__qtd_volume')

    return requisicoes


def retorna_dados_normalizados_excel_visao_dilog(queryset):
    requisicoes = queryset.annotate(status_requisicao=Case(
        When(status='AGUARDANDO_ENVIO', then=Value('Aguardando envio')),
        When(status='DILOG_ENVIA', then=Value('Enviada')),
        When(status='CANCELADA', then=Value('Cancelada')),
        When(status='DISTRIBUIDOR_CONFIRMA', then=Value('Confirmada')),
        When(status='DISTRIBUIDOR_SOLICITA_ALTERACAO', then=Value('Em análise')),
        When(status='DILOG_ACEITA_ALTERACAO', then=Value('Alterada')),
        output_field=CharField(),
    ), codigo_eol_unidade=Value('', output_field=CharField())).values(
        'distribuidor__nome_fantasia', 'numero_solicitacao', 'status_requisicao', 'quantidade_total_guias',
        'guias__numero_guia', 'guias__status', 'guias__data_entrega', 'guias__codigo_unidade', 'guias__nome_unidade',
        'guias__endereco_unidade', 'guias__endereco_unidade', 'guias__numero_unidade', 'guias__bairro_unidade',
        'guias__cep_unidade', 'guias__cidade_unidade', 'guias__estado_unidade', 'guias__contato_unidade',
        'guias__telefone_unidade', 'guias__alimentos__nome_alimento', 'guias__alimentos__codigo_suprimento',
        'guias__alimentos__codigo_papa', 'guias__alimentos__embalagens__tipo_embalagem', 'codigo_eol_unidade',
        'guias__alimentos__embalagens__descricao_embalagem', 'guias__alimentos__embalagens__capacidade_embalagem',
        'guias__alimentos__embalagens__unidade_medida', 'guias__alimentos__embalagens__qtd_volume')

    escolas = Escola.objects.all().values('codigo_eol', 'codigo_codae')

    for requisicao in requisicoes:
        for escola in escolas:
            if requisicao['guias__codigo_unidade'] == escola['codigo_codae']:
                requisicao['codigo_eol_unidade'] = escola.get('codigo_eol', '')

    return requisicoes


def retorna_dados_normalizados_excel_entregas_distribuidor(queryset): # noqa C901
    requisicoes = queryset.annotate(status_requisicao=Case(
        When(status='AGUARDANDO_ENVIO', then=Value('Aguardando envio')),
        When(status='DILOG_ENVIA', then=Value('Recebida')),
        When(status='CANCELADA', then=Value('Cancelada')),
        When(status='DISTRIBUIDOR_CONFIRMA', then=Value('Confirmada')),
        When(status='DISTRIBUIDOR_SOLICITA_ALTERACAO', then=Value('Em análise')),
        When(status='DILOG_ACEITA_ALTERACAO', then=Value('Alterada')),
        output_field=CharField(),
    )).values(
        'numero_solicitacao', 'status_requisicao', 'quantidade_total_guias', 'guias__numero_guia',
        'guias__data_entrega', 'guias__codigo_unidade', 'guias__escola__codigo_eol', 'guias__nome_unidade',
        'guias__endereco_unidade', 'guias__numero_unidade', 'guias__bairro_unidade', 'guias__cep_unidade',
        'guias__cidade_unidade', 'guias__estado_unidade', 'guias__contato_unidade', 'guias__telefone_unidade',
        'guias__alimentos__nome_alimento', 'guias__alimentos__codigo_suprimento', 'guias__alimentos__codigo_papa',
        'guias__alimentos__embalagens__tipo_embalagem', 'guias__alimentos__embalagens__descricao_embalagem',
        'guias__alimentos__embalagens__capacidade_embalagem', 'guias__alimentos__embalagens__unidade_medida',
        'guias__alimentos__embalagens__qtd_volume', 'guias__status', 'guias__alimentos__embalagens__qtd_a_receber',
        'guias__insucessos__placa_veiculo', 'guias__insucessos__nome_motorista', 'guias__insucessos__criado_em',
        'guias__insucessos__hora_tentativa', 'guias__insucessos__motivo', 'guias__insucessos__justificativa',
        'guias__insucessos__criado_por__cpf', 'guias__insucessos__criado_por__nome', 'distribuidor__nome_fantasia')

    for requisicao in requisicoes:
        for guia in queryset[0].guias.all():
            if guia.numero_guia == requisicao['guias__numero_guia']:
                if guia.conferencias.first():
                    conferencias = guia.conferencias.all().order_by('criado_em')
                    requisicao['primeira_conferencia'] = conferencias[0]
                    conferencia_alimento = alinhaAlimentos(requisicao, conferencias[0])
                    if conferencia_alimento:
                        requisicao['conferencia_alimento'] = conferencia_alimento
                    for conferencia in conferencias:
                        if conferencia.eh_reposicao:
                            requisicao['primeira_reposicao'] = conferencia
                            reposicao_alimento = alinhaAlimentos(requisicao, conferencia)
                            if reposicao_alimento:
                                requisicao['reposicao_alimento'] = reposicao_alimento
                            break

    return requisicoes


def alinhaAlimentos(requisicao, conferencia):
    for conf_alim in conferencia.conferencia_dos_alimentos.all():
        if conf_alim.nome_alimento == requisicao['guias__alimentos__nome_alimento']:
            return conf_alim


def valida_guia_conferencia(queryset, escola):
    if queryset.count() == 0:
        return Response(dict(detail=f'Erro: Guia não encontrada', status=False),
                        status=HTTP_404_NOT_FOUND)
    guia = queryset.first()
    if guia.status in status_invalidos_para_conferencia:
        return Response(dict(
            detail=f'Erro ao buscar guia: Essa guia não está pronta para o processo de conferencia'
        ), status=HTTP_400_BAD_REQUEST)
    if guia.escola != escola:
        return Response(dict(
            detail=f'Erro ao buscar guia: Essa guia não pertence a sua escola'
        ), status=HTTP_400_BAD_REQUEST)
    serializer = GuiaDaRemessaComAlimentoSerializer(guia)
    return Response(serializer.data)


def valida_guia_insucesso(queryset):
    if queryset.count() == 0:
        return Response(dict(detail=f'Erro: Guia não encontrada', status=False),
                        status=HTTP_404_NOT_FOUND)
    guia = queryset.first()
    if guia.status in status_invalidos_para_conferencia:
        return Response(dict(
            detail=f'Erro ao buscar guia: Essa guia não está pronta para registro de insucesso'
        ), status=HTTP_400_BAD_REQUEST)
    serializer = GuiaDaRemessaSerializer(guia)

    return Response(serializer.data)


def verifica_se_a_guia_pode_ser_conferida(guia):
    try:
        guia = Guia.objects.get(uuid=guia.uuid)
        if guia.status in status_invalidos_para_conferencia:
            raise ValidationError(f'Erro ao buscar guia: Essa guia ainda não pode ser conferida.')
    except ObjectDoesNotExist:
        raise ValidationError(f'Guia de remessa não existe.')


def atualiza_guia_com_base_nas_conferencias_por_alimentos(guia, user, status_dos_alimentos, eh_reposicao, ocorrencias_dos_alimentos):  # noqa C901
    """
    Método responsavel por chamar hooks de atualização de status das guias baseado nos status dos alimentos conferidos e
    no tipo de conferencia caso seja uma reposição.
    """
    try:
        guia_obj = Guia.objects.get(uuid=guia.uuid)
        if len(status_dos_alimentos) == 0:
            raise ValidationError(f'Status dos alimentos não foram informados.')
        try:
            if all(status == status_alimento_recebido for status in status_dos_alimentos):
                guia_obj.reposicao_total(user=user) if eh_reposicao else guia_obj.escola_recebe(user=user)
            elif all(status == status_alimento_nao_recebido for status in status_dos_alimentos):
                guia_obj.reposicao_parcial(user=user) if eh_reposicao else guia_obj.escola_nao_recebe(user=user)
            elif all(ocorrencia == ocorrencia_em_atraso for ocorrencia in ocorrencias_dos_alimentos):
                guia_obj.escola_recebe_parcial_atraso(user=user)
            else:
                guia_obj.reposicao_parcial(user=user) if eh_reposicao else guia_obj.escola_recebe_parcial(user=user)
        except InvalidTransitionError as e:
            raise ValidationError(f'Erro de transição de estado: {e}')

    except ObjectDoesNotExist:
        raise ValidationError(f'Guia de remessa não existe.')


def registra_qtd_a_receber(conferencia_individual):  # noqa C901
    try:
        guia = conferencia_individual.conferencia.guia
        nome_alimento = conferencia_individual.nome_alimento
        tipo_embalagem = conferencia_individual.tipo_embalagem

        alimento = guia.alimentos.get(nome_alimento=nome_alimento)
        embalagem = alimento.embalagens.get(tipo_embalagem=tipo_embalagem)
        if conferencia_individual.conferencia.eh_reposicao:
            embalagem.qtd_a_receber = embalagem.qtd_a_receber - conferencia_individual.qtd_recebido
        else:
            embalagem.qtd_a_receber = embalagem.qtd_volume - conferencia_individual.qtd_recebido
        if embalagem.qtd_a_receber < 0:
            embalagem.qtd_a_receber = 0
        embalagem.save()
    except ObjectDoesNotExist:
        raise ValidationError(f'Alimento ou embalagem não existe.')


def retorna_status_alimento(status):
    nomes_alimentos = ConferenciaIndividualPorAlimento.STATUS_ALIMENTO_NOMES
    switcher = {
        status_alimento_recebido: nomes_alimentos[status_alimento_recebido],
        status_alimento_nao_recebido: nomes_alimentos[status_alimento_nao_recebido],
        status_alimento_parcial: nomes_alimentos[status_alimento_parcial]
    }
    return switcher.get(status, 'Status Inválido')


def retorna_ocorrencias_alimento(ocorrencias):
    ocorrencias_retorno = []
    for ocorrencia in ocorrencias:
        nomes_ocorrencias = ConferenciaIndividualPorAlimento.OCORRENCIA_NOMES
        qtd_menor = ConferenciaIndividualPorAlimento.OCORRENCIA_QTD_MENOR
        prob_qualidade = ConferenciaIndividualPorAlimento.OCORRENCIA_PROBLEMA_QUALIDADE
        alimento_diferente = ConferenciaIndividualPorAlimento.OCORRENCIA_ALIMENTO_DIFERENTE
        embalagem_danificada = ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_DANIFICADA
        embalagem_violada = ConferenciaIndividualPorAlimento.OCORRENCIA_EMBALAGEM_VIOLADA
        validade_expirada = ConferenciaIndividualPorAlimento.OCORRENCIA_VALIDADE_EXPIRADA
        atraso_entrega = ConferenciaIndividualPorAlimento.OCORRENCIA_ATRASO_ENTREGA
        ausencia_produto = ConferenciaIndividualPorAlimento.OCORRENCIA_AUSENCIA_PRODUTO

        switcher = {
            qtd_menor: nomes_ocorrencias[qtd_menor],
            prob_qualidade: nomes_ocorrencias[prob_qualidade],
            alimento_diferente: nomes_ocorrencias[alimento_diferente],
            embalagem_danificada: nomes_ocorrencias[embalagem_danificada],
            embalagem_violada: nomes_ocorrencias[embalagem_violada],
            validade_expirada: nomes_ocorrencias[validade_expirada],
            atraso_entrega: nomes_ocorrencias[atraso_entrega],
            ausencia_produto: nomes_ocorrencias[ausencia_produto]
        }
        ocorrencias_retorno.insert(0, switcher.get(ocorrencia, 'Ocorrência Inválida'))
    return ', '.join(ocorrencias_retorno)


def retorna_status_guia_remessa(status):
    nomes_status = GuiaRemessaWorkFlow.states

    aguardando_envio = GuiaRemessaWorkFlow.AGUARDANDO_ENVIO
    aguardando_confirmacao = GuiaRemessaWorkFlow.AGUARDANDO_CONFIRMACAO
    pendente_conferencia = GuiaRemessaWorkFlow.PENDENTE_DE_CONFERENCIA
    insucesso = GuiaRemessaWorkFlow.DISTRIBUIDOR_REGISTRA_INSUCESSO
    recebida = GuiaRemessaWorkFlow.RECEBIDA
    nao_recebida = GuiaRemessaWorkFlow.NAO_RECEBIDA
    parcial = GuiaRemessaWorkFlow.RECEBIMENTO_PARCIAL
    repo_total = GuiaRemessaWorkFlow.REPOSICAO_TOTAL
    repo_parcial = GuiaRemessaWorkFlow.REPOSICAO_PARCIAL
    cancelada = GuiaRemessaWorkFlow.CANCELADA

    switcher = {
        aguardando_envio: nomes_status[aguardando_envio],
        aguardando_confirmacao: nomes_status[aguardando_confirmacao],
        pendente_conferencia: nomes_status[pendente_conferencia],
        insucesso: nomes_status[insucesso],
        recebida: nomes_status[recebida],
        nao_recebida: nomes_status[nao_recebida],
        parcial: nomes_status[parcial],
        repo_total: nomes_status[repo_total],
        repo_parcial: nomes_status[repo_parcial],
        cancelada: nomes_status[cancelada]
    }

    state = switcher.get(status, 'Status Inválido')
    return state.title


def valida_rf_ou_cpf(user):
    if user.registro_funcional is None:
        return user.cpf
    else:
        return user.registro_funcional


def retorna_motivo_insucesso(motivo):
    nomes_motivos = InsucessoEntregaGuia.MOTIVO_NOMES

    ue_fechada = InsucessoEntregaGuia.MOTIVO_UNIDADE_FECHADA
    outros = InsucessoEntregaGuia.MOTIVO_OUTROS

    switcher = {
        ue_fechada: nomes_motivos[ue_fechada],
        outros: nomes_motivos[outros],
    }

    return switcher.get(motivo, 'Motivo Inválido')
