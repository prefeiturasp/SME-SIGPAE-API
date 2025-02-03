import datetime

import pytest
from faker import Faker
from model_mommy import mommy
from rest_framework.test import APIClient

from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import (
    InformativoPartindoDaEscolaWorkflow,
    PedidoAPartirDaEscolaWorkflow,
)
from ...dados_comuns.models import TemplateMensagem
from ..api.serializers.serializers import (
    AlteracaoCardapioSerializer,
    GrupoSuspensaoAlimentacao,
    InversaoCardapioSerializer,
    MotivoAlteracaoCardapioSerializer,
    QuantidadePorPeriodoSuspensaoAlimentacao,
    SubstituicoesAlimentacaoNoPeriodoEscolarSerializer,
    SuspensaoAlimentacaoNoPeriodoEscolar,
    SuspensaoAlimentacaoSerializer,
)
from ..models import (
    AlteracaoCardapio,
    AlteracaoCardapioCEI,
    AlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    InversaoCardapio,
    MotivoAlteracaoCardapio,
    MotivoSuspensao,
    SubstituicaoAlimentacaoNoPeriodoEscolar,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
    SuspensaoAlimentacao,
    SuspensaoAlimentacaoDaCEI,
)

fake = Faker("pt_BR")
Faker.seed(420)


@pytest.fixture
def codae():
    return mommy.make("Codae")


@pytest.fixture
def tipo_alimentacao():
    return mommy.make("cardapio.TipoAlimentacao", nome="Refeição")


@pytest.fixture
def tipo_alimentacao_lanche_emergencial():
    return mommy.make("cardapio.TipoAlimentacao", nome="Lanche Emergencial")


@pytest.fixture
def client():
    client = APIClient()
    return client


@pytest.fixture
def cardapio_valido():
    cardapio_valido = mommy.make(
        "Cardapio",
        id=1,
        data=datetime.date(2019, 11, 29),
        uuid="7a4ec98a-18a8-4d0a-b722-1da8f99aaf4b",
        descricao="lorem ipsum",
    )
    return cardapio_valido


@pytest.fixture
def cardapio_valido2():
    cardapio_valido2 = mommy.make(
        "Cardapio",
        id=2,
        data=datetime.date(2019, 12, 15),
        uuid="7a4ec98a-18a8-4d0a-b722-1da8f99aaf4c",
    )
    return cardapio_valido2


@pytest.fixture
def cardapio_valido3():
    data = datetime.datetime.now() + datetime.timedelta(days=6)
    cardapio_valido = mommy.make("Cardapio", id=22, data=data.date())
    return cardapio_valido


@pytest.fixture
def cardapio_invalido():
    cardapio_invalido = mommy.prepare(
        "Cardapio",
        _save_related=True,
        id=3,
        data=datetime.date(2019, 7, 2),
        uuid="7a4ec98a-18a8-4d0a-b722-1da8f99aaf4d",
    )
    return cardapio_invalido


@pytest.fixture
def dre_guaianases():
    return mommy.make("DiretoriaRegional", nome="DIRETORIA REGIONAL GUAIANASES")


@pytest.fixture
def escola_dre_guaianases(dre_guaianases):
    lote = mommy.make("Lote")
    return mommy.make("Escola", lote=lote, diretoria_regional=dre_guaianases)


@pytest.fixture
def contato():
    return mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")


@pytest.fixture
def email_por_modulo(terceirizada):
    modulo = mommy.make("Modulo", nome="Gestão de Alimentação")
    email_por_modulo = mommy.make(
        "EmailTerceirizadaPorModulo",
        email="terceirizada.fake@email.com",
        modulo=modulo,
        terceirizada=terceirizada,
    )
    return email_por_modulo


@pytest.fixture
def periodo_manha():
    return mommy.make(
        "escola.PeriodoEscolar",
        nome="MANHA",
        uuid="42325516-aebd-4a3d-97c0-2a77c317c6be",
    )


@pytest.fixture
def periodo_tarde():
    return mommy.make(
        "escola.PeriodoEscolar",
        nome="TARDE",
        uuid="88966d6a-f9d5-4986-9ffb-25b6f41b0795",
    )


@pytest.fixture
def escola():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = mommy.make("TipoUnidadeEscolar", iniciais="EMEF")
    contato = mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )

    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="EMEF JOAO MENDES",
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def escola_com_vinculo_alimentacao(
    escola, periodo_manha, tipo_alimentacao, tipo_alimentacao_lanche_emergencial
):
    mommy.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_manha,
        tipo_unidade_escolar=escola.tipo_unidade,
        tipos_alimentacao=[tipo_alimentacao, tipo_alimentacao_lanche_emergencial],
    )
    return escola


