import datetime

import pytest
from model_bakery import baker

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers import (
    AlteracaoCardapioSerializer,
    MotivoAlteracaoCardapioSerializer,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    AlteracaoCardapio,
    MotivoAlteracaoCardapio,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
)
from sme_sigpae_api.dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 1), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 2), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 3), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 9, 30), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 9, 29), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 9, 28), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
    ]
)
def datas_alteracao_vencida(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 4), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 5), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 6), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 10, 7), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 8), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 9), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
    ]
)
def datas_alteracao_semana(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicial, status
        ((2019, 10, 4), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 10), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 10, 15), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
        ((2019, 10, 20), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 30), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        ((2019, 11, 4), PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR),
    ]
)
def datas_alteracao_mes(request):
    return request.param


@pytest.fixture
def substituicoes_alimentacao_periodo(escola):
    alteracao_cardapio = baker.make(
        AlteracaoCardapio, escola=escola, observacao="teste"
    )
    return baker.make(
        SubstituicaoAlimentacaoNoPeriodoEscolar,
        uuid="59beb0ca-982a-49da-98b8-10a296f274ba",
        alteracao_cardapio=alteracao_cardapio,
    )


@pytest.fixture
def motivo_alteracao_cardapio_serializer():
    motivo_alteracao_cardapio = baker.make(MotivoAlteracaoCardapio)
    return MotivoAlteracaoCardapioSerializer(motivo_alteracao_cardapio)


@pytest.fixture
def alteracao_cardapio_serializer(escola):
    alteracao_cardapio = baker.make(AlteracaoCardapio, escola=escola)
    return AlteracaoCardapioSerializer(alteracao_cardapio)


@pytest.fixture
def inclusao_normal_autorizada_periodo_manha(
    escola_com_dias_nao_letivos, periodo_manha
):
    grupo_inclusao_normal = baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_com_dias_nao_letivos,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data="2023-11-19",
    )
    baker.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=100,
        periodo_escolar=periodo_manha,
    )
    return grupo_inclusao_normal


@pytest.fixture
def inclusao_normal_autorizada_periodo_tarde(escola_com_dias_letivos, periodo_tarde):
    grupo_inclusao_normal = baker.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
    )
    baker.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data="2023-11-19",
    )
    baker.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=100,
        periodo_escolar=periodo_tarde,
    )
    return grupo_inclusao_normal


@pytest.fixture
def inclusao_continua_autorizada_periodo_manha(
    escola_com_dias_nao_letivos, periodo_manha
):
    inclusao_continua = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_nao_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_continua,
        numero_alunos=100,
        periodo_escolar=periodo_manha,
        dias_semana=[5, 6],
    )
    return inclusao_continua


@pytest.fixture
def inclusao_continua_autorizada_periodo_manha_dias_semana(
    escola_com_dias_letivos, periodo_manha
):
    inclusao_continua = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_continua,
        numero_alunos=100,
        periodo_escolar=periodo_manha,
        dias_semana=[3, 4],
    )
    return inclusao_continua


@pytest.fixture
def inclusao_continua_autorizada_periodo_tarde(escola_com_dias_letivos, periodo_tarde):
    inclusao_continua = baker.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    baker.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_continua,
        numero_alunos=100,
        periodo_escolar=periodo_tarde,
        dias_semana=[5, 6],
    )
    return inclusao_continua


@pytest.fixture
def alteracao_cardapio(escola, template_mensagem_alteracao_cardapio):
    return baker.make(
        AlteracaoCardapio,
        escola=escola,
        observacao="teste",
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )


@pytest.fixture
def alteracao_cardapio_com_datas_intervalo(
    escola, template_mensagem_alteracao_cardapio
):
    alteracao = baker.make(
        AlteracaoCardapio,
        escola=escola,
        observacao="teste",
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 10, 6),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
    )
    baker.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-04",
        alteracao_cardapio=alteracao,
    )
    baker.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-05",
        alteracao_cardapio=alteracao,
    )
    baker.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-06",
        alteracao_cardapio=alteracao,
    )
    return alteracao


