import calendar
import json
from datetime import date, datetime

import environ
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from sme_sigpae_api.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.dados_comuns.validators import deve_ter_extensao_xls_xlsx_pdf
from sme_sigpae_api.escola.api.serializers_create import (
    AlunoPeriodoParcialCreateSerializer,
)
from sme_sigpae_api.escola.models import (
    Aluno,
    AlunoPeriodoParcial,
    DiretoriaRegional,
    Escola,
    FaixaEtaria,
    Lote,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    CategoriaMedicao,
    ClausulaDeDesconto,
    DiaSobremesaDoce,
    Empenho,
    GrupoMedicao,
    Medicao,
    OcorrenciaMedicaoInicial,
    ParametrizacaoFinanceira,
    ParametrizacaoFinanceiraTabela,
    ParametrizacaoFinanceiraTabelaValor,
    PermissaoLancamentoEspecial,
    Responsavel,
    SolicitacaoMedicaoInicial,
    TipoContagemAlimentacao,
    ValorMedicao,
)
from sme_sigpae_api.perfil.models import Usuario
from sme_sigpae_api.terceirizada.models import Contrato, Edital

from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns.constants import DIRETOR_UE
from ...inclusao_alimentacao.models import InclusaoAlimentacaoContinua
from ..utils import (
    atualiza_alunos_periodo_parcial,
    log_alteracoes_escola_corrige_periodo,
)
from ..validators import (
    valida_medicoes_inexistentes_cei,
    valida_medicoes_inexistentes_ceu_gestao,
    valida_medicoes_inexistentes_emebs,
    validate_lancamento_alimentacoes_inclusoes_ceu_gestao,
    validate_lancamento_alimentacoes_medicao,
    validate_lancamento_alimentacoes_medicao_cei,
    validate_lancamento_alimentacoes_medicao_emebs,
    validate_lancamento_dietas_cei,
    validate_lancamento_dietas_emebs,
    validate_lancamento_dietas_emef,
    validate_lancamento_dietas_inclusoes_ceu_gestao,
    validate_lancamento_inclusoes,
    validate_lancamento_inclusoes_cei,
    validate_lancamento_inclusoes_dietas_cei,
    validate_lancamento_inclusoes_dietas_emef_emebs,
    validate_lancamento_kit_lanche,
    validate_lanche_emergencial,
    validate_medicao_cemei,
    validate_solicitacoes_etec,
    validate_solicitacoes_etec_ceu_gestao,
    validate_solicitacoes_programas_e_projetos,
    validate_solicitacoes_programas_e_projetos_ceu_gestao,
    validate_solicitacoes_programas_e_projetos_emebs,
)


class DiaSobremesaDoceCreateSerializer(serializers.ModelSerializer):
    tipo_unidade = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoUnidadeEscolar.objects.all(),
        required=True,
    )

    criado_por = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Usuario.objects.all(), required=True
    )

    class Meta:
        model = DiaSobremesaDoce
        exclude = ("id",)


class CadastroSobremesaDoceCreateSerializer(serializers.ModelSerializer):
    tipo_unidades = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoUnidadeEscolar.objects.all(),
        required=True,
        many=True,
    )
    editais = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Edital.objects.all(),
        required=True,
        many=True,
    )

    class Meta:
        model = DiaSobremesaDoce
        fields = ("tipo_unidades", "editais")


class DiaSobremesaDoceCreateManySerializer(serializers.ModelSerializer):
    cadastros_calendario = CadastroSobremesaDoceCreateSerializer(
        many=True, required=True
    )

    def create(self, validated_data):
        """Cria ou atualiza dias de sobremesa doce."""
        DiaSobremesaDoce.objects.filter(data=validated_data["data"]).delete()
        dia_sobremesa_doce = None
        for cadastro in validated_data["cadastros_calendario"]:
            for tipo_unidade in cadastro["tipo_unidades"]:
                for edital in cadastro["editais"]:
                    if not DiaSobremesaDoce.objects.filter(
                        data=validated_data["data"],
                        tipo_unidade=tipo_unidade,
                        edital=edital,
                    ):
                        dia_sobremesa_doce = DiaSobremesaDoce(
                            criado_por=self.context["request"].user,
                            data=validated_data["data"],
                            tipo_unidade=tipo_unidade,
                            edital=edital,
                        )
                        dia_sobremesa_doce.save()
        return dia_sobremesa_doce

    class Meta:
        model = DiaSobremesaDoce
        fields = ("data", "uuid", "cadastros_calendario")


class OcorrenciaMedicaoInicialCreateSerializer(serializers.ModelSerializer):
    ultimo_arquivo = serializers.SerializerMethodField()
    nome_ultimo_arquivo = serializers.CharField()

    def get_ultimo_arquivo(self, obj):
        env = environ.Env()
        api_url = env.str("URL_ANEXO", default="http://localhost:8000")
        return f"{api_url}{obj.ultimo_arquivo.url}"

    def validate_nome_ultimo_arquivo(self, nome_ultimo_arquivo):
        deve_ter_extensao_xls_xlsx_pdf(nome_ultimo_arquivo)
        return nome_ultimo_arquivo

    class Meta:
        model = OcorrenciaMedicaoInicial
        exclude = (
            "id",
            "solicitacao_medicao_inicial",
        )


class ResponsavelCreateSerializer(serializers.ModelSerializer):
    nome = serializers.CharField()
    rf = serializers.CharField()

    class Meta:
        model = Responsavel
        exclude = (
            "id",
            "solicitacao_medicao_inicial",
        )


class SolicitacaoMedicaoInicialCreateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    tipos_contagem_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=TipoContagemAlimentacao.objects.all(),
        many=True,
    )
    alunos_periodo_parcial = AlunoPeriodoParcialCreateSerializer(
        many=True, required=False
    )
    responsaveis = ResponsavelCreateSerializer(many=True)
    com_ocorrencias = serializers.BooleanField(required=False)
    ocorrencia = OcorrenciaMedicaoInicialCreateSerializer(required=False)
    logs = LogSolicitacoesUsuarioSerializer(many=True, required=False)
    justificativa_sem_lancamentos = serializers.CharField(required=False)

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        responsaveis_dict = validated_data.pop("responsaveis", [])
        alunos_periodo_parcial = validated_data.pop("alunos_periodo_parcial", [])
        tipos_contagem_alimentacao = validated_data.pop(
            "tipos_contagem_alimentacao", []
        )
        solicitacao = SolicitacaoMedicaoInicial.objects.create(**validated_data)
        solicitacao.tipos_contagem_alimentacao.set(tipos_contagem_alimentacao)
        for responsavel in responsaveis_dict:
            Responsavel.objects.create(
                solicitacao_medicao_inicial=solicitacao,
                nome=responsavel.get("nome", ""),
                rf=responsavel.get("rf", ""),
            )
        if alunos_periodo_parcial:
            escola_associada = validated_data.get("escola")
            atualiza_alunos_periodo_parcial(solicitacao, alunos_periodo_parcial)
            for aluno in alunos_periodo_parcial:
                AlunoPeriodoParcial.objects.create(
                    solicitacao_medicao_inicial=solicitacao,
                    aluno=Aluno.objects.get(uuid=aluno.get("aluno", "")),
                    data=aluno.get("data", ""),
                    escola=escola_associada,
                )

        solicitacao.inicia_fluxo(user=self.context["request"].user)
        return solicitacao

    def valida_finalizar_medicao_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_emef_emei_cieja
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []

        lista_erros = validate_lancamento_alimentacoes_medicao(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes(instance, lista_erros)
        lista_erros = validate_lancamento_dietas_emef(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes_dietas_emef_emebs(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        lista_erros = validate_solicitacoes_etec(instance, lista_erros)
        lista_erros = validate_solicitacoes_programas_e_projetos(instance, lista_erros)

        if lista_erros:
            raise ValidationError(lista_erros)

    # TODO: adicionar testes unitarios
    def valida_finalizar_medicao_cemei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:  # pragma: no cover
        if (
            not instance.escola.eh_cemei
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return
        lista_erros = validate_medicao_cemei(instance)
        if lista_erros:
            raise ValidationError(lista_erros)

    def valida_finalizar_medicao_cei(self, instance: SolicitacaoMedicaoInicial) -> None:
        if (
            not instance.escola.eh_cei
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = valida_medicoes_inexistentes_cei(instance, lista_erros)
        lista_erros = validate_lancamento_alimentacoes_medicao_cei(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_inclusoes_cei(instance, lista_erros)
        lista_erros = validate_lancamento_dietas_cei(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes_dietas_cei(instance, lista_erros)
        if lista_erros:
            raise ValidationError(lista_erros)

    def valida_finalizar_medicao_ceu_gestao(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_ceu_gestao
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = valida_medicoes_inexistentes_ceu_gestao(instance, lista_erros)
        lista_erros = validate_lancamento_alimentacoes_inclusoes_ceu_gestao(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_dietas_inclusoes_ceu_gestao(
            instance, lista_erros
        )
        lista_erros = validate_solicitacoes_programas_e_projetos_ceu_gestao(
            instance, lista_erros
        )
        lista_erros = validate_solicitacoes_etec_ceu_gestao(instance, lista_erros)
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)

        if lista_erros:
            raise ValidationError(lista_erros)

    def valida_finalizar_medicao_emebs(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_emebs
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = valida_medicoes_inexistentes_emebs(instance, lista_erros)
        lista_erros = validate_lancamento_alimentacoes_medicao_emebs(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_inclusoes(instance, lista_erros, True)
        lista_erros = validate_lancamento_dietas_emebs(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes_dietas_emef_emebs(
            instance, lista_erros, True
        )
        lista_erros = validate_solicitacoes_programas_e_projetos_emebs(
            instance, lista_erros
        )

        if lista_erros:
            raise ValidationError(lista_erros)

    def cria_valores_medicao_logs_alunos_matriculados_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        valores_medicao_a_criar = []
        logs_do_mes = escola.logs_alunos_matriculados_por_periodo.filter(
            criado_em__month=instance.mes,
            criado_em__year=instance.ano,
            tipo_turma="REGULAR",
        )
        categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        for dia in range(1, quantidade_dias_mes + 1):
            for periodo_escolar in escola.periodos_escolares_com_alunos:
                try:
                    medicao = instance.medicoes.get(
                        periodo_escolar__nome=periodo_escolar
                    )
                except Medicao.DoesNotExist:
                    medicao = Medicao.objects.create(
                        solicitacao_medicao_inicial=instance,
                        periodo_escolar=PeriodoEscolar.objects.get(
                            nome=periodo_escolar
                        ),
                    )
                if not medicao.valores_medicao.filter(
                    categoria_medicao=categoria,
                    dia=f"{dia:02d}",
                    nome_campo="matriculados",
                ).exists():
                    log = logs_do_mes.filter(
                        periodo_escolar__nome=periodo_escolar, criado_em__day=dia
                    ).first()
                    valor_medicao = ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=f"{dia:02d}",
                        nome_campo="matriculados",
                        valor=log.quantidade_alunos if log else 0,
                    )
                    valores_medicao_a_criar.append(valor_medicao)

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def analisa_periodos_por_dia_matriculados(
        self,
        logs_do_mes,
        dia,
        periodo_escolar,
        medicao,
        categoria,
        valores_medicao_a_criar,
    ):
        for log in logs_do_mes.filter(
            data__day=dia, periodo_escolar__nome=periodo_escolar
        ):
            if not medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo="matriculados",
                faixa_etaria=log.faixa_etaria,
            ).exists():
                valor_medicao = ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=f"{dia:02d}",
                    nome_campo="matriculados",
                    valor=log.quantidade,
                    faixa_etaria=log.faixa_etaria,
                )
                valores_medicao_a_criar.append(valor_medicao)
        return valores_medicao_a_criar

    def cria_valores_medicao_logs_alunos_matriculados_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        valores_medicao_a_criar = []
        logs_do_mes = escola.logs_alunos_matriculados_por_faixa_etaria.filter(
            data__month=instance.mes,
            data__year=instance.ano,
        )
        categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        for dia in range(1, quantidade_dias_mes + 1):
            periodos_escolares_com_alunos = escola.periodos_escolares_com_alunos
            if instance.ue_possui_alunos_periodo_parcial:
                periodos_escolares_com_alunos.append("PARCIAL")
            for periodo_escolar in periodos_escolares_com_alunos:
                try:
                    medicao = instance.medicoes.get(
                        periodo_escolar__nome=periodo_escolar
                    )
                except Medicao.DoesNotExist:
                    medicao = Medicao.objects.create(
                        solicitacao_medicao_inicial=instance,
                        periodo_escolar=PeriodoEscolar.objects.get(
                            nome=periodo_escolar
                        ),
                    )
                valores_medicao_a_criar = self.analisa_periodos_por_dia_matriculados(
                    logs_do_mes,
                    dia,
                    periodo_escolar,
                    medicao,
                    categoria,
                    valores_medicao_a_criar,
                )

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def checa_se_existe_ao_menos_um_log_quantidade_maior_que_0(
        self, categoria: CategoriaMedicao, logs_do_mes: QuerySet, periodo_escolar: str
    ) -> bool:
        if categoria == CategoriaMedicao.objects.get(
            nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
        ):
            if not logs_do_mes.filter(
                classificacao__nome__in=[
                    "Tipo A ENTERAL",
                    "Tipo A RESTRIÇÃO DE AMINOÁCIDOS",
                ],
                periodo_escolar__nome=periodo_escolar,
                quantidade__gt=0,
            ).exists():
                return True
        else:
            if (
                not logs_do_mes.filter(
                    classificacao__nome__icontains=categoria.nome.split(" - ")[1],
                    periodo_escolar__nome=periodo_escolar,
                    quantidade__gt=0,
                )
                .exclude(classificacao__nome__icontains="enteral")
                .exclude(classificacao__nome__icontains="aminoácidos")
                .exists()
            ):
                return True
        return False

    def retorna_valor_para_log_dieta_autorizada(
        self,
        categoria: CategoriaMedicao,
        logs_do_mes: QuerySet,
        periodo_escolar: str,
        dia: int,
    ) -> int:
        if categoria == CategoriaMedicao.objects.get(
            nome="DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS"
        ):
            log_enteral = logs_do_mes.filter(
                classificacao__nome__icontains="enteral",
                periodo_escolar__nome=periodo_escolar,
                data__day=dia,
            ).first()
            log_restricao_aminoacidos = logs_do_mes.filter(
                classificacao__nome__icontains="aminoácidos",
                periodo_escolar__nome=periodo_escolar,
                data__day=dia,
            ).first()
            valor = (log_enteral.quantidade if log_enteral else 0) + (
                log_restricao_aminoacidos.quantidade if log_restricao_aminoacidos else 0
            )
        else:
            log = (
                logs_do_mes.filter(
                    classificacao__nome__icontains=categoria.nome.split(" - ")[1],
                    periodo_escolar__nome=periodo_escolar,
                    data__day=dia,
                )
                .exclude(classificacao__nome__icontains="enteral")
                .exclude(classificacao__nome__icontains="aminoácidos")
                .first()
            )
            valor = log.quantidade if log else 0
        return valor

    def cria_valores_medicao_logs_dietas_autorizadas_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        valores_medicao_a_criar = []
        logs_do_mes = escola.logs_dietas_autorizadas.filter(
            data__month=instance.mes, data__year=instance.ano
        )
        categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        for dia in range(1, quantidade_dias_mes + 1):
            for categoria in categorias:
                for periodo_escolar in escola.periodos_escolares_com_alunos:
                    medicao = instance.medicoes.get(
                        periodo_escolar__nome=periodo_escolar
                    )
                    if self.checa_se_existe_ao_menos_um_log_quantidade_maior_que_0(
                        categoria, logs_do_mes, periodo_escolar
                    ):
                        continue
                    if not medicao.valores_medicao.filter(
                        categoria_medicao=categoria,
                        dia=f"{dia:02d}",
                        nome_campo="dietas_autorizadas",
                    ).exists():
                        valor = self.retorna_valor_para_log_dieta_autorizada(
                            categoria, logs_do_mes, periodo_escolar, dia
                        )
                        valor_medicao = ValorMedicao(
                            medicao=medicao,
                            categoria_medicao=categoria,
                            dia=f"{dia:02d}",
                            nome_campo="dietas_autorizadas",
                            valor=valor,
                        )
                        valores_medicao_a_criar.append(valor_medicao)
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def logs_filtrados_cei(self, categoria, logs_do_mes, dia, periodo_escolar):
        if categoria == CategoriaMedicao.objects.get(nome="DIETA ESPECIAL - TIPO A"):
            logs = logs_do_mes.filter(
                classificacao__nome__icontains="TIPO A",
                data__day=dia,
                periodo_escolar__nome=periodo_escolar,
            )
            return logs
        else:
            logs = logs_do_mes.filter(
                data__day=dia,
                periodo_escolar__nome=periodo_escolar,
                classificacao__nome__icontains=categoria.nome.split(" - ")[1],
            ).exclude(classificacao__nome__icontains="TIPO A")
            return logs

    def valor_log_dietas_autorizadas_cei(
        self, categoria, log, logs, valores_medicao_a_criar
    ):
        if categoria == CategoriaMedicao.objects.get(nome="DIETA ESPECIAL - TIPO A"):
            return sum(
                logs.filter(faixa_etaria=log.faixa_etaria).values_list(
                    "quantidade", flat=True
                )
            )
        else:
            return log.quantidade

    def checa_se_ja_existe_valor_dieta_tipo_a(self, valores_medicao_a_criar, log):
        return [
            v.faixa_etaria
            for v in valores_medicao_a_criar
            if "TIPO A" in v.categoria_medicao.nome
            and v.medicao.nome_periodo_grupo == log.periodo_escolar.nome
            and v.faixa_etaria == log.faixa_etaria
            and v.dia == f"{log.data.day:02d}"
        ]

    def append_valores_medicao_a_criar(
        self, valores_medicao_a_criar, medicao, categoria, dia, log, logs
    ):
        if not medicao.valores_medicao.filter(
            categoria_medicao=categoria,
            dia=f"{dia:02d}",
            nome_campo="dietas_autorizadas",
            faixa_etaria=log.faixa_etaria,
        ).exists():
            valor = self.valor_log_dietas_autorizadas_cei(
                categoria, log, logs, valores_medicao_a_criar
            )
            valor_medicao = ValorMedicao(
                medicao=medicao,
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo="dietas_autorizadas",
                valor=valor,
                faixa_etaria=log.faixa_etaria,
            )
            if categoria == CategoriaMedicao.objects.get(
                nome="DIETA ESPECIAL - TIPO A"
            ):
                if not self.checa_se_ja_existe_valor_dieta_tipo_a(
                    valores_medicao_a_criar, log
                ):
                    valores_medicao_a_criar.append(valor_medicao)
            else:
                valores_medicao_a_criar.append(valor_medicao)
        return valores_medicao_a_criar

    def analisa_periodos_por_dia_dietas_autorizadas(
        self,
        periodos_escolares_com_alunos,
        instance,
        categoria,
        logs_do_mes,
        dia,
        valores_medicao_a_criar,
    ):
        for periodo_escolar in periodos_escolares_com_alunos:
            medicao = instance.medicoes.get(periodo_escolar__nome=periodo_escolar)
            if self.checa_se_existe_ao_menos_um_log_quantidade_maior_que_0(
                categoria, logs_do_mes, periodo_escolar
            ):
                continue
            logs = self.logs_filtrados_cei(categoria, logs_do_mes, dia, periodo_escolar)
            for log in logs:
                valores_medicao_a_criar = self.append_valores_medicao_a_criar(
                    valores_medicao_a_criar, medicao, categoria, dia, log, logs
                )
        return valores_medicao_a_criar

    def cria_valores_medicao_logs_dietas_autorizadas_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        valores_medicao_a_criar = []
        logs_do_mes = escola.logs_dietas_autorizadas_cei.filter(
            data__month=instance.mes, data__year=instance.ano
        )
        categorias = CategoriaMedicao.objects.filter(
            nome__in=["DIETA ESPECIAL - TIPO A", "DIETA ESPECIAL - TIPO B"]
        )
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        for dia in range(1, quantidade_dias_mes + 1):
            for categoria in categorias:
                periodos_escolares_com_alunos = escola.periodos_escolares_com_alunos
                if instance.ue_possui_alunos_periodo_parcial:
                    periodos_escolares_com_alunos.append("PARCIAL")
                valores_medicao_a_criar = (
                    self.analisa_periodos_por_dia_dietas_autorizadas(
                        periodos_escolares_com_alunos,
                        instance,
                        categoria,
                        logs_do_mes,
                        dia,
                        valores_medicao_a_criar,
                    )
                )
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def retorna_medicao_por_nome_grupo(
        self, instance: SolicitacaoMedicaoInicial, nome_grupo: str
    ) -> Medicao:
        try:
            medicao = instance.medicoes.get(grupo__nome=nome_grupo)
        except Medicao.DoesNotExist:
            grupo = GrupoMedicao.objects.get(nome=nome_grupo)
            medicao = Medicao.objects.create(
                solicitacao_medicao_inicial=instance, grupo=grupo
            )
        return medicao

    def retorna_numero_alunos_dia(
        self, inclusao: InclusaoAlimentacaoContinua, data: date
    ) -> int:
        dia_semana = data.weekday()
        numero_alunos = 0
        for quantidade_periodo in inclusao.quantidades_periodo.filter(
            dias_semana__icontains=dia_semana, cancelado=False
        ):
            numero_alunos += quantidade_periodo.numero_alunos
        return numero_alunos

    def cria_valor_medicao(
        self,
        numero_alunos: int,
        medicao: Medicao,
        categoria: CategoriaMedicao,
        dia: int,
        nome_campo: str,
        valores_medicao_a_criar: list,
    ) -> list:
        if numero_alunos > 0:
            valor_medicao = ValorMedicao(
                medicao=medicao,
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo=nome_campo,
                valor=numero_alunos,
            )
            valores_medicao_a_criar.append(valor_medicao)
        return valores_medicao_a_criar

    def cria_valores_medicao_logs_numero_alunos_inclusoes_continuas(
        self,
        instance: SolicitacaoMedicaoInicial,
        inclusoes_continuas: QuerySet,
        quantidade_dias_mes: int,
        nome_motivo: str,
        nome_grupo: str,
    ) -> None:
        if not inclusoes_continuas.filter(motivo__nome__icontains=nome_motivo).exists():
            return
        categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
        medicao = self.retorna_medicao_por_nome_grupo(instance, nome_grupo)
        valores_medicao_a_criar = []
        for dia in range(1, quantidade_dias_mes + 1):
            data = date(year=int(instance.ano), month=int(instance.mes), day=dia)
            numero_alunos = 0
            for inclusao in inclusoes_continuas.filter(
                motivo__nome__icontains=nome_motivo
            ):
                if not (inclusao.data_inicial <= data <= inclusao.data_final):
                    continue
                if medicao.valores_medicao.filter(
                    categoria_medicao=categoria,
                    dia=f"{dia:02d}",
                    nome_campo="numero_de_alunos",
                ).exists():
                    continue
                numero_alunos += self.retorna_numero_alunos_dia(inclusao, data)
            valores_medicao_a_criar = self.cria_valor_medicao(
                numero_alunos,
                medicao,
                categoria,
                dia,
                "numero_de_alunos",
                valores_medicao_a_criar,
            )
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        ultimo_dia_mes = date(
            year=int(instance.ano), month=int(instance.mes), day=quantidade_dias_mes
        )
        primeiro_dia_mes = date(year=int(instance.ano), month=int(instance.mes), day=1)
        inclusoes_continuas = escola.inclusoes_alimentacao_continua.filter(
            status="CODAE_AUTORIZADO",
            data_inicial__lte=ultimo_dia_mes,
            data_final__gte=primeiro_dia_mes,
        )
        if not inclusoes_continuas.count():
            return
        self.cria_valores_medicao_logs_numero_alunos_inclusoes_continuas(
            instance,
            inclusoes_continuas,
            quantidade_dias_mes,
            "Programas/Projetos",
            "Programas e Projetos",
        )
        self.cria_valores_medicao_logs_numero_alunos_inclusoes_continuas(
            instance, inclusoes_continuas, quantidade_dias_mes, "ETEC", "ETEC"
        )

    def cria_valores_medicao_logs_numero_alunos_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        self.cria_valores_medicao_logs_numero_alunos_inclusoes_continuas_emef_emei(
            instance
        )

    def cria_valores_medicao_kit_lanches_emef_emei_ceu_gestao(
        self, instance, kits_lanche, kits_lanche_unificado
    ):
        valores_medicao_a_criar = []
        medicao = self.retorna_medicao_por_nome_grupo(
            instance, "Solicitações de Alimentação"
        )
        categoria = CategoriaMedicao.objects.get(nome="SOLICITAÇÕES DE ALIMENTAÇÃO")
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        for dia in range(1, quantidade_dias_mes + 1):
            if medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                dia=f"{dia:02d}",
                nome_campo="kit_lanche",
            ).exists():
                continue
            total_dia = 0
            for kit_lanche in kits_lanche.filter(solicitacao_kit_lanche__data__day=dia):
                total_dia += kit_lanche.quantidade_alimentacoes
            for kit_lanche in kits_lanche_unificado.filter(
                solicitacao_unificada__solicitacao_kit_lanche__data__day=dia
            ):
                total_dia += kit_lanche.total_kit_lanche
            valores_medicao_a_criar = self.cria_valor_medicao(
                total_dia,
                medicao,
                categoria,
                dia,
                "kit_lanche",
                valores_medicao_a_criar,
            )
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def cria_valores_medicao_logs_kit_lanche_lanches_emergenciais_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        kits_lanche = escola.kit_lanche_solicitacaokitlancheavulsa_rastro_escola.filter(
            status="CODAE_AUTORIZADO",
            solicitacao_kit_lanche__data__month=instance.mes,
            solicitacao_kit_lanche__data__year=instance.ano,
        )
        kits_lanche_unificado = escola.escolaquantidade_set.filter(
            solicitacao_unificada__status="CODAE_AUTORIZADO",
            solicitacao_unificada__solicitacao_kit_lanche__data__month=instance.mes,
            solicitacao_unificada__solicitacao_kit_lanche__data__year=instance.ano,
            cancelado=False,
        )
        lanches_emergenciais = escola.alteracaocardapio_set.filter(
            motivo__nome="Lanche Emergencial",
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=instance.mes,
            datas_intervalo__data__year=instance.ano,
            datas_intervalo__cancelado=False,
        )

        if (
            not kits_lanche.exists()
            and not kits_lanche_unificado.exists()
            and not lanches_emergenciais.exists()
        ):
            return

        self.cria_valores_medicao_kit_lanches_emef_emei_ceu_gestao(
            instance, kits_lanche, kits_lanche_unificado
        )

    def cria_valores_medicao_logs_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if not instance.escola.eh_emef_emei_cieja or instance.logs_salvos:
            return

        self.cria_valores_medicao_logs_alunos_matriculados_emef_emei(instance)
        self.cria_valores_medicao_logs_dietas_autorizadas_emef_emei(instance)
        self.cria_valores_medicao_logs_numero_alunos_emef_emei(instance)
        self.cria_valores_medicao_logs_kit_lanche_lanches_emergenciais_emef_emei(
            instance
        )

        instance.logs_salvos = True
        instance.save()

    def cria_valores_medicao_logs_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if not instance.escola.eh_cei or instance.logs_salvos:
            return

        self.cria_valores_medicao_logs_alunos_matriculados_cei(instance)
        self.cria_valores_medicao_logs_dietas_autorizadas_cei(instance)

        instance.logs_salvos = True
        instance.save()

    def update(self, instance, validated_data):
        self._check_user_permission()
        self._update_instance_fields(instance, validated_data)
        self._update_responsaveis(instance)
        self._update_alunos(instance, validated_data)
        self._update_tipos_contagem_alimentacao(instance)
        anexos = self._process_anexos(instance)
        self._finaliza_medicao_se_necessario(instance, validated_data, anexos)
        self._finaliza_medicao_sem_lancamentos(instance, validated_data)
        return instance

    def _check_user_permission(self):
        if (
            isinstance(self.context["request"].user.vinculo_atual.instituicao, Escola)
            and self.context["request"].user.vinculo_atual.perfil.nome != DIRETOR_UE
        ):
            raise PermissionDenied("Você não tem permissão para executar essa ação.")

    def _update_instance_fields(self, instance, validated_data):
        if "dre_ciencia_correcao_data" in validated_data:
            validated_data["dre_ciencia_correcao_usuario"] = self.context[
                "request"
            ].user
        update_instance_from_dict(instance, validated_data, save=True)

    def _update_responsaveis(self, instance):
        responsaveis_dict = self.context["request"].data.get("responsaveis")
        if responsaveis_dict:
            instance.responsaveis.all().delete()
            for responsavel_data in json.loads(responsaveis_dict):
                Responsavel.objects.create(
                    solicitacao_medicao_inicial=instance, **responsavel_data
                )

    def _update_alunos(self, instance, validated_data):
        alunos_periodo_parcial = self.context["request"].data.get(
            "alunos_periodo_parcial"
        )
        if alunos_periodo_parcial:
            escola_associada = validated_data.get("escola")
            if self.context["request"].data.get("alunos_parcial_alterado") == "true":
                atualiza_alunos_periodo_parcial(
                    instance, json.loads(alunos_periodo_parcial)
                )
            instance.alunos_periodo_parcial.all().delete()
            for aluno in json.loads(alunos_periodo_parcial):
                (dia, mes, ano) = aluno.get("data", "").split("/")
                dia = int(dia)
                mes = int(mes)
                ano = int(ano)
                if aluno.get("data_removido", ""):
                    (dia_, mes_, ano_) = aluno.get("data_removido", "").split("/")
                    dia_ = int(dia_)
                    mes_ = int(mes_)
                    ano_ = int(ano_)
                AlunoPeriodoParcial.objects.create(
                    solicitacao_medicao_inicial=instance,
                    aluno=Aluno.objects.get(uuid=aluno.get("aluno", "")),
                    data=date(ano, mes, dia),
                    data_removido=(
                        date(ano_, mes_, dia_)
                        if aluno.get("data_removido", "")
                        else None
                    ),
                    escola=escola_associada,
                )

    def _update_tipos_contagem_alimentacao(self, instance):
        tipos_contagem_alimentacao = self._get_tipos_contagem_alimentacao_from_request()
        if tipos_contagem_alimentacao:
            tipos_contagem_alimentacao = TipoContagemAlimentacao.objects.filter(
                uuid__in=tipos_contagem_alimentacao
            )
            instance.tipos_contagem_alimentacao.set(tipos_contagem_alimentacao)

    def _get_tipos_contagem_alimentacao_from_request(self):
        if "tipos_contagem_alimentacao[]" in self.context["request"].data:
            return self.context["request"].data.getlist("tipos_contagem_alimentacao[]")
        return self.context["request"].data.get("tipos_contagem_alimentacao")

    def _process_anexos(self, instance):
        anexos_string = self.context["request"].data.get("anexos")
        if anexos_string:
            anexos = json.loads(anexos_string)
            for anexo in anexos:
                if ".pdf" in anexo["nome"]:
                    arquivo = convert_base64_to_contentfile(anexo["base64"])
                    OcorrenciaMedicaoInicial.objects.update_or_create(
                        solicitacao_medicao_inicial=instance,
                        defaults={
                            "ultimo_arquivo": arquivo,
                            "nome_ultimo_arquivo": anexo.get("nome"),
                        },
                    )
            return anexos

    def _finaliza_medicao_se_necessario(self, instance, validated_data, anexos):
        if validated_data.get("justificativa_sem_lancamentos", None):
            return
        key_com_ocorrencias = validated_data.get("com_ocorrencias", None)
        if key_com_ocorrencias is not None and self.context["request"].data.get(
            "finaliza_medicao"
        ):
            self.cria_valores_medicao_logs_emef_emei(instance)
            self.cria_valores_medicao_logs_cei(instance)
            self.valida_finalizar_medicao_emef_emei(instance)
            self.valida_finalizar_medicao_cemei(instance)
            self.valida_finalizar_medicao_cei(instance)
            self.valida_finalizar_medicao_ceu_gestao(instance)
            self.valida_finalizar_medicao_emebs(instance)
            instance.ue_envia(user=self.context["request"].user)
            if hasattr(instance, "ocorrencia"):
                instance.ocorrencia.ue_envia(
                    user=self.context["request"].user, anexos=anexos
                )
            for medicao in instance.medicoes.all():
                medicao.ue_envia(user=self.context["request"].user)

    def _checa_se_pode_finalizar_sem_lancamentos(self, instance) -> None:
        medicoes_nomes_com_solicitacoes_autorizadas = (
            instance.escola.get_lista_medicoes_solicitacoes_autorizadas_no_mes(
                int(instance.mes), int(instance.ano)
            )
        )
        if medicoes_nomes_com_solicitacoes_autorizadas:
            lista_erros = []
            for medicao_nome in medicoes_nomes_com_solicitacoes_autorizadas:
                medicao = instance.get_or_create_medicao_por_periodo_e_ou_grupo(
                    medicao_nome
                )
                if medicao_nome in ["Programas e Projetos", "ETEC"]:
                    if not medicao.possui_ao_menos_uma_observacao():
                        lista_erros.append(
                            {
                                "periodo_escolar": medicao_nome,
                                "erro": "Existem solicitações de alimentações no período, "
                                "adicione ao menos uma justificativa para finalizar",
                            }
                        )
                else:
                    lista_erros.append(
                        {
                            "periodo_escolar": medicao_nome,
                            "erro": "Existem solicitações de alimentações no período. "
                            "Não é possível finalizar sem lançamentos.",
                        }
                    )

            if lista_erros:
                raise serializers.ValidationError(lista_erros)

    def _finaliza_medicao_sem_lancamentos(self, instance, validated_data):
        if not validated_data.get("justificativa_sem_lancamentos", None):
            return
        self._checa_se_pode_finalizar_sem_lancamentos(instance)
        instance.ue_envia(user=self.context["request"].user)
        for medicao in instance.medicoes.all():
            medicao.ue_envia(user=self.context["request"].user)

    class Meta:
        model = SolicitacaoMedicaoInicial
        exclude = (
            "id",
            "criado_por",
        )


class ValorMedicaoCreateUpdateSerializer(serializers.ModelSerializer):
    valor = serializers.CharField()
    nome_campo = serializers.CharField()
    categoria_medicao = serializers.SlugRelatedField(
        slug_field="id",
        required=True,
        queryset=CategoriaMedicao.objects.all(),
    )
    tipo_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=FaixaEtaria.objects.all(),
    )
    medicao_uuid = serializers.SerializerMethodField()
    medicao_alterado_em = serializers.SerializerMethodField()

    def get_medicao_alterado_em(self, obj):
        if obj.medicao.alterado_em:
            return datetime.strftime(obj.medicao.alterado_em, "%d/%m/%Y, às %H:%M:%S")

    def get_medicao_uuid(self, obj):
        return obj.medicao.uuid

    class Meta:
        model = ValorMedicao
        exclude = (
            "id",
            "medicao",
        )


class MedicaoCreateUpdateSerializer(serializers.ModelSerializer):
    solicitacao_medicao_inicial = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=SolicitacaoMedicaoInicial.objects.all(),
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="nome",
        required=False,
        queryset=PeriodoEscolar.objects.all(),
    )
    grupo = serializers.SlugRelatedField(
        slug_field="nome",
        required=False,
        queryset=GrupoMedicao.objects.all(),
    )
    valores_medicao = ValorMedicaoCreateUpdateSerializer(many=True, required=False)
    infantil_ou_fundamental = serializers.CharField(required=False)

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        valores_medicao_dict = validated_data.pop("valores_medicao", None)

        if validated_data.get("periodo_escolar", "") and validated_data.get(
            "grupo", ""
        ):
            medicao, created = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=validated_data.get(
                    "solicitacao_medicao_inicial", ""
                ),
                periodo_escolar=validated_data.get("periodo_escolar", ""),
                grupo=validated_data.get("grupo", ""),
            )
        elif validated_data.get("periodo_escolar", "") and not validated_data.get(
            "grupo", ""
        ):
            medicao, created = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=validated_data.get(
                    "solicitacao_medicao_inicial", ""
                ),
                periodo_escolar=validated_data.get("periodo_escolar", ""),
                grupo=None,
            )
        else:
            medicao, created = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=validated_data.get(
                    "solicitacao_medicao_inicial", ""
                ),
                grupo=validated_data.get("grupo", ""),
                periodo_escolar=None,
            )
        medicao.save()
        infantil_ou_fundamental = validated_data.pop("infantil_ou_fundamental", "N/A")

        for valor_medicao in valores_medicao_dict:
            dia = int(valor_medicao.get("dia", ""))
            mes = int(medicao.solicitacao_medicao_inicial.mes)
            ano = int(medicao.solicitacao_medicao_inicial.ano)
            semana = ValorMedicao.get_week_of_month(ano, mes, dia)
            ValorMedicao.objects.update_or_create(
                medicao=medicao,
                dia=valor_medicao.get("dia", ""),
                semana=semana,
                nome_campo=valor_medicao.get("nome_campo", ""),
                categoria_medicao=valor_medicao.get("categoria_medicao", ""),
                tipo_alimentacao=valor_medicao.get("tipo_alimentacao", None),
                faixa_etaria=valor_medicao.get("faixa_etaria", None),
                infantil_ou_fundamental=infantil_ou_fundamental,
                defaults={
                    "valor": valor_medicao.get("valor", ""),
                },
            )

        return medicao

    def update(self, instance, validated_data):  # noqa C901
        user = self.context["request"].user
        acao = instance.workflow_class.MEDICAO_CORRIGIDA_PELA_UE
        valores = validated_data.get("valores_medicao", None)
        if instance.status in [
            acao,
            instance.workflow_class.MEDICAO_CORRECAO_SOLICITADA,
        ]:
            log_alteracoes_escola_corrige_periodo(user, instance, acao, valores)

        valores_medicao_dict = validated_data.pop("valores_medicao", None)
        infantil_ou_fundamental = validated_data.pop("infantil_ou_fundamental", "N/A")

        if valores_medicao_dict:
            for valor_medicao in valores_medicao_dict:
                dia = int(valor_medicao.get("dia", ""))
                mes = int(instance.solicitacao_medicao_inicial.mes)
                ano = int(instance.solicitacao_medicao_inicial.ano)
                semana = ValorMedicao.get_week_of_month(ano, mes, dia)
                try:
                    ValorMedicao.objects.update_or_create(
                        medicao=instance,
                        dia=valor_medicao.get("dia", ""),
                        semana=semana,
                        nome_campo=valor_medicao.get("nome_campo", ""),
                        categoria_medicao=valor_medicao.get("categoria_medicao", ""),
                        tipo_alimentacao=valor_medicao.get("tipo_alimentacao", None),
                        faixa_etaria=valor_medicao.get("faixa_etaria", None),
                        infantil_ou_fundamental=infantil_ou_fundamental,
                        defaults={
                            "valor": valor_medicao.get("valor", ""),
                        },
                    )
                except ValorMedicao.MultipleObjectsReturned:
                    ValorMedicao.objects.filter(
                        medicao=instance,
                        dia=valor_medicao.get("dia", ""),
                        semana=semana,
                        nome_campo=valor_medicao.get("nome_campo", ""),
                        categoria_medicao=valor_medicao.get("categoria_medicao", ""),
                        tipo_alimentacao=valor_medicao.get("tipo_alimentacao", None),
                        faixa_etaria=valor_medicao.get("faixa_etaria", None),
                        infantil_ou_fundamental=infantil_ou_fundamental,
                    ).delete()
                    ValorMedicao.objects.update_or_create(
                        medicao=instance,
                        dia=valor_medicao.get("dia", ""),
                        semana=semana,
                        nome_campo=valor_medicao.get("nome_campo", ""),
                        categoria_medicao=valor_medicao.get("categoria_medicao", ""),
                        tipo_alimentacao=valor_medicao.get("tipo_alimentacao", None),
                        faixa_etaria=valor_medicao.get("faixa_etaria", None),
                        infantil_ou_fundamental=infantil_ou_fundamental,
                        defaults={
                            "valor": valor_medicao.get("valor", ""),
                        },
                    )
        eh_observacao = self.context["request"].data.get(
            "eh_observacao",
        )
        if not eh_observacao:
            instance.valores_medicao.filter(valor=-1).delete()
        instance.alterado_em = datetime.now()
        instance.save()

        return instance

    class Meta:
        model = Medicao
        exclude = (
            "id",
            "criado_por",
        )


class PermissaoLancamentoEspecialCreateUpdateSerializer(serializers.ModelSerializer):
    escola = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Escola.objects.all()
    )
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=PeriodoEscolar.objects.all()
    )
    alimentacoes_lancamento_especial = serializers.SlugRelatedField(
        slug_field="uuid",
        required=True,
        queryset=AlimentacaoLancamentoEspecial.objects.all(),
        many=True,
    )
    diretoria_regional = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=DiretoriaRegional.objects.all()
    )
    criado_por = serializers.SlugRelatedField(
        slug_field="uuid", required=True, queryset=Usuario.objects.all()
    )

    def validate(self, attrs):
        data_inicial = attrs.get("data_inicial", None)
        data_final = attrs.get("data_final", None)
        if data_inicial and data_final and data_inicial > data_final:
            raise ValidationError("data inicial não pode ser maior que data final")

        return attrs

    class Meta:
        model = PermissaoLancamentoEspecial
        fields = "__all__"