@pytest.fixture
def escola_com_dias_letivos(escola_com_vinculo_alimentacao):
    mommy.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-18",
        dia_letivo=True,
    )
    mommy.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-19",
        dia_letivo=False,
    )
    return escola_com_vinculo_alimentacao


@pytest.fixture
def escola_com_dias_nao_letivos(escola_com_vinculo_alimentacao):
    mommy.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-18",
        dia_letivo=False,
    )
    mommy.make(
        "DiaCalendario",
        escola=escola_com_vinculo_alimentacao,
        data="2023-11-19",
        dia_letivo=False,
    )
    return escola_com_vinculo_alimentacao


@pytest.fixture
def inclusao_normal_autorizada_periodo_manha(
    escola_com_dias_nao_letivos, periodo_manha
):
    grupo_inclusao_normal = mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_com_dias_nao_letivos,
        status="CODAE_AUTORIZADO",
    )
    mommy.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data="2023-11-19",
    )
    mommy.make(
        "QuantidadePorPeriodo",
        grupo_inclusao_normal=grupo_inclusao_normal,
        numero_alunos=100,
        periodo_escolar=periodo_manha,
    )
    return grupo_inclusao_normal


@pytest.fixture
def inclusao_normal_autorizada_periodo_tarde(escola_com_dias_letivos, periodo_tarde):
    grupo_inclusao_normal = mommy.make(
        "GrupoInclusaoAlimentacaoNormal",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
    )
    mommy.make(
        "InclusaoAlimentacaoNormal",
        grupo_inclusao=grupo_inclusao_normal,
        data="2023-11-19",
    )
    mommy.make(
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
    inclusao_continua = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_nao_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    mommy.make(
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
    inclusao_continua = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    mommy.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_continua,
        numero_alunos=100,
        periodo_escolar=periodo_manha,
        dias_semana=[3, 4],
    )
    return inclusao_continua


@pytest.fixture
def inclusao_continua_autorizada_periodo_tarde(escola_com_dias_letivos, periodo_tarde):
    inclusao_continua = mommy.make(
        "InclusaoAlimentacaoContinua",
        escola=escola_com_dias_letivos,
        status="CODAE_AUTORIZADO",
        data_inicial="2023-11-01",
        data_final="2023-11-30",
    )
    mommy.make(
        "QuantidadePorPeriodo",
        inclusao_alimentacao_continua=inclusao_continua,
        numero_alunos=100,
        periodo_escolar=periodo_tarde,
        dias_semana=[5, 6],
    )
    return inclusao_continua


@pytest.fixture
def escola_cei():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = mommy.make("TipoUnidadeEscolar", iniciais="CEI DIRET")
    contato = mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )
    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="CEI DIRET JOAO MENDES",
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def escola_cemei():
    terceirizada = mommy.make("Terceirizada")
    lote = mommy.make("Lote", terceirizada=terceirizada)
    tipo_gestao = mommy.make("TipoGestao", nome="TERC TOTAL")
    tipo_unidade = mommy.make("TipoUnidadeEscolar", iniciais="CEMEI")
    contato = mommy.make("dados_comuns.Contato", nome="FULANO", email="fake@email.com")
    diretoria_regional = mommy.make(
        "DiretoriaRegional",
        nome="DIRETORIA REGIONAL IPIRANGA",
        uuid="012f7722-9ab4-4e21-b0f6-85e17b58b0d1",
    )
    escola = mommy.make(
        "Escola",
        lote=lote,
        nome="CEMEI JOAO MENDES",
        codigo_eol="000546",
        uuid="a627fc63-16fd-482c-a877-16ebc1a82e57",
        contato=contato,
        diretoria_regional=diretoria_regional,
        tipo_gestao=tipo_gestao,
        tipo_unidade=tipo_unidade,
    )
    return escola


@pytest.fixture
def escola_com_periodos_e_horarios_combos(escola):
    periodo_manha = mommy.make(
        "escola.PeriodoEscolar",
        nome="MANHA",
        uuid="42325516-aebd-4a3d-97c0-2a77c317c6be",
    )
    periodo_tarde = mommy.make(
        "escola.PeriodoEscolar",
        nome="TARDE",
        uuid="5d668346-ad83-4334-8fec-94c801198d99",
    )
    mommy.make(
        "escola.EscolaPeriodoEscolar",
        quantidade_alunos=325,
        escola=escola,
        periodo_escolar=periodo_manha,
    )
    mommy.make(
        "escola.EscolaPeriodoEscolar",
        quantidade_alunos=418,
        escola=escola,
        periodo_escolar=periodo_tarde,
    )
    return escola