@pytest.fixture
def alteracao_cardapio_outra_dre(
    escola_dre_guaianases, template_mensagem_alteracao_cardapio
):
    return baker.make(
        AlteracaoCardapio,
        escola=escola_dre_guaianases,
        observacao="teste",
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 12, 31),
        rastro_escola=escola_dre_guaianases,
        rastro_dre=escola_dre_guaianases.diretoria_regional,
    )


@pytest.fixture
def alteracao_cardapio_dre_validar(alteracao_cardapio):
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    alteracao_cardapio.save()
    return alteracao_cardapio


@pytest.fixture
def alteracao_cardapio_dre_validado(alteracao_cardapio):
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    alteracao_cardapio.save()
    return alteracao_cardapio


@pytest.fixture
def alteracao_cardapio_codae_autorizado(alteracao_cardapio):
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    alteracao_cardapio.save()
    return alteracao_cardapio


@pytest.fixture
def alteracao_cardapio_codae_questionado(alteracao_cardapio):
    alteracao_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    alteracao_cardapio.save()
    return alteracao_cardapio


@pytest.fixture()
def daqui_dez_dias_ou_ultimo_dia_do_ano():
    hoje = datetime.date.today()
    dia_alteracao = hoje + datetime.timedelta(days=10)
    if dia_alteracao.year != hoje.year:
        dia_alteracao = datetime.date(hoje.year, 12, 31)
    return dia_alteracao


@pytest.fixture(
    params=[
        # data do teste 15 out 2019
        # data_inicial, data_final
        (datetime.date(2019, 10, 17), datetime.date(2019, 10, 26)),
        (datetime.date(2019, 10, 18), datetime.date(2019, 10, 26)),
        (datetime.date(2020, 10, 11), datetime.date(2019, 10, 26)),
    ]
)
def alteracao_substituicoes_params(request, daqui_dez_dias_ou_ultimo_dia_do_ano):
    alimentacao1 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao1")
    alimentacao2 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao2")
    alimentacao3 = baker.make("cardapio.TipoAlimentacao", nome="tp_alimentacao3")
    periodo_escolar = baker.make("escola.PeriodoEscolar", nome="MANHA")
    tipo_unidade_escolar = baker.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    escola = baker.make(
        "escola.Escola", nome="PERICLIS", tipo_unidade=tipo_unidade_escolar
    )
    baker.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_escolar,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[alimentacao1, alimentacao2, alimentacao3],
    )
    motivo = baker.make(
        "cardapio.MotivoAlteracaoCardapio",
        nome="outro",
        uuid="478b09e1-4c14-4e50-a446-fbc0af727a09",
    )
    data_inicial, data_final = request.param
    return {
        "observacao": "<p>teste</p>\n",
        "motivo": str(motivo.uuid),
        "status": "DRE_A VALIDAR",
        "alterar_dia": daqui_dez_dias_ou_ultimo_dia_do_ano.isoformat(),
        "quantidades_periodo_TARDE": {"numero_de_alunos": "30"},
        "eh_alteracao_com_lanche_repetida": False,
        "escola": str(escola.uuid),
        "substituicoes": [
            {
                "periodo_escolar": str(periodo_escolar.uuid),
                "tipos_alimentacao_de": [
                    str(alimentacao1.uuid),
                    str(alimentacao2.uuid),
                ],
                "tipos_alimentacao_para": [str(alimentacao3.uuid)],
                "qtd_alunos": 10,
            }
        ],
        "datas_intervalo": [
            {"data": "2019-10-17"},
            {"data": "2019-10-18"},
            {"data": "2019-10-19"},
        ],
        "data_inicial": daqui_dez_dias_ou_ultimo_dia_do_ano.isoformat(),
        "data_final": daqui_dez_dias_ou_ultimo_dia_do_ano.isoformat(),
    }