class EmpenhoCreateUpdateSerializer(serializers.ModelSerializer):
    contrato = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Contrato.objects.all()
    )
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )

    class Meta:
        model = Empenho
        fields = "__all__"


class ClausulaDeDescontoCreateUpdateSerializer(serializers.ModelSerializer):
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )

    class Meta:
        model = ClausulaDeDesconto
        fields = "__all__"
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=("edital", "numero_clausula", "item_clausula"),
                message="Já existe uma cláusula cadastrada para este edital com o mesmo número e item de cláusula.",
            )
        ]


class ParametrizacaoFinanceiraTabelaValorWriteModelSerializer(
    serializers.ModelSerializer
):
    tipo_alimentacao = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=TipoAlimentacao.objects.all(),
    )
    faixa_etaria = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        allow_null=True,
        queryset=FaixaEtaria.objects.all(),
    )

    class Meta:
        model = ParametrizacaoFinanceiraTabelaValor
        fields = ["faixa_etaria", "tipo_alimentacao", "grupo", "valor_colunas"]

    def validate_valor_colunas(self, valor_colunas):
        valores = list(valor_colunas.values())
        if not (valores and all(valores)):
            raise serializers.ValidationError("Todos os campos devem ser preenchidos")
        return valor_colunas


class ParametrizacaoFinanceiraTabelaWriteModelSerializer(serializers.ModelSerializer):
    valores = ParametrizacaoFinanceiraTabelaValorWriteModelSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceiraTabela
        fields = ["nome", "valores"]