@pytest.fixture
def template_mensagem_inversao_cardapio():
    return mommy.make(
        TemplateMensagem,
        tipo=TemplateMensagem.INVERSAO_CARDAPIO,
        assunto="TESTE INVERSAO CARDAPIO",
        template_html="@id @criado_em @status @link",
    )


@pytest.fixture
def inversao_dia_cardapio(
    cardapio_valido2, cardapio_valido3, template_mensagem_inversao_cardapio, escola
):
    return mommy.make(
        InversaoCardapio,
        criado_em=datetime.date(2019, 12, 12),
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )


@pytest.fixture
def inversao_dia_cardapio_outra_dre(
    cardapio_valido2,
    cardapio_valido3,
    template_mensagem_inversao_cardapio,
    escola_dre_guaianases,
):
    return mommy.make(
        InversaoCardapio,
        criado_em=datetime.date(2019, 12, 12),
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        escola=escola_dre_guaianases,
        rastro_escola=escola_dre_guaianases,
        rastro_dre=escola_dre_guaianases.diretoria_regional,
    )


@pytest.fixture
def inversao_dia_cardapio_dre_validar(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_codae_questionado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_QUESTIONADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_dre_validado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.DRE_VALIDADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio_codae_autorizado(inversao_dia_cardapio):
    inversao_dia_cardapio.status = PedidoAPartirDaEscolaWorkflow.CODAE_AUTORIZADO
    inversao_dia_cardapio.save()
    return inversao_dia_cardapio


@pytest.fixture
def inversao_dia_cardapio2(cardapio_valido, cardapio_valido2, escola):
    mommy.make(
        TemplateMensagem,
        assunto="TESTE INVERSAO CARDAPIO",
        tipo=TemplateMensagem.INVERSAO_CARDAPIO,
        template_html="@id @criado_em @status @link",
    )
    return mommy.make(
        InversaoCardapio,
        uuid="98dc7cb7-7a38-408d-907c-c0f073ca2d13",
        cardapio_de=cardapio_valido,
        cardapio_para=cardapio_valido2,
        escola=escola,
    )


@pytest.fixture
def inversao_cardapio_serializer(escola):
    cardapio_de = mommy.make("cardapio.Cardapio")
    cardapio_para = mommy.make("cardapio.Cardapio")
    inversao_cardapio = mommy.make(
        InversaoCardapio,
        cardapio_de=cardapio_de,
        cardapio_para=cardapio_para,
        escola=escola,
    )
    return InversaoCardapioSerializer(inversao_cardapio)


@pytest.fixture
def suspensao_alimentacao(motivo_suspensao_alimentacao):
    return mommy.make(SuspensaoAlimentacao, motivo=motivo_suspensao_alimentacao)


@pytest.fixture
def suspensao_periodo_escolar(suspensao_alimentacao):
    return mommy.make(
        SuspensaoAlimentacaoNoPeriodoEscolar,
        suspensao_alimentacao=suspensao_alimentacao,
    )


@pytest.fixture
def template_mensagem_suspensao_alimentacao():
    return mommy.make(TemplateMensagem, tipo=TemplateMensagem.SUSPENSAO_ALIMENTACAO)


@pytest.fixture
def grupo_suspensao_alimentacao(escola):
    grupo_suspensao = mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola,
        rastro_escola=escola,
    )
    mommy.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 29),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    mommy.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 30),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    mommy.make(
        SuspensaoAlimentacao,
        data=datetime.date(2022, 1, 31),
        grupo_suspensao=grupo_suspensao,
        cancelado=False,
    )
    return grupo_suspensao


@pytest.fixture
def suspensao_alimentacao_de_cei(escola):
    motivo = mommy.make(MotivoSuspensao, nome="Suspensão de aula")
    periodos_escolares = mommy.make("escola.PeriodoEscolar", _quantity=2)
    return mommy.make(
        SuspensaoAlimentacaoDaCEI,
        escola=escola,
        motivo=motivo,
        periodos_escolares=periodos_escolares,
        data=datetime.date(2020, 4, 20),
    )


@pytest.fixture
def grupo_suspensao_alimentacao_outra_dre(
    escola_dre_guaianases, template_mensagem_suspensao_alimentacao
):
    return mommy.make(
        GrupoSuspensaoAlimentacao,
        observacao="lorem ipsum",
        escola=escola_dre_guaianases,
        rastro_escola=escola_dre_guaianases,
    )


