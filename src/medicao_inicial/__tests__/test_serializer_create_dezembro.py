import datetime

import pytest
from freezegun import freeze_time

from src.core.models import FaixaEtaria
from src.medicao_inicial.api.serializers_create import (
    SolicitacaoMedicaoInicialCreateSerializer,
)
from src.medicao_inicial.models import (
    CategoriaMedicao,
    Medicao,
    ValorMedicao,
)

pytestmark = pytest.mark.django_db

CAMPOS_NAO_GERADOS = [
    "matriculados",
    "numero_de_alunos",
    "dietas_autorizadas",
]


def _cria_dias_letivos_dezembro(dia_calendario_factory, escola):
    for dia in range(1, 23):
        dia_calendario_factory.create(
            escola=escola,
            data=datetime.date(2026, 12, dia),
            dia_letivo=dia != 20,
        )


def _cria_valor(
    medicao,
    categoria,
    dia,
    nome_campo,
    valor="100",
    faixa_etaria=None,
):
    ValorMedicao.objects.create(
        medicao=medicao,
        categoria_medicao=categoria,
        dia=f"{dia:02d}",
        nome_campo=nome_campo,
        valor=valor,
        faixa_etaria=faixa_etaria,
    )


@freeze_time("2026-12-15")
def test_gera_valores_zerados_dos_lancamentos_restantes_de_dezembro(
    solicitacao_medicao_inicial_factory,
    dia_calendario_factory,
    periodo_escolar_factory,
    escola,
):
    _cria_dias_letivos_dezembro(dia_calendario_factory, escola)
    solicitacao = solicitacao_medicao_inicial_factory.create(
        escola=escola,
        mes="12",
        ano="2026",
    )
    periodo = periodo_escolar_factory.create(nome="MANHA")
    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)

    for dia in list(range(1, 15)) + [20]:
        for campo in ["frequencia", "refeicao"] + CAMPOS_NAO_GERADOS:
            _cria_valor(medicao, categoria, dia, campo)

    for dia in list(range(15, 20)) + list(range(21, 23)):
        for campo in CAMPOS_NAO_GERADOS:
            _cria_valor(medicao, categoria, dia, campo)

    _cria_valor(medicao, categoria, 15, "refeicao")

    serializer = SolicitacaoMedicaoInicialCreateSerializer()
    serializer.gera_valores_zerados_dias_restantes_dezembro(solicitacao)

    for dia in range(1, 15):
        valores = medicao.valores_medicao.filter(dia=f"{dia:02d}")
        assert set(valores.values_list("valor", flat=True)) == {"100"}

    for dia in list(range(15, 20)) + list(range(21, 23)):
        for campo in CAMPOS_NAO_GERADOS:
            assert (
                medicao.valores_medicao.get(dia=f"{dia:02d}", nome_campo=campo).valor
                == "100"
            )
        for campo in ["frequencia", "refeicao"]:
            assert (
                medicao.valores_medicao.get(dia=f"{dia:02d}", nome_campo=campo).valor
                == "0"
            )

    dia_nao_letivo = medicao.valores_medicao.filter(dia="20")
    assert set(dia_nao_letivo.values_list("valor", flat=True)) == {"100"}


@freeze_time("2026-12-15")
def test_gera_valores_zerados_preserva_faixa_etaria_cei(
    solicitacao_medicao_inicial_factory,
    dia_calendario_factory,
    periodo_escolar_factory,
    escola,
):
    _cria_dias_letivos_dezembro(dia_calendario_factory, escola)
    solicitacao = solicitacao_medicao_inicial_factory.create(
        escola=escola,
        mes="12",
        ano="2026",
    )
    periodo = periodo_escolar_factory.create(nome="INTEGRAL")
    medicao = Medicao.objects.create(
        solicitacao_medicao_inicial=solicitacao,
        periodo_escolar=periodo,
    )
    categoria = CategoriaMedicao.objects.create(nome=CategoriaMedicao.ALIMENTACAO)
    faixa_etaria = FaixaEtaria.objects.create(inicio=0, fim=3)

    for dia in list(range(1, 15)) + [20]:
        _cria_valor(
            medicao,
            categoria,
            dia,
            "frequencia",
            faixa_etaria=faixa_etaria,
        )

    serializador = SolicitacaoMedicaoInicialCreateSerializer()
    serializador.gera_valores_zerados_dias_restantes_dezembro(solicitacao)

    for dia in list(range(15, 20)) + list(range(21, 23)):
        valor = medicao.valores_medicao.get(
            dia=f"{dia:02d}",
            nome_campo="frequencia",
            faixa_etaria=faixa_etaria,
        )
        assert valor.valor == "0"

    valor_dia_nao_letivo = medicao.valores_medicao.get(
        dia="20",
        nome_campo="frequencia",
        faixa_etaria=faixa_etaria,
    )
    assert valor_dia_nao_letivo.valor == "100"