class ParametrizacaoFinanceiraWriteModelSerializer(serializers.ModelSerializer):
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )
    lote = serializers.SlugRelatedField(slug_field="uuid", queryset=Lote.objects.all())
    tipos_unidades = serializers.SlugRelatedField(
        slug_field="uuid", queryset=TipoUnidadeEscolar.objects.all(), many=True
    )
    tabelas = ParametrizacaoFinanceiraTabelaWriteModelSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceira
        fields = ["edital", "lote", "tipos_unidades", "legenda", "tabelas"]

    def validate(self, attrs):
        if self.instance:
            return attrs

        if ParametrizacaoFinanceira.objects.filter(
            edital=attrs["edital"],
            lote=attrs["lote"],
            tipos_unidades__in=attrs["tipos_unidades"],
        ).exists():
            raise ValidationError(
                "Já existe uma parametrização financeira para este edital, lote e tipos de unidades"
            )

        return attrs

    def create(self, validated_data):
        tabelas = validated_data.pop("tabelas")

        parametrizacao_financeira = super().create(validated_data)

        for tabela in tabelas:
            valores = tabela.pop("valores")

            _tabela = ParametrizacaoFinanceiraTabela.objects.create(
                **tabela,
                parametrizacao_financeira=parametrizacao_financeira,
            )

            ParametrizacaoFinanceiraTabelaValor.objects.bulk_create(
                [
                    ParametrizacaoFinanceiraTabelaValor(**valor, tabela=_tabela)
                    for valor in valores
                ]
            )

        return parametrizacao_financeira

    def update(self, instance, validated_data):
        tabelas = validated_data.pop("tabelas")

        instance = super().update(instance, validated_data)

        for tabela in tabelas:
            valores = tabela.pop("valores")

            _tabela, created = ParametrizacaoFinanceiraTabela.objects.get_or_create(
                **tabela, parametrizacao_financeira=instance
            )

            for valor in valores:
                tipo_alimentacao_id = (
                    valor.get("tipo_alimentacao").id
                    if valor.get("tipo_alimentacao")
                    else None
                )
                faixa_etaria_id = (
                    valor.get("faixa_etaria").id if valor.get("faixa_etaria") else None
                )

                ParametrizacaoFinanceiraTabelaValor.objects.update_or_create(
                    tabela=_tabela,
                    grupo=valor.get("grupo"),
                    tipo_alimentacao_id=tipo_alimentacao_id,
                    faixa_etaria_id=faixa_etaria_id,
                    defaults=valor,
                )

        return instance