@pytest.fixture
def grupo_suspensao_alimentacao_informado(grupo_suspensao_alimentacao):
    grupo_suspensao_alimentacao.status = InformativoPartindoDaEscolaWorkflow.INFORMADO
    grupo_suspensao_alimentacao.save()
    return grupo_suspensao_alimentacao


@pytest.fixture
def grupo_suspensao_alimentacao_escola_cancelou(grupo_suspensao_alimentacao):
    for (
        suspensao_alimentacao
    ) in grupo_suspensao_alimentacao.suspensoes_alimentacao.all():
        suspensao_alimentacao.cancelado = True
        suspensao_alimentacao.save()

    grupo_suspensao_alimentacao.status = (
        InformativoPartindoDaEscolaWorkflow.ESCOLA_CANCELOU
    )
    grupo_suspensao_alimentacao.save()
    return grupo_suspensao_alimentacao


@pytest.fixture
def quantidade_por_periodo_suspensao_alimentacao():
    return mommy.make(QuantidadePorPeriodoSuspensaoAlimentacao, numero_alunos=100)


@pytest.fixture
def suspensao_alimentacao_serializer(suspensao_alimentacao):
    return SuspensaoAlimentacaoSerializer(suspensao_alimentacao)


@pytest.fixture
def motivo_alteracao_cardapio():
    return mommy.make(MotivoAlteracaoCardapio, nome="Aniversariantes do mês")


@pytest.fixture
def motivo_alteracao_cardapio_lanche_emergencial():
    return mommy.make(
        MotivoAlteracaoCardapio,
        nome="Lanche Emergencial",
        uuid="19d0bca9-3cfe-4542-869e-185d580fef06",
    )


@pytest.fixture
def motivo_alteracao_cardapio_inativo():
    return mommy.make(MotivoAlteracaoCardapio, nome="Motivo Inativo", ativo=False)


@pytest.fixture
def motivo_suspensao_alimentacao():
    return mommy.make(MotivoSuspensao, nome="Não vai ter aula")


@pytest.fixture
def motivo_alteracao_cardapio_serializer():
    motivo_alteracao_cardapio = mommy.make(MotivoAlteracaoCardapio)
    return MotivoAlteracaoCardapioSerializer(motivo_alteracao_cardapio)


@pytest.fixture
def template_mensagem_alteracao_cardapio():
    return mommy.make(TemplateMensagem, tipo=TemplateMensagem.ALTERACAO_CARDAPIO)


@pytest.fixture
def alteracao_cardapio(escola, template_mensagem_alteracao_cardapio):
    return mommy.make(
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
    alteracao = mommy.make(
        AlteracaoCardapio,
        escola=escola,
        observacao="teste",
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 10, 6),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=AlteracaoCardapio.workflow_class.DRE_A_VALIDAR,
    )
    mommy.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-04",
        alteracao_cardapio=alteracao,
    )
    mommy.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-05",
        alteracao_cardapio=alteracao,
    )
    mommy.make(
        "DataIntervaloAlteracaoCardapio",
        data="2019-10-06",
        alteracao_cardapio=alteracao,
    )
    return alteracao


@pytest.fixture
def alteracao_cardapio_cei(escola, template_mensagem_alteracao_cardapio):
    return mommy.make(
        AlteracaoCardapioCEI,
        escola=escola,
        observacao="teste",
        data=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )


