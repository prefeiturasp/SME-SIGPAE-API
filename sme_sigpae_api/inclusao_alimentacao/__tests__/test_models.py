import datetime
from uuid import UUID

import pytest
from model_bakery import baker
from xworkflows.base import InvalidTransitionError

from ...dados_comuns.fluxo_status import PedidoAPartirDaEscolaWorkflow
from ...escola.models import Escola, PeriodoEscolar
from ..models import InclusaoAlimentacaoContinua, MotivoInclusaoContinua

pytestmark = pytest.mark.django_db


def test_motivo_inclusao_continua(motivo_inclusao_continua):
    assert isinstance(motivo_inclusao_continua.nome, str)
    assert isinstance(motivo_inclusao_continua.uuid, UUID)
    assert motivo_inclusao_continua.__str__() == "teste nome"


def test_motivo_inclusao_normal(motivo_inclusao_normal):
    assert isinstance(motivo_inclusao_normal.nome, str)
    assert isinstance(motivo_inclusao_normal.uuid, UUID)


def test_quantidade_por_periodo(quantidade_por_periodo):
    assert isinstance(quantidade_por_periodo.numero_alunos, int)
    assert isinstance(quantidade_por_periodo.periodo_escolar, PeriodoEscolar)
    assert quantidade_por_periodo.tipos_alimentacao.all().count() == 5
    assert quantidade_por_periodo.__str__() == (
        f"{quantidade_por_periodo.numero_alunos} alunos para "
        + f"{quantidade_por_periodo.periodo_escolar} com "
        + f"{quantidade_por_periodo.tipos_alimentacao.all().count()} "
        "tipo(s) de alimentação"
    )


def test_inclusao_alimentacao_continua(inclusao_alimentacao_continua_params):
    inclusao_alimentacao_continua, esperado = inclusao_alimentacao_continua_params
    assert isinstance(inclusao_alimentacao_continua.escola, Escola)
    assert isinstance(inclusao_alimentacao_continua.motivo, MotivoInclusaoContinua)
    assunto, template_html = inclusao_alimentacao_continua.template_mensagem
    assert assunto == "TESTE"
    assert "98DC7" in template_html
    assert "RASCUNHO" in template_html
    assert inclusao_alimentacao_continua.data == esperado


def test_inclusao_alimentacao_continua_solicitacoes_similares(
    inclusao_alimentacao_continua,
):
    assert inclusao_alimentacao_continua.solicitacoes_similares == []


def test_inclusao_alimentacao_continua_fluxo(inclusao_alimentacao_continua_params):
    inclusao_alimentacao_continua, esperado = inclusao_alimentacao_continua_params
    fake_user = baker.make("perfil.Usuario")
    inclusao_alimentacao_continua.inicia_fluxo(user=fake_user)
    assert inclusao_alimentacao_continua.ta_na_dre
    inclusao_alimentacao_continua.dre_valida(user=fake_user)
    assert inclusao_alimentacao_continua.ta_na_codae
    inclusao_alimentacao_continua.codae_autoriza(user=fake_user)
    assert inclusao_alimentacao_continua.ta_na_terceirizada


def test_inclusao_alimentacao_continua_fluxo_erro(inclusao_alimentacao_continua_params):
    inclusao_alimentacao_continua, esperado = inclusao_alimentacao_continua_params
    assert (
        InclusaoAlimentacaoContinua.get_solicitacoes_rascunho(
            inclusao_alimentacao_continua.criado_por
        ).count()
        == 1
    )
    # TODO: pedir incremento do fluxo para testá-lo por completo
    with pytest.raises(
        InvalidTransitionError,
        match="Transition 'dre_pede_revisao' isn't available from state 'RASCUNHO'.",
    ):
        inclusao_alimentacao_continua.dre_pede_revisao()


def test_motivo_inclusao_normal_str(motivo_inclusao_normal_nome):
    assert motivo_inclusao_normal_nome.__str__() == "Passeio 5h"


def test_grupo_inclusao_alimentacao_normal_str(grupo_inclusao_alimentacao_nome):
    assert grupo_inclusao_alimentacao_nome.__str__() == (
        f"{grupo_inclusao_alimentacao_nome.escola} pedindo "
        f"{grupo_inclusao_alimentacao_nome.inclusoes.count()} "
        "inclusoes"
    )


def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_rascunho(
    make_grupo_inclusao_alimentacao_normal,
):
    make_grupo_inclusao_alimentacao_normal(
        kwargs_inclusao1={"data": datetime.datetime(2023, 12, 8)},
        kwargs_inclusao2={"data": datetime.datetime(2023, 12, 11)},
    )

    # o proprio grupo eh um rascunho
    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.RASCUNHO},
        kwargs_inclusao1={"data": datetime.datetime(2023, 12, 8)},
        kwargs_inclusao2={"data": datetime.datetime(2023, 12, 11)},
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_rascunho2(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal
):
    # o grupo possui uma unica similar e que eh rascunho
    make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.RASCUNHO},
        kwargs_inclusao1={"data": datetime.datetime(2023, 12, 8)},
        kwargs_inclusao2={"data": datetime.datetime(2023, 12, 11)},
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_motivo_permitido(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, motivo
):
    make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={"data": datetime.datetime(2023, 12, 8)},
        kwargs_inclusao2={"data": datetime.datetime(2023, 12, 11)},
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_motivo_permitido2(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, motivo
):
    grupo_similar = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 1
    assert grupo_inclusao_alimentacao_normal.solicitacoes_similares[0] == grupo_similar


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_motivo_nao_permitido(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, motivo
):
    make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={"data": datetime.datetime(2023, 12, 8)},
        kwargs_inclusao2={"data": datetime.datetime(2023, 12, 11)},
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_motivo_nao_permitido2(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, motivo
):
    make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_escola_diferente(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, make_escola
):
    escolas = make_escola(kwargs_escola={"_quantity": 2})

    make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[0],
        },
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[1],
        },
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 0


