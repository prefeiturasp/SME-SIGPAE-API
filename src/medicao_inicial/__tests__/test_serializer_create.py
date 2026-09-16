from datetime import date

import pytest
from model_bakery import baker
from types import SimpleNamespace

from src.dados_comuns.constants import GRUPO_PROGRAMAS_E_PROJETOS, TIPOS_UNIDADE_ESCOLAR
from src.medicao_inicial.api.serializers_create import (
    DescontoFinanceiroUpdateSerializer,
    SolicitacaoMedicaoInicialCreateSerializer,
)
from src.medicao_inicial.models import (
    CategoriaMedicao,
    DescontoFinanceiro,
    GrupoMedicao,
    Medicao,
    ValorMedicao,
    TipoContagemAlimentacao,
)


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cei_create(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "periodo_escolar": periodo_escolar_parcial.nome,
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    instance = serializer.save()

    assert instance.tipo_lancamento == "ALIMENTACOES"
    assert instance.quantidade == 10
    assert instance.relatorio_financeiro == relatorio_financeiro_cei
    assert list(instance.unidades_educacionais.all()) == [escola_ceu_gestao]


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cei_update(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
):
    obj = baker.make(
        DescontoFinanceiro,
        relatorio_financeiro=relatorio_financeiro_cei,
        faixa_etaria=faixas_etarias_ativas[0],
        periodo_escolar=periodo_escolar_parcial,
        clausula_desconto=clausula_desconto,
        quantidade=5,
        tipo_lancamento="DIETAS_TIPO_A",
    )

    obj.unidades_educacionais.set([escola_ceu_gestao])

    payload = {
        "tipo_lancamento": "ALIMENTACOES",
        "quantidade": 20,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=obj,
        data=payload,
        partial=True,
    )

    assert serializer.is_valid(), serializer.errors

    updated = serializer.save()

    assert updated.tipo_lancamento == "ALIMENTACOES"
    assert updated.quantidade == 20


@pytest.mark.django_db
def test_desconto_financeiro_grupo_cei_campos_obrigatorios(
    relatorio_financeiro_cei,
    escola_ceu_gestao,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()
    assert "faixa_etaria" in serializer.errors
    assert "periodo_escolar" in serializer.errors
    assert serializer.errors["faixa_etaria"][0] == "Campo obrigatório para o grupo."
    assert serializer.errors["periodo_escolar"][0] == "Campo obrigatório para o grupo."


@pytest.mark.django_db
def test_desconto_financeiro_grupo_emei_nao_permite_faixa_etaria(
    relatorio_financeiro_emei,
    escola_ceu_gestao,
    faixas_etarias_ativas,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emei.uuid),
        "unidades_educacionais": [str(escola_ceu_gestao.uuid)],
        "tipo_lancamento": "ALIMENTACOES",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 10,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()
    assert "faixa_etaria" in serializer.errors
    assert (
        serializer.errors["faixa_etaria"][0]
        == "Não é permitido informar faixa etária para este grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_grupo_cemei_campos_obrigatorios(
    relatorio_financeiro_cemei,
    escola_cemei,
    clausula_desconto,
    faixas_etarias_ativas,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cemei.uuid),
        "unidades_educacionais": [str(escola_cemei.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_B",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 1,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "cei_ou_emei" in serializer.errors
    assert serializer.errors["cei_ou_emei"][0] == "Campo obrigatório para o grupo."

    payload["cei_ou_emei"] = TIPOS_UNIDADE_ESCOLAR.CEI.value

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "faixa_etaria" in serializer.errors
    assert "periodo_escolar" in serializer.errors

    assert serializer.errors["faixa_etaria"][0] == "Campo obrigatório para o grupo."
    assert serializer.errors["periodo_escolar"][0] == "Campo obrigatório para o grupo."

    payload["cei_ou_emei"] = TIPOS_UNIDADE_ESCOLAR.EMEI.value
    payload["faixa_etaria"] = str(faixas_etarias_ativas[0].uuid)

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "faixa_etaria" in serializer.errors
    assert (
        serializer.errors["faixa_etaria"][0]
        == "Não é permitido informar faixa etária para este grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_cemei(
    relatorio_financeiro_cemei,
    escola_cemei,
    faixas_etarias_ativas,
    periodo_escolar_parcial,
    clausula_desconto,
    tipo_alimentacao_refeicao,
):
    payload_create = {
        "relatorio_financeiro_id": str(relatorio_financeiro_cemei.uuid),
        "unidades_educacionais": [str(escola_cemei.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "faixa_etaria": str(faixas_etarias_ativas[0].uuid),
        "periodo_escolar": periodo_escolar_parcial.nome,
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 11,
        "cei_ou_emei": TIPOS_UNIDADE_ESCOLAR.CEI.value,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload_create)
    assert serializer.is_valid(), serializer.errors

    instance_created = serializer.save()

    assert instance_created.tipo_lancamento == "DIETAS_TIPO_A"
    assert instance_created.cei_ou_emei == TIPOS_UNIDADE_ESCOLAR.CEI.value
    assert instance_created.faixa_etaria == faixas_etarias_ativas[0]
    assert instance_created.periodo_escolar == periodo_escolar_parcial

    payload_update = {
        "cei_ou_emei": TIPOS_UNIDADE_ESCOLAR.EMEI.value,
        "tipo_alimentacao": str(tipo_alimentacao_refeicao.uuid),
        "faixa_etaria": None,
        "periodo_escolar": None,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=instance_created,
        data=payload_update,
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors

    instance_updated = serializer.save()

    assert instance_updated.cei_ou_emei == TIPOS_UNIDADE_ESCOLAR.EMEI.value
    assert instance_updated.tipo_alimentacao == tipo_alimentacao_refeicao
    assert instance_updated.faixa_etaria is None
    assert instance_updated.periodo_escolar is None


@pytest.mark.django_db
def test_desconto_financeiro_grupo_emebs_campos_obrigatorios(
    relatorio_financeiro_emebs,
    escola_emebs,
    clausula_desconto,
):
    payload = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emebs.uuid),
        "unidades_educacionais": [str(escola_emebs.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 1,
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload)

    assert not serializer.is_valid()

    assert "infantil_ou_fundamental" in serializer.errors
    assert (
        serializer.errors["infantil_ou_fundamental"][0]
        == "Campo obrigatório para o grupo."
    )


@pytest.mark.django_db
def test_desconto_financeiro_serializer_grupo_emebs(
    relatorio_financeiro_emebs,
    escola_emebs,
    tipo_alimentacao_refeicao,
    clausula_desconto,
):
    payload_create = {
        "relatorio_financeiro_id": str(relatorio_financeiro_emebs.uuid),
        "unidades_educacionais": [str(escola_emebs.uuid)],
        "tipo_lancamento": "DIETAS_TIPO_A",
        "tipo_alimentacao": str(tipo_alimentacao_refeicao.uuid),
        "clausula_desconto": str(clausula_desconto.uuid),
        "quantidade": 11,
        "infantil_ou_fundamental": "INFANTIL",
    }

    serializer = DescontoFinanceiroUpdateSerializer(data=payload_create)
    assert serializer.is_valid(), serializer.errors

    instance_created = serializer.save()

    assert instance_created.tipo_lancamento == "DIETAS_TIPO_A"
    assert instance_created.infantil_ou_fundamental == "INFANTIL"
    assert instance_created.tipo_alimentacao == tipo_alimentacao_refeicao

    payload_update = {
        "infantil_ou_fundamental": "FUNDAMENTAL",
        "faixa_etaria": None,
        "periodo_escolar": None,
    }

    serializer = DescontoFinanceiroUpdateSerializer(
        instance=instance_created,
        data=payload_update,
        partial=True,
    )
    assert serializer.is_valid(), serializer.errors

    instance_updated = serializer.save()

    assert instance_updated.infantil_ou_fundamental == "FUNDAMENTAL"
    assert instance_updated.tipo_alimentacao == tipo_alimentacao_refeicao


DIAS_SEMANA_TODOS = [0, 1, 2, 3, 4, 5, 6]
MOTIVO_PROGRAMAS_PROJETOS = "Programas/Projetos Contínuos"


@pytest.mark.django_db
class TestCriaValoresMedicaoInclusoesContinuas:
    def _setup_dependencias(self):
        categoria, _ = CategoriaMedicao.objects.get_or_create(nome="ALIMENTAÇÃO")
        grupo_programas, _ = GrupoMedicao.objects.get_or_create(
            nome=GRUPO_PROGRAMAS_E_PROJETOS
        )
        grupo_etec, _ = GrupoMedicao.objects.get_or_create(nome="ETEC")
        return categoria, grupo_programas, grupo_etec

    def _setup_escola(self):
        return baker.make("Escola")

    def _setup_solicitacao(self, escola, mes="09", ano="2023"):
        return baker.make(
            "SolicitacaoMedicaoInicial",
            escola=escola,
            mes=mes,
            ano=ano,
        )

    def _setup_inclusao_continua(
        self,
        escola,
        motivo_nome=MOTIVO_PROGRAMAS_PROJETOS,
        data_inicial=date(2023, 9, 1),
        data_final=date(2023, 9, 30),
        status="CODAE_AUTORIZADO",
        numero_alunos=10,
        encerrado_a_partir_de=None,
        cancelado=False,
        dias_semana=None,
        periodo_escolar=None,
    ):
        motivo = baker.make("MotivoInclusaoContinua", nome=motivo_nome)
        inclusao = baker.make(
            "InclusaoAlimentacaoContinua",
            escola=escola,
            rastro_escola=escola,
            data_inicial=data_inicial,
            data_final=data_final,
            motivo=motivo,
            status=status,
        )
        if periodo_escolar is None:
            periodo_escolar = baker.make("PeriodoEscolar", nome="MANHA")
        baker.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao,
            periodo_escolar=periodo_escolar,
            numero_alunos=numero_alunos,
            dias_semana=dias_semana or DIAS_SEMANA_TODOS,
            encerrado_a_partir_de=encerrado_a_partir_de,
            cancelado=cancelado,
        )
        return inclusao

    def _valores_numero_alunos(self, solicitacao, grupo_nome):
        medicao = solicitacao.medicoes.filter(grupo__nome=grupo_nome).first()
        if not medicao:
            return ValorMedicao.objects.none()
        return medicao.valores_medicao.filter(
            nome_campo="numero_de_alunos",
            categoria_medicao__nome="ALIMENTAÇÃO",
        )

    def _dias_criados(self, valores):
        return set(valores.values_list("dia", flat=True))

    def test_cria_valores_quando_inclusao_programas_projetos_autorizada_e_ativa(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(escola, numero_alunos=15)

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valores = self._valores_numero_alunos(solicitacao, GRUPO_PROGRAMAS_E_PROJETOS)
        assert valores.count() == 30
        assert self._dias_criados(valores) == {f"{dia:02d}" for dia in range(1, 31)}
        assert all(valor.valor == "15" for valor in valores)

    def test_nao_cria_valores_nem_medicao_quando_encerramento_antes_do_mes(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola, mes="09", ano="2023")
        self._setup_inclusao_continua(
            escola,
            data_inicial=date(2023, 8, 1),
            data_final=date(2023, 9, 30),
            encerrado_a_partir_de=date(2023, 8, 20),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
        ).exists()
        assert not self._valores_numero_alunos(
            solicitacao, GRUPO_PROGRAMAS_E_PROJETOS
        ).exists()

    def test_nao_cria_quando_encerramento_no_ultimo_dia_do_mes_anterior(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola, mes="09", ano="2023")
        self._setup_inclusao_continua(
            escola,
            data_inicial=date(2023, 8, 1),
            data_final=date(2023, 12, 31),
            encerrado_a_partir_de=date(2023, 8, 31),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
        ).exists()

    def test_cria_valores_somente_ate_data_encerramento_antecipado_no_mesmo_mes(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(
            escola,
            numero_alunos=12,
            encerrado_a_partir_de=date(2023, 9, 10),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valores = self._valores_numero_alunos(solicitacao, GRUPO_PROGRAMAS_E_PROJETOS)
        assert self._dias_criados(valores) == {f"{dia:02d}" for dia in range(1, 11)}
        assert valores.count() == 10
        assert all(valor.valor == "12" for valor in valores)

    def test_cria_apenas_primeiro_dia_quando_encerramento_no_primeiro_dia_do_mes(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(
            escola,
            encerrado_a_partir_de=date(2023, 9, 1),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valores = self._valores_numero_alunos(solicitacao, GRUPO_PROGRAMAS_E_PROJETOS)
        assert self._dias_criados(valores) == {"01"}

    def test_nao_cria_quando_inclusao_nao_autorizada(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(escola, status="ESCOLA_CANCELOU")

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
        ).exists()

    def test_nao_cria_quando_nao_existe_inclusao_continua(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        assert not solicitacao.medicoes.exists()

    def test_etec_respeita_encerramento_antecipado_no_mesmo_mes(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(
            escola,
            motivo_nome="ETEC",
            numero_alunos=8,
            encerrado_a_partir_de=date(2023, 9, 15),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valores = self._valores_numero_alunos(solicitacao, "ETEC")
        assert self._dias_criados(valores) == {f"{dia:02d}" for dia in range(1, 16)}
        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
        ).exists()

    def test_etec_nao_cria_medicao_quando_encerrada_antes_do_mes(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(
            escola,
            motivo_nome="ETEC",
            data_inicial=date(2023, 8, 1),
            data_final=date(2023, 9, 30),
            encerrado_a_partir_de=date(2023, 8, 10),
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome="ETEC",
        ).exists()

    def test_soma_apenas_periodos_ainda_ativos_apos_encerramento_parcial(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        periodo_manha = baker.make("PeriodoEscolar", nome="MANHA")
        periodo_tarde = baker.make("PeriodoEscolar", nome="TARDE")
        inclusao = self._setup_inclusao_continua(
            escola,
            numero_alunos=10,
            encerrado_a_partir_de=date(2023, 9, 10),
            periodo_escolar=periodo_manha,
        )
        baker.make(
            "QuantidadePorPeriodo",
            inclusao_alimentacao_continua=inclusao,
            periodo_escolar=periodo_tarde,
            numero_alunos=20,
            dias_semana=DIAS_SEMANA_TODOS,
            encerrado_a_partir_de=None,
            cancelado=False,
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valores = self._valores_numero_alunos(solicitacao, GRUPO_PROGRAMAS_E_PROJETOS)
        valores_por_dia = {valor.dia: valor.valor for valor in valores}
        assert valores_por_dia["10"] == "30"
        assert valores_por_dia["11"] == "20"
        assert valores_por_dia["30"] == "20"
        assert "01" in valores_por_dia

    def test_nao_recria_valor_quando_numero_de_alunos_ja_existe_no_dia(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(escola, numero_alunos=10)
        categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
        grupo = GrupoMedicao.objects.get(nome=GRUPO_PROGRAMAS_E_PROJETOS)
        medicao = baker.make(
            "Medicao",
            solicitacao_medicao_inicial=solicitacao,
            grupo=grupo,
        )
        baker.make(
            "ValorMedicao",
            medicao=medicao,
            categoria_medicao=categoria,
            dia="05",
            nome_campo="numero_de_alunos",
            valor="99",
        )

        SolicitacaoMedicaoInicialCreateSerializer().cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            solicitacao
        )

        valor_dia_05 = medicao.valores_medicao.get(
            dia="05",
            nome_campo="numero_de_alunos",
            categoria_medicao=categoria,
        )
        assert valor_dia_05.valor == "99"
        assert medicao.valores_medicao.filter(
            dia="05",
            nome_campo="numero_de_alunos",
        ).count() == 1

    def test_nao_cria_medicao_quando_todos_os_dias_ficam_sem_alunos(self):
        self._setup_dependencias()
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        inclusao = self._setup_inclusao_continua(
            escola,
            encerrado_a_partir_de=date(2023, 8, 31),
            data_inicial=date(2023, 8, 1),
            data_final=date(2023, 9, 30),
        )
        serializer = SolicitacaoMedicaoInicialCreateSerializer()
        serializer.cria_valores_medicao_logs_numero_alunos_inclusoes_continuas(
            solicitacao,
            escola.inclusoes_alimentacao_continua.all(),
            30,
            "Programas/Projetos",
            GRUPO_PROGRAMAS_E_PROJETOS,
        )

        assert inclusao.quantidades_periodo.exists()
        assert not Medicao.objects.filter(
            solicitacao_medicao_inicial=solicitacao,
            grupo__nome=GRUPO_PROGRAMAS_E_PROJETOS,
        ).exists()

    def test_valores_por_dia_respeitam_data_inicial_data_final_e_encerramento(self):
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        inclusao = self._setup_inclusao_continua(
            escola,
            data_inicial=date(2023, 9, 5),
            data_final=date(2023, 9, 20),
            numero_alunos=7,
            encerrado_a_partir_de=date(2023, 9, 12),
        )
        serializer = SolicitacaoMedicaoInicialCreateSerializer()

        valores_por_dia = serializer._valores_numero_alunos_inclusoes_continuas_por_dia(
            solicitacao,
            escola.inclusoes_alimentacao_continua.filter(uuid=inclusao.uuid),
            30,
        )

        assert set(valores_por_dia.keys()) == set(range(5, 13))
        assert all(numero == 7 for numero in valores_por_dia.values())

    def test_quantidade_periodo_cancelada_nao_entra_no_numero_de_alunos(self):
        escola = self._setup_escola()
        solicitacao = self._setup_solicitacao(escola)
        self._setup_inclusao_continua(escola, numero_alunos=10, cancelado=True)
        serializer = SolicitacaoMedicaoInicialCreateSerializer()

        valores_por_dia = serializer._valores_numero_alunos_inclusoes_continuas_por_dia(
            solicitacao,
            escola.inclusoes_alimentacao_continua.all(),
            30,
        )

        assert valores_por_dia == {}


@pytest.mark.django_db
def test_solicitacao_medicao_inicial_salva_descricao_do_metodo(
    escola_emei,
    usuario,
):
    tipo_contagem = baker.make(TipoContagemAlimentacao)

    payload = {
        "escola": str(escola_emei.uuid),
        "tipos_contagem_alimentacao": [str(tipo_contagem.uuid)],
        "responsaveis": [
            {
                "nome": "João Silva",
                "rf": "1234567",
            }
        ],
        "mes": "05",
        "ano": "2025",
        "recreio_nas_ferias": None,
        "descricao_metodo": "Contagem manual",
    }

    request = SimpleNamespace(user=usuario)

    serializer = SolicitacaoMedicaoInicialCreateSerializer(
        data=payload,
        context={"request": request},
    )

    assert serializer.is_valid(), serializer.errors

    solicitacao = serializer.save()

    assert solicitacao.descricao_metodo == "Contagem manual"
    assert list(solicitacao.tipos_contagem_alimentacao.all()) == [
        tipo_contagem
    ]