@pytest.fixture
def alteracao_cardapio_outra_dre(
    escola_dre_guaianases, template_mensagem_alteracao_cardapio
):
    return mommy.make(
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


@pytest.fixture
def substituicoes_alimentacao_periodo(escola):
    alteracao_cardapio = mommy.make(
        AlteracaoCardapio, escola=escola, observacao="teste"
    )
    return mommy.make(
        SubstituicaoAlimentacaoNoPeriodoEscolar,
        uuid="59beb0ca-982a-49da-98b8-10a296f274ba",
        alteracao_cardapio=alteracao_cardapio,
    )


@pytest.fixture
def alteracao_cardapio_serializer(escola):
    alteracao_cardapio = mommy.make(AlteracaoCardapio, escola=escola)
    return AlteracaoCardapioSerializer(alteracao_cardapio)


@pytest.fixture
def substituicoes_alimentacao_no_periodo_escolar_serializer():
    substituicoes_alimentacao_no_periodo_escolar = mommy.make(
        SubstituicaoAlimentacaoNoPeriodoEscolar
    )
    return SubstituicoesAlimentacaoNoPeriodoEscolarSerializer(
        substituicoes_alimentacao_no_periodo_escolar
    )


@pytest.fixture(
    params=[
        (
            datetime.date(2019, 8, 10),
            datetime.date(2019, 10, 24),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
        (
            datetime.date(2019, 1, 1),
            datetime.date(2019, 3, 3),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
        (
            datetime.date(2019, 1, 1),
            datetime.date(2019, 3, 4),
            "Diferença entre as datas não pode ultrapassar de 60 dias",
        ),
    ]
)
def datas_de_inversoes_intervalo_maior_60_dias(request):
    return request.param


@pytest.fixture(
    params=[
        (datetime.date(2019, 8, 10), datetime.date(2019, 10, 9), True),
        (datetime.date(2019, 1, 1), datetime.date(2019, 3, 1), True),
        (datetime.date(2019, 1, 1), datetime.date(2019, 3, 2), True),
    ]
)
def datas_de_inversoes_intervalo_entre_60_dias(request):
    return request.param


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 5),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 2),
            datetime.date(2019, 10, 6),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 3),
            datetime.date(2019, 10, 7),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 10, 5),
            datetime.date(2019, 10, 1),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 6),
            datetime.date(2019, 10, 2),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 7),
            datetime.date(2019, 10, 3),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_vencida(request):
    return request.param


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        ((2019, 10, 4), (2019, 10, 30), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 5), (2019, 10, 12), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 6), (2019, 10, 13), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (
            (2019, 10, 7),
            (2019, 10, 14),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        ((2019, 10, 28), (2019, 10, 7), PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR),
        ((2019, 10, 29), (2019, 10, 8), PedidoAPartirDaEscolaWorkflow.RASCUNHO),
        (
            (2019, 10, 30),
            (2019, 10, 9),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            (2019, 10, 30),
            (2019, 10, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_desta_semana(request):
    return request.param


@pytest.fixture(
    params=[
        # dia cardapio de, dia cardapio para, status
        (
            datetime.date(2019, 10, 29),
            datetime.date(2019, 11, 1),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 15),
            datetime.date(2019, 10, 31),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 10),
            datetime.date(2019, 10, 29),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 28),
            datetime.date(2019, 11, 3),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 10, 10),
            datetime.date(2019, 10, 15),
            PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
        ),
        (
            datetime.date(2019, 10, 15),
            datetime.date(2019, 10, 10),
            PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        ),
        (
            datetime.date(2019, 10, 4),
            datetime.date(2019, 11, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
        (
            datetime.date(2019, 11, 4),
            datetime.date(2019, 10, 4),
            PedidoAPartirDaEscolaWorkflow.DRE_PEDIU_ESCOLA_REVISAR,
        ),
    ]
)
def datas_inversao_deste_mes(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (datetime.time(10, 29), datetime.time(11, 29), True),
        (datetime.time(7, 10), datetime.time(7, 30), True),
        (datetime.time(6, 0), datetime.time(6, 10), True),
        (datetime.time(23, 30), datetime.time(23, 59), True),
        (datetime.time(20, 0), datetime.time(20, 22), True),
        (datetime.time(11, 0), datetime.time(13, 0), True),
        (datetime.time(15, 3), datetime.time(15, 21), True),
    ]
)
def horarios_combos_tipo_alimentacao_validos(request):
    return request.param


@pytest.fixture(
    params=[
        # data inicio, data fim, esperado
        (
            datetime.time(10, 29),
            datetime.time(9, 29),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(7, 10),
            datetime.time(6, 30),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(6, 0),
            datetime.time(5, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(23, 30),
            datetime.time(22, 59),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(20, 0),
            datetime.time(19, 22),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(11, 0),
            datetime.time(11, 0),
            "Hora Inicio não pode ser maior do que hora final",
        ),
        (
            datetime.time(15, 3),
            datetime.time(12, 21),
            "Hora Inicio não pode ser maior do que hora final",
        ),
    ]
)
def horarios_combos_tipo_alimentacao_invalidos(request):
    return request.param


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


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de create, data para create, data de update, data para update
        (
            datetime.date(2019, 10, 25),
            datetime.date(2019, 11, 25),
            datetime.date(2019, 11, 24),
            datetime.date(2019, 11, 28),
        ),
        (
            datetime.date(2019, 10, 26),
            datetime.date(2019, 12, 24),
            datetime.date(2019, 10, 20),
            datetime.date(2019, 11, 24),
        ),
        (
            datetime.date(2019, 12, 25),
            datetime.date(2019, 12, 30),
            datetime.date(2019, 12, 15),
            datetime.date(2019, 12, 31),
        ),
    ]
)
def inversao_card_params(request):
    return request.param


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de, data para
        (
            datetime.date(2019, 12, 25),
            datetime.date(2020, 1, 10),
        ),  # deve ser no ano corrente
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 20),
        ),  # nao pode ser no passado
        (
            datetime.date(2019, 10, 17),
            datetime.date(2019, 12, 20),
        ),  # nao pode ter mais de 60 dias de intervalo
        (
            datetime.date(2019, 10, 31),
            datetime.date(2019, 10, 15),
        ),  # data de nao pode ser maior que data para
    ]
)
def inversao_card_params_error(request):
    return request.param


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 5), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 10), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 20), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 25), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 10, 31), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 3), datetime.date(2019, 12, 31)),
        (datetime.date(2019, 11, 4), datetime.date(2019, 12, 31)),
    ]
)
def suspensao_alimentacao_parametros_mes(request):
    return request.param