def test_grupo_inclusao_alimentacao_normal_solicitacoes_similares_escola_igual(
    make_grupo_inclusao_alimentacao_normal, make_motivo_inclusao_normal, make_escola
):
    escola = make_escola()

    similar = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    grupo_inclusao_alimentacao_normal = make_grupo_inclusao_alimentacao_normal(
        kwargs_grupo={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_inclusao1={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
        kwargs_inclusao2={
            "data": datetime.datetime(2023, 12, 11),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(grupo_inclusao_alimentacao_normal.solicitacoes_similares) == 1
    assert grupo_inclusao_alimentacao_normal.solicitacoes_similares[0] == similar


def test_inclusao_alimentacao_cei_solicitacoes_similares_rascunho(
    make_inclusao_alimentacao_cei,
):
    inclusao = make_inclusao_alimentacao_cei(
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    make_inclusao_alimentacao_cei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        },
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cei_solicitacoes_similares_rascunho2(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal
):
    make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.RASCUNHO},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_inclusao_alimentacao_cei_solicitacoes_similares_motivo_permitido(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_inclusao_alimentacao_cei_solicitacoes_similares_motivo_permitido2(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, motivo
):
    similar = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 1
    assert inclusao.solicitacoes_similares[0] == similar


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_inclusao_alimentacao_cei_solicitacoes_similares_motivo_nao_permitido(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_inclusao_alimentacao_cei_solicitacoes_similares_motivo_nao_permitido2(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cei_solicitacoes_similares_escola_diferente(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, make_escola_cei
):
    escolas = make_escola_cei(kwargs_escola={"_quantity": 2})

    make_inclusao_alimentacao_cei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[0],
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[1],
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cei_solicitacoes_similares_escola_igual(
    make_inclusao_alimentacao_cei, make_motivo_inclusao_normal, make_escola_cei
):
    escola = make_escola_cei()

    similar = make_inclusao_alimentacao_cei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    inclusao = make_inclusao_alimentacao_cei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 1
    assert inclusao.solicitacoes_similares[0] == similar


def test_inclusao_alimentacao_cemei_solicitacoes_similares_rascunho(
    make_inclusao_alimentacao_cemei,
):
    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.RASCUNHO,
        },
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cemei_solicitacoes_similares_rascunho2(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal
):
    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.RASCUNHO},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_inclusao_alimentacao_cemei_solicitacoes_similares_motivo_permitido(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo", [("Dia da família"), ("Reposição de aula"), ("Outro")]
)
def test_inclusao_alimentacao_cemei_solicitacoes_similares_motivo_permitido2(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, motivo
):
    similar = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 1
    assert inclusao.solicitacoes_similares[0] == similar


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_inclusao_alimentacao_cemei_solicitacoes_similares_motivo_nao_permitido(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={"data": datetime.datetime(2023, 12, 8)},
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


@pytest.mark.parametrize(
    "motivo",
    [
        ("Evento Específico"),
        ("Programas/Projetos Específicos"),
        ("ETEC"),
        ("Programas/Projetos Contínuos"),
        ("x90x89x"),
    ],
)
def test_inclusao_alimentacao_cemei_solicitacoes_similares_motivo_nao_permitido2(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, motivo
):
    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={"status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR},
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal(motivo),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cemei_solicitacoes_similares_escola_diferente(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, make_escola
):
    escolas = make_escola(kwargs_escola={"_quantity": 2})

    make_inclusao_alimentacao_cemei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[0],
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escolas[1],
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 0


def test_inclusao_alimentacao_cemei_solicitacoes_similares_escola_igual(
    make_inclusao_alimentacao_cemei, make_motivo_inclusao_normal, make_escola
):
    escola = make_escola()

    similar = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    inclusao = make_inclusao_alimentacao_cemei(
        kwargs_inclusao={
            "status": PedidoAPartirDaEscolaWorkflow.DRE_A_VALIDAR,
            "escola": escola,
        },
        kwargs_motivo={
            "data": datetime.datetime(2023, 12, 8),
            "motivo": make_motivo_inclusao_normal("Dia da família"),
        },
    )

    assert len(inclusao.solicitacoes_similares) == 1
    assert inclusao.solicitacoes_similares[0] == similar


def test_inclusao_alimentacao_normal(inclusao_alimentacao_normal):
    assert inclusao_alimentacao_normal.__str__() == (
        f"Dia {inclusao_alimentacao_normal.data} "
        + f"{inclusao_alimentacao_normal.motivo}"
    )


def test_inclusao_alimentacao_normal_outro_motivo(
    inclusao_alimentacao_normal_outro_motivo,
):
    assert inclusao_alimentacao_normal_outro_motivo.__str__() == (
        f"Dia {inclusao_alimentacao_normal_outro_motivo.data} - Outro motivo: "
        + f"{inclusao_alimentacao_normal_outro_motivo.outro_motivo}"
    )


def test_inclusao_alimentacao_cei_solicitacoes_similares(
    inclusao_alimentacao_cei,
):
    assert inclusao_alimentacao_cei.solicitacoes_similares == []


def test_inclusao_alimentacao_cemei_solicitacoes_similares(
    inclusao_alimentacao_cemei,
):
    assert inclusao_alimentacao_cemei.solicitacoes_similares == []
