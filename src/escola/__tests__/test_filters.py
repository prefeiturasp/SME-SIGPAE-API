from unittest.mock import Mock

import pytest
from django.http import QueryDict
from model_bakery import baker

from src.dados_comuns.constants import TIPOS_UNIDADE_ESCOLAR, PayloadVariaveis
from src.escola.api.filters import (
    AlunoFilter,
    DiretoriaRegionalFilter,
    EscolaParaFiltrosFilter,
    LogAlunosMatriculadosFaixaEtariaDiaFilter,
    SubprefeituraFilter,
)
from src.escola.models import (
    Aluno,
    Escola,
    LogAlunosMatriculadosFaixaEtariaDia,
    Subprefeitura,
    TipoUnidadeEscolar,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def escolas_para_filtros(tipo_gestao):
    dre = baker.make("DiretoriaRegional", nome="DRE FILTROS")
    tipo_emef = baker.make(
        TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.EMEF.value
    )
    tipo_cei = baker.make(TipoUnidadeEscolar, iniciais=TIPOS_UNIDADE_ESCOLAR.CEI.value)
    lote_a = baker.make("Lote", nome="LOTE A")
    lote_b = baker.make("Lote", nome="LOTE B")

    escola_emef_lote_a = baker.make(
        Escola,
        codigo_eol="000001",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )
    escola_emef_lote_b = baker.make(
        Escola,
        codigo_eol="000002",
        diretoria_regional=dre,
        tipo_unidade=tipo_emef,
        lote=lote_b,
        tipo_gestao=tipo_gestao,
    )
    escola_cei_lote_a = baker.make(
        Escola,
        codigo_eol="000003",
        diretoria_regional=dre,
        tipo_unidade=tipo_cei,
        lote=lote_a,
        tipo_gestao=tipo_gestao,
    )

    return {
        "dre": dre,
        "tipo_emef": tipo_emef,
        "tipo_cei": tipo_cei,
        "lote_a": lote_a,
        "lote_b": lote_b,
        "escola_emef_lote_a": escola_emef_lote_a,
        "escola_emef_lote_b": escola_emef_lote_b,
        "escola_cei_lote_a": escola_cei_lote_a,
    }


def test_diretoria_regional_filter(diretoria_regional):
    filtro_dre = DiretoriaRegionalFilter(
        data={"dre": diretoria_regional.uuid},
        queryset=Escola.objects.all().prefetch_related("diretoria_regional"),
    )
    assert filtro_dre.qs.count() == 3
    for escola in filtro_dre.qs:
        assert escola.diretoria_regional.nome == diretoria_regional.nome
        assert str(escola.diretoria_regional.uuid) == diretoria_regional.uuid


def test_aluno_filter_codigo_eol(aluno):
    filtro_codigo_eol = AlunoFilter(
        data={"codigo_eol": aluno.codigo_eol}, queryset=Aluno.objects.all()
    )
    assert filtro_codigo_eol.qs.count() == 1
    assert filtro_codigo_eol.qs[0].nome == aluno.nome
    assert filtro_codigo_eol.qs[0].codigo_eol == aluno.codigo_eol

    filtro = AlunoFilter(data={"codigo_eol": aluno.nome}, queryset=Aluno.objects.all())
    assert filtro.qs.count() == 0


def test_aluno_filter_dre(aluno):
    diretoria_regional = aluno.escola.diretoria_regional

    filtro_dre = AlunoFilter(
        data={"dre": diretoria_regional.uuid}, queryset=Aluno.objects.all()
    )
    assert filtro_dre.qs.count() == 1
    assert filtro_dre.qs[0].nome == aluno.nome
    assert (
        str(filtro_dre.qs[0].escola.diretoria_regional.uuid) == diretoria_regional.uuid
    )

    filtro = AlunoFilter(
        data={"dre": diretoria_regional.nome}, queryset=Aluno.objects.all()
    )
    assert filtro.qs.count() == 0


def test_aluno_filter_dieta_especial(dieta_codae_autorizou, dieta_cancelada):
    assert dieta_codae_autorizou.aluno == dieta_cancelada.aluno
    aluno = dieta_cancelada.aluno

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": True}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 0

    filtro_nao_tem_dieta_especial = AlunoFilter(
        data={"nao_tem_dieta_especial": False}, queryset=Aluno.objects.all()
    )
    assert filtro_nao_tem_dieta_especial.qs.count() == 2
    aluno_dieta = filtro_nao_tem_dieta_especial.qs.distinct()[0]
    assert aluno_dieta.dietas_especiais.count() == 2
    for dieta in aluno_dieta.dietas_especiais.all():
        assert dieta.aluno.nome == aluno.nome


def test_aluno_filter_periodo_escola(aluno):
    periodo_escolar = aluno.periodo_escolar

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": "TARDE"}, queryset=Aluno.objects.all()
    )
    assert filtro_periodo_escola.qs.count() == 0

    filtro_periodo_escola = AlunoFilter(
        data={"periodo_escolar_nome": periodo_escolar.nome},
        queryset=Aluno.objects.all(),
    )
    assert filtro_periodo_escola.qs.count() == 1
    assert filtro_periodo_escola.qs[0].nome == aluno.nome