@pytest.fixture(
    params=[
        # data_inicial, data_final
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 4)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 5)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 6)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 7)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 8)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 9)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 10)),
        (datetime.date(2019, 10, 4), datetime.date(2019, 10, 11)),
    ]
)
def suspensao_alimentacao_parametros_semana(request):
    return request.param


@pytest.fixture()
def daqui_dez_dias_ou_ultimo_dia_do_ano():
    hoje = datetime.date.today()
    dia_alteracao = hoje + datetime.timedelta(days=10)
    if dia_alteracao.year != hoje.year:
        dia_alteracao = datetime.date(hoje.year, 12, 31)
    return dia_alteracao


@pytest.fixture()
def alterar_tipos_alimentacao_data():
    alimentacao1 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao1")
    alimentacao2 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao2")
    alimentacao3 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao3")
    periodo_escolar = mommy.make("escola.PeriodoEscolar", nome="MANHA")
    tipo_unidade_escolar = mommy.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    vinculo = mommy.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_escolar,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[alimentacao1],
    )
    return {"vinculo": vinculo, "tipos_alimentacao": [alimentacao2, alimentacao3]}


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
    alimentacao1 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao1")
    alimentacao2 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao2")
    alimentacao3 = mommy.make("cardapio.TipoAlimentacao", nome="tp_alimentacao3")
    periodo_escolar = mommy.make("escola.PeriodoEscolar", nome="MANHA")
    tipo_unidade_escolar = mommy.make("escola.TipoUnidadeEscolar", iniciais="EMEF")
    escola = mommy.make(
        "escola.Escola", nome="PERICLIS", tipo_unidade=tipo_unidade_escolar
    )
    mommy.make(
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        periodo_escolar=periodo_escolar,
        tipo_unidade_escolar=tipo_unidade_escolar,
        tipos_alimentacao=[alimentacao1, alimentacao2, alimentacao3],
    )
    motivo = mommy.make(
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


@pytest.fixture(
    params=[
        # data_create , data_update
        (datetime.date(2019, 10, 17), datetime.date(2019, 10, 18)),
    ]
)
def suspensao_alimentacao_cei_params(request):
    motivo = mommy.make(
        "cardapio.MotivoSuspensao",
        nome="outro",
        uuid="478b09e1-4c14-4e50-a446-fbc0af727a08",
    )

    data_create, data_update = request.param
    return motivo, data_create, data_update


@pytest.fixture(
    params=[
        # data do teste 14 out 2019
        # data de, data para
        (
            datetime.date(2019, 12, 25),
            datetime.date(2020, 1, 10),
        ),  # deve ser no ano corrente
        (
            datetime.date(2019, 10, 1),
            datetime.date(2019, 10, 20),
        ),  # nao pode ser no passado
        (
            datetime.date(2019, 10, 17),
            datetime.date(2019, 12, 20),
        ),  # nao pode ter mais de 60 dias de intervalo
        (
            datetime.date(2019, 10, 31),
            datetime.date(2019, 10, 15),
        ),  # data de nao pode ser maior que data para
    ]
)
def grupo_suspensao_alimentacao_params(request):
    return request.param


@pytest.fixture
def tipo_unidade_escolar():
    cardapio1 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 11))
    cardapio2 = mommy.make("cardapio.Cardapio", data=datetime.date(2019, 10, 15))
    return mommy.make(
        "TipoUnidadeEscolar",
        iniciais=fake.name()[:10],
        cardapios=[cardapio1, cardapio2],
    )


@pytest.fixture
def periodo_escolar():
    return mommy.make("PeriodoEscolar")


