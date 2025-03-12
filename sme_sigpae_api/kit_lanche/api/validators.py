from django.db.models import Sum
from rest_framework import serializers

from ...dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from ..models import EscolaQuantidade, SolicitacaoKitLanche, SolicitacaoKitLancheAvulsa


def solicitacao_deve_ter_1_ou_mais_kits(numero_kits: int):
    deve_ter_1_ou_mais_kit = numero_kits >= 1
    if not deve_ter_1_ou_mais_kit:
        raise serializers.ValidationError(
            "Quando lista_kit_lanche_igual é Verdadeiro, "
            '"solicitacao_kit_lanche", deve ter de 1 a 3 kits'
        )
    return True


def solicitacao_deve_ter_0_kit(numero_kits: int):
    deve_ter_nenhum_kit = numero_kits == 0
    if not deve_ter_nenhum_kit:
        raise serializers.ValidationError(
            'Em "solicitacao_kit_lanche", quando lista_kit_lanche NÃO é igual, deve ter 0 kit'
        )
    return True


def escola_quantidade_deve_ter_0_kit(
    numero_kits: int,
    indice: int,
):
    deve_ter_nenhum_kit = numero_kits == 0
    if not deve_ter_nenhum_kit:
        raise serializers.ValidationError(
            f"escola_quantidade indice # {indice} deve ter 0 kit"
            " pois a lista é igual para todas as escolas"
        )
    return True


def escola_quantidade_deve_ter_1_ou_mais_kits(
    numero_kits: int,
    indice: int,
):
    deve_ter_um_ou_mais = numero_kits >= 1
    if not deve_ter_um_ou_mais:
        raise serializers.ValidationError(
            f"escola_quantidade indice # {indice} deve ter 1 ou mais kits"
        )
    return True


def escola_quantidade_nao_deve_ter_kits_e_tempo_passeio(
    num_kits, tempo_passeio, indice
):
    vazio = num_kits == 0 and tempo_passeio is None
    if not vazio:
        raise serializers.ValidationError(
            f"escola_quantidade indice #{indice} "
            "deve ter kits = [] e tempo passeio nulo"
        )


def escola_quantidade_pedido_nao_pode_ser_mais_que_alunos(
    escola, quantidade_alunos_pedido, indice
):
    if quantidade_alunos_pedido > escola.quantidade_alunos:
        raise serializers.ValidationError(
            f"escola {escola.nome} tem menos alunos que a quantidade pedida "
            f"{quantidade_alunos_pedido}. Ver indice #{indice}"
        )


def escola_quantidade_deve_ter_mesmo_tempo_passeio(
    escola_quantidade, solicitacao_kit_lanche, indice
):
    tempo_passeio_escola = escola_quantidade.get("tempo_passeio")
    tempo_passeio_geral = solicitacao_kit_lanche.get("tempo_passeio")

    if tempo_passeio_escola != tempo_passeio_geral:
        raise serializers.ValidationError(
            f"escola_quantidade indice #{indice} diverge do tempo_passeio"
            f" de solicitacao_kit_lanche. Esperado: {tempo_passeio_geral}, recebido: {tempo_passeio_escola}"
        )
    return True


def valida_tempo_passeio_lista_igual(tempo_passeio):
    horas = [h[0] for h in EscolaQuantidade.HORAS]
    tentativa1 = tempo_passeio in horas
    if not tentativa1:
        raise serializers.ValidationError(
            "Quando o lista_kit_lanche_igual for Verdadeiro, tempo de passeio deve "
            f"ser qualquer uma das opções: {horas}."
        )
    return True


def valida_tempo_passeio_lista_nao_igual(tempo_passeio):
    tentativa2 = tempo_passeio is None

    if not tentativa2:
        raise serializers.ValidationError(
            "Quando o lista_kit_lanche_igual for Falso, tempo de passeio deve "
            "ser null. Cada escola deve ter uma "
            "especificação própria dos seus kit-lanches."
        )
    return True


def valida_quantidade_kits_tempo_passeio(tempo_passeio, quantidade_kits):  # noqa C901
    if tempo_passeio == SolicitacaoKitLanche.QUATRO:
        if quantidade_kits != 1:
            raise serializers.ValidationError(
                f"Tempo de passeio {tempo_passeio} de quatro horas deve ter 1 kit"
            )
    elif tempo_passeio == SolicitacaoKitLanche.CINCO_A_SETE:
        if quantidade_kits != 2:
            raise serializers.ValidationError(
                f"Tempo de passeio {tempo_passeio} de cinco a sete horas deve ter 2 kits"
            )
    elif tempo_passeio == SolicitacaoKitLanche.OITO_OU_MAIS:
        if quantidade_kits != 3:
            raise serializers.ValidationError(
                f"Tempo de passeio {tempo_passeio} de oito ou mais horas deve ter 3 kits"
            )
    return True


def nao_deve_ter_mais_solicitacoes_que_alunos(solicitacao_avulsa):
    """Impede solicitar mais do que a quantidade de alunos que a escola tem.

    Quando a solicitação sai de rascunho para inicio de fluxo, não deve deixar passar
    caso tenha mais  quantidade_aluno_passeio que a quantidade de alunos da escola.
    """
    data = solicitacao_avulsa.data
    escola = solicitacao_avulsa.escola
    if escola.tipo_unidade.iniciais not in ["CEU GESTAO", "CMCT"]:
        quantidade_aluno_passeio = solicitacao_avulsa.quantidade_alunos

        solicitacoes = SolicitacaoKitLancheAvulsa.objects.filter(
            escola=escola,
            status__in=[
                PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
                PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO,
                PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO,
                PedidoAPartirDaEscolaWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            ],
            solicitacao_kit_lanche__data=data,
        ).aggregate(Sum("quantidade_alunos"))

        if solicitacoes.get("quantidade_alunos__sum") is None:
            quantidade_alunos = 0
        else:
            quantidade_alunos = int(solicitacoes.get("quantidade_alunos__sum"))  # type: ignore
        quantidade_alunos_total_passeio = quantidade_alunos + quantidade_aluno_passeio
        if quantidade_alunos_total_passeio > escola.quantidade_alunos:
            raise serializers.ValidationError(
                "A quantidade de alunos informados para o evento excede a quantidade de alunos matriculados na escola."
                f' Na data {data.strftime("%d-%m-%Y")} já tem pedidos para {quantidade_alunos} alunos'
            )