def test_aluno_filter_escola_egressos_false(aluno):
    escola = aluno.escola

    mock_request = Mock()
    mock_request.query_params = {"inclui_alunos_egressos": "false"}
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 1
    assert filtro_escola.qs[0].nome == aluno.nome
    assert filtro_escola.qs[0].escola == escola


def test_aluno_filter_escola_egressos_true(aluno):
    escola = aluno.escola
    mock_request = Mock()
    mock_request.query_params = {
        "inclui_alunos_egressos": "true",
        "mes": "5",
        "ano": "2023",
    }
    filtro_escola = AlunoFilter(
        data={"escola": escola.uuid}, queryset=Aluno.objects.all(), request=mock_request
    )
    assert filtro_escola.qs.count() == 0


def test_log_aluno_filter_escola(log_alunos_matriculados_faixa_etaria_dia):
    escola = log_alunos_matriculados_faixa_etaria_dia.escola
    filtro_escola = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"escola_uuid": escola.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_escola.qs.count() == 1
    assert filtro_escola.qs[0].escola == escola

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"escola_uuid": escola.diretoria_regional.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_periodo_escola(log_alunos_matriculados_faixa_etaria_dia):
    periodo_escolar = log_alunos_matriculados_faixa_etaria_dia.periodo_escolar

    filtro_periodo_escola = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"nome_periodo_escolar": periodo_escolar.nome},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_periodo_escola.qs.count() == 1
    assert filtro_periodo_escola.qs[0].periodo_escolar == periodo_escolar

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"nome_periodo_escolar": periodo_escolar.uuid},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_mes(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_mes = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"mes": data.month},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_mes.qs.count() == 1
    assert filtro_mes.qs[0].data.month == data.month

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"mes": 0}, queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all()
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_ano(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_ano = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"ano": data.year},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_ano.qs.count() == 1
    assert filtro_ano.qs[0].data.year == data.year

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"ano": "cinco"},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_log_aluno_filter_dia(log_alunos_matriculados_faixa_etaria_dia):
    data = log_alunos_matriculados_faixa_etaria_dia.data
    filtro_dias = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"dias": [data.day]},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro_dias.qs.count() == 1
    assert filtro_dias.qs[0].data.day == data.day

    filtro = LogAlunosMatriculadosFaixaEtariaDiaFilter(
        data={"dias": [data.day + 1]},
        queryset=LogAlunosMatriculadosFaixaEtariaDia.objects.all(),
    )
    assert filtro.qs.count() == 0