@pytest.fixture
def faixas_etarias_ativas():
    faixas = [
        (0, 1),
        (1, 4),
        (4, 6),
        (6, 8),
        (8, 12),
        (12, 24),
        (24, 48),
        (48, 72),
    ]
    return [
        mommy.make("FaixaEtaria", inicio=inicio, fim=fim, ativo=True)
        for (inicio, fim) in faixas
    ]


@pytest.fixture(
    params=[
        # periodo escolar, tipo unidade escolar
        ("MANHA", "EMEF"),
        ("MANHA", "CIEJA"),
    ]
)
def vinculo_tipo_alimentacao(request):
    nome_periodo, nome_ue = request.param
    tipos_alimentacao = mommy.make("TipoAlimentacao", _quantity=5)
    tipo_unidade_escolar = mommy.make("TipoUnidadeEscolar", iniciais=nome_ue)
    periodo_escolar = mommy.make("PeriodoEscolar", nome=nome_periodo)
    return mommy.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipos_alimentacao=tipos_alimentacao,
        uuid="3bdf8144-9b17-495a-8387-5ce0d2a6120a",
        tipo_unidade_escolar=tipo_unidade_escolar,
        periodo_escolar=periodo_escolar,
    )


@pytest.fixture(
    params=[
        # hora inicio, hora fim
        ("07:00:00", "07:30:00"),
    ]
)
def horario_tipo_alimentacao(
    request, vinculo_tipo_alimentacao, escola_com_periodos_e_horarios_combos
):
    hora_inicio, hora_fim = request.param
    escola = escola_com_periodos_e_horarios_combos
    tipo_alimentacao = mommy.make(
        "TipoAlimentacao",
        nome="Lanche",
        posicao=2,
        uuid="c42a24bb-14f8-4871-9ee8-05bc42cf3061",
    )
    periodo_escolar = mommy.make(
        "PeriodoEscolar", nome="TARDE", uuid="22596464-271e-448d-bcb3-adaba43fffc8"
    )

    return mommy.make(
        "HorarioDoComboDoTipoDeAlimentacaoPorUnidadeEscolar",
        hora_inicial=hora_inicio,
        hora_final=hora_fim,
        escola=escola,
        tipo_alimentacao=tipo_alimentacao,
        periodo_escolar=periodo_escolar,
    )


@pytest.fixture
def client_autenticado_vinculo_escola_cardapio(
    client,
    django_user_model,
    escola,
    template_mensagem_alteracao_cardapio,
    cardapio_valido2,
    cardapio_valido3,
):
    email = "test@test.com"
    rf = "8888888"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional="8888888"
    )
    assert escola.tipo_gestao.nome == "TERC TOTAL"
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        InversaoCardapio,
        cardapio_de=cardapio_valido2,
        cardapio_para=cardapio_valido3,
        criado_por=user,
        criado_em=datetime.date(2019, 12, 12),
        escola=escola,
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
        status=PedidoAPartirDaEscolaWorkflow.RASCUNHO,
    )
    mommy.make(
        AlteracaoCardapio,
        criado_por=user,
        escola=escola,
        data_inicial=datetime.date(2019, 10, 4),
        data_final=datetime.date(2019, 12, 31),
        rastro_escola=escola,
        rastro_dre=escola.diretoria_regional,
    )
    mommy.make(
        GrupoSuspensaoAlimentacao, criado_por=user, escola=escola, rastro_escola=escola
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_escola_cei_cardapio(
    client, django_user_model, escola_cei, template_mensagem_alteracao_cardapio
):
    email = "test@test.com"
    rf = "8888888"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=rf, password=password, email=email, registro_funcional="8888888"
    )
    assert escola_cei.tipo_gestao.nome == "TERC TOTAL"
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        GrupoSuspensaoAlimentacao,
        criado_por=user,
        escola=escola_cei,
        rastro_escola=escola_cei,
    )
    client.login(username=rf, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_dre_cardapio(
    client, django_user_model, escola, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_cogestor = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_cardapio(client, django_user_model, codae):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_admin_gestao_alimentacao = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_admin_gestao_alimentacao,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_codae_dieta_cardapio(
    client, django_user_model, escola, codae
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_dieta = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_DIETA_ESPECIAL,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=codae,
        perfil=perfil_dieta,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_terceirizada_cardapio(
    client, django_user_model, escola, codae
):
    email = "test@test.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888888"
    )
    perfil_nutri_admin = mommy.make(
        "Perfil",
        nome=constants.ADMINISTRADOR_EMPRESA,
        ativo=True,
        uuid="41c20c8b-7e57-41ed-9433-ccb92e8afaf1",
    )
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola.lote.terceirizada,
        perfil=perfil_nutri_admin,
        data_inicial=hoje,
        ativo=True,
    )
    mommy.make(
        TemplateMensagem,
        assunto="TESTE",
        tipo=TemplateMensagem.DIETA_ESPECIAL,
        template_html="@id @criado_em @status @link",
    )
    client.login(username=email, password=password)
    return client


@pytest.fixture
def alteracao_cemei(escola_cemei, tipo_alimentacao, faixas_etarias_ativas):
    periodo_escolar = mommy.make("escola.PeriodoEscolar", nome="MANHA")
    alteracao_cemei = mommy.make(
        AlteracaoCardapioCEMEI,
        escola=escola_cemei,
        alunos_cei_e_ou_emei=AlteracaoCardapioCEMEI.CEI,
        rastro_escola=escola_cemei,
        rastro_lote=escola_cemei.lote,
        rastro_dre=escola_cemei.diretoria_regional,
        alterar_dia="2023-08-01",
    )
    subs1 = mommy.make(
        SubstituicaoAlimentacaoNoPeriodoEscolarCEMEICEI,
        alteracao_cardapio=alteracao_cemei,
        periodo_escolar=periodo_escolar,
    )
    subs1.tipos_alimentacao_de.set([tipo_alimentacao])
    subs1.tipos_alimentacao_para.set([tipo_alimentacao])
    subs1.save()
    mommy.make(
        FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
        substituicao_alimentacao=subs1,
        matriculados_quando_criado=10,
        faixa_etaria=faixas_etarias_ativas[0],
        quantidade=10,
    )
    return alteracao_cemei


@pytest.fixture
def alteracao_cemei_dre_a_validar(alteracao_cemei):
    alteracao_cemei.status = alteracao_cemei.workflow_class.DRE_A_VALIDAR
    alteracao_cemei.save()
    return alteracao_cemei


@pytest.fixture
def alteracao_cemei_dre_validado(alteracao_cemei):
    alteracao_cemei.status = alteracao_cemei.workflow_class.DRE_VALIDADO
    alteracao_cemei.save()
    return alteracao_cemei


@pytest.fixture
def client_autenticado_vinculo_escola_cemei(
    client, django_user_model, escola_cemei, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_diretor = mommy.make("Perfil", nome="DIRETOR_UE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei,
        perfil=perfil_diretor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client


@pytest.fixture
def client_autenticado_vinculo_dre_escola_cemei(
    client, django_user_model, escola_cemei, template_mensagem_alteracao_cardapio
):
    email = "test@test1.com"
    password = constants.DJANGO_ADMIN_PASSWORD
    user = django_user_model.objects.create_user(
        username=email, password=password, email=email, registro_funcional="8888889"
    )
    perfil_cogestor = mommy.make("Perfil", nome="COGESTOR_DRE", ativo=True)
    hoje = datetime.date.today()
    mommy.make(
        "Vinculo",
        usuario=user,
        instituicao=escola_cemei.diretoria_regional,
        perfil=perfil_cogestor,
        data_inicial=hoje,
        ativo=True,
    )

    client.login(username=email, password=password)
    return client


@pytest.fixture
def vinculos_alimentacao():
    mommy.make(
        "TipoUnidadeEscolar", iniciais="CEI DIRET", tem_somente_integral_e_parcial=False
    )
    mommy.make(
        "TipoUnidadeEscolar", iniciais="EMEF", tem_somente_integral_e_parcial=False
    )
    mommy.make(
        "TipoUnidadeEscolar",
        iniciais="EMEF P FOM",
        tem_somente_integral_e_parcial=False,
    )

    tipo_unidade = mommy.make(
        "TipoUnidadeEscolar", iniciais="CEMEI", tem_somente_integral_e_parcial=True
    )
    escola = mommy.make("Escola", tipo_unidade=tipo_unidade)
    periodo_escolar = mommy.make(
        "PeriodoEscolar",
        nome="INTEGRAL",
    )
    escola_periodo_escolar = mommy.make(
        "EscolaPeriodoEscolar",
        periodo_escolar=periodo_escolar,
        escola=escola,
        quantidade_alunos=20,
    )

    return tipo_unidade, escola, periodo_escolar, escola_periodo_escolar


@pytest.fixture
def ativa_vinculo(vinculos_alimentacao):
    tipo_unidade, escola, periodo_escolar, escola_periodo_escolar = vinculos_alimentacao
    mommy.make(
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
        tipo_unidade_escolar=tipo_unidade,
        periodo_escolar=periodo_escolar,
        ativo=False,
    )
    return tipo_unidade, escola_periodo_escolar