def test_escola_para_filtros_tipo_unidade_lista(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_emef"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 2
    assert set(filtro.qs.values_list("tipo_unidade__uuid", flat=True)) == {
        escolas_para_filtros["tipo_emef"].uuid
    }


def test_escola_para_filtros_tipo_unidade_lista_multiplos(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [
            str(escolas_para_filtros["tipo_emef"].uuid),
            str(escolas_para_filtros["tipo_cei"].uuid),
        ],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_lote_lista(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.LOTE_UUID.value, [str(escolas_para_filtros["lote_a"].uuid)]
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 2
    assert set(filtro.qs.values_list("lote__uuid", flat=True)) == {
        escolas_para_filtros["lote_a"].uuid
    }


def test_escola_para_filtros_excluir_tipo_unidade(escolas_para_filtros):
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.EXCLUIR_TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_emef"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_cei_lote_a"].uuid


def test_escola_para_filtros_tipo_unidade_in_existente(escolas_para_filtros):
    data = QueryDict(f"tipo_unidade__uuid__in={escolas_para_filtros['tipo_cei'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_cei_lote_a"].uuid


def test_escola_para_filtros_lote_exact_existente(escolas_para_filtros):
    data = QueryDict(f"lote__uuid={escolas_para_filtros['lote_b'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escolas_para_filtros["escola_emef_lote_b"].uuid


def test_escola_para_filtros_diretoria_regional_existente(escolas_para_filtros):
    data = QueryDict(f"diretoria_regional__uuid={escolas_para_filtros['dre'].uuid}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_tipo_gestao_existente(escolas_para_filtros, tipo_gestao):
    data = QueryDict(f"tipo_gestao__nome={tipo_gestao.nome}")

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3


def test_escola_para_filtros_diretoria_regional_lista(escolas_para_filtros):
    outra_dre = baker.make("DiretoriaRegional", nome="OUTRA DRE")
    baker.make(
        Escola,
        codigo_eol="000004",
        diretoria_regional=outra_dre,
        tipo_unidade=escolas_para_filtros["tipo_emef"],
        lote=escolas_para_filtros["lote_a"],
        tipo_gestao=escolas_para_filtros["escola_emef_lote_a"].tipo_gestao,
    )
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(escolas_para_filtros["dre"].uuid)],
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 3
    assert set(filtro.qs.values_list("diretoria_regional__uuid", flat=True)) == {
        escolas_para_filtros["dre"].uuid
    }


def test_escola_para_filtros_subprefeitura_lista(escolas_para_filtros):
    subprefeitura = baker.make("Subprefeitura", nome="CENTRO")
    escola = escolas_para_filtros["escola_emef_lote_a"]
    escola.subprefeitura = subprefeitura
    escola.save()
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.SUBPREFEITURA_UUID.value, [str(subprefeitura.uuid)]
    )

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert filtro.qs.count() == 1
    assert filtro.qs[0].uuid == escola.uuid


def test_escola_para_filtros_combina_dre_lote_subprefeitura_e_tipo(escolas_para_filtros):
    subprefeitura = baker.make("Subprefeitura", nome="SUL")
    escola = escolas_para_filtros["escola_cei_lote_a"]
    escola.subprefeitura = subprefeitura
    escola.save()
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(escolas_para_filtros["dre"].uuid)],
    )
    data.setlist(
        PayloadVariaveis.LOTE_UUID.value, [str(escolas_para_filtros["lote_a"].uuid)]
    )
    data.setlist(
        PayloadVariaveis.SUBPREFEITURA_UUID.value, [str(subprefeitura.uuid)]
    )
    data.setlist(
        PayloadVariaveis.TIPO_UNIDADE_UUID.value,
        [str(escolas_para_filtros["tipo_cei"].uuid)],
    )
    data["tipo_gestao__nome"] = escolas_para_filtros["escola_cei_lote_a"].tipo_gestao.nome

    filtro = EscolaParaFiltrosFilter(
        data=data, queryset=Escola.objects.all().order_by("codigo_eol")
    )

    assert list(filtro.qs.values_list("uuid", flat=True)) == [escola.uuid]


def test_subprefeitura_sem_parametro_mantem_cadastro_completo():
    baker.make("Subprefeitura", nome="NORTE")
    baker.make("Subprefeitura", nome="SUL")

    filtro = SubprefeituraFilter(data=QueryDict(), queryset=Subprefeitura.objects.all())

    assert {"NORTE", "SUL"} <= set(filtro.qs.values_list("nome", flat=True))


def test_subprefeitura_filtra_uma_e_varias_dres_sem_duplicar():
    dre_a = baker.make("DiretoriaRegional", nome="DRE A")
    dre_b = baker.make("DiretoriaRegional", nome="DRE B")
    dre_c = baker.make("DiretoriaRegional", nome="DRE C")
    compartilhada = baker.make("Subprefeitura", nome="COMPARTILHADA")
    compartilhada.diretoria_regional.add(dre_a, dre_b)
    somente_c = baker.make("Subprefeitura", nome="SOMENTE C")
    somente_c.diretoria_regional.add(dre_c)

    data_uma = QueryDict(mutable=True)
    data_uma.setlist("diretoria_regional__uuid", [str(dre_a.uuid)])
    filtro_uma = SubprefeituraFilter(
        data=data_uma, queryset=Subprefeitura.objects.all()
    )
    assert list(filtro_uma.qs.values_list("uuid", flat=True)) == [compartilhada.uuid]

    data_varias = QueryDict(mutable=True)
    data_varias.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(dre_a.uuid), str(dre_b.uuid)],
    )
    filtro_varias = SubprefeituraFilter(
        data=data_varias, queryset=Subprefeitura.objects.all()
    )
    assert list(filtro_varias.qs.values_list("uuid", flat=True)) == [compartilhada.uuid]


def test_subprefeitura_dre_nao_enxerga_fora_do_escopo():
    dre = baker.make("DiretoriaRegional", nome="DRE USUARIO")
    outra = baker.make("DiretoriaRegional", nome="DRE ALHEIA")
    da_dre = baker.make("Subprefeitura", nome="DA DRE")
    da_dre.diretoria_regional.add(dre)
    alheia = baker.make("Subprefeitura", nome="ALHEIA")
    alheia.diretoria_regional.add(outra)
    request = Mock()
    request.user.is_authenticated = True
    request.user.vinculo_atual.instituicao = dre
    data = QueryDict(mutable=True)
    data.setlist(
        PayloadVariaveis.DIRETORIA_REGIONAL_UUID.value,
        [str(dre.uuid), str(outra.uuid)],
    )

    filtro = SubprefeituraFilter(
        data=data, queryset=Subprefeitura.objects.all(), request=request
    )

    assert list(filtro.qs.values_list("uuid", flat=True)) == [da_dre.uuid]
