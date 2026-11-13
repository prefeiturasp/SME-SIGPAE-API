import calendar
import json
from collections import defaultdict
from datetime import date, datetime

import environ
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from src.dados_comuns.api.serializers import LogSolicitacoesUsuarioSerializer
from src.dados_comuns.constants import StringsValidationErrors
from src.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from src.dados_comuns.validators import deve_ter_extensao_xls_xlsx_pdf
from src.dieta_especial.solicitacao_dieta_especial.api.validators import (
    somente_digitos,
)
from src.dieta_especial.solicitacao_dieta_especial.models import ClassificacaoDieta
from src.eol_servico.utils import MENSAGEM_RF_NAO_LOCALIZADO, EOLServicoSGP
from src.escola.api.serializers_create import (
    AlunoPeriodoParcialCreateSerializer,
)
from src.escola.models import (
    Aluno,
    AlunoPeriodoParcial,
    DiretoriaRegional,
    Escola,
    FaixaEtaria,
    GrupoUnidadeEscolar,
    Lote,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)
from src.medicao_inicial.api.constants import CAMPOS_CONTROLADOS_PELO_FLUXO
from src.medicao_inicial.models import (
    AlimentacaoLancamentoEspecial,
    CategoriaMedicao,
    ClausulaDeDesconto,
    DescontoFinanceiro,
    DiaSobremesaDoce,
    GrupoMedicao,
    Medicao,
    MedicaoFinal,
    OcorrenciaMedicaoInicial,
    ParametrizacaoFinanceira,
    ParametrizacaoFinanceiraTabela,
    ParametrizacaoFinanceiraTabelaValor,
    PermissaoLancamentoEspecial,
    RelatorioFinanceiro,
    Responsavel,
    SolicitacaoMedicaoInicial,
    TipoContagemAlimentacao,
    TipoSobremesaDoce,
    TipoValorParametrizacaoFinanceira,
    ValorMedicao,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cei_cci_cips import (
    cria_valores_medicao_participantes_cei,
    cria_valores_medicao_participantes_dietas_autorizadas_cei,
    validate_lancamento_alimentacoes_medicao_recreio_cei,
    validate_lancamento_dietas_medicao_recreio_cei,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_cemei import (
    cria_valores_medicao_participantes_cemei,
    cria_valores_medicao_participantes_dietas_autorizadas_cemei,
    validate_lancamento_alimentacoes_medicao_recreio_cemei,
    validate_lancamento_dietas_medicao_recreio_cemei,
)
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_emef_emei_ceu_gesto_cieja import (
    cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao,
    cria_valores_medicao_participantes_emef_emei_cieja_ceugestao,
    validate_lancamento_alimentacoes_medicao_recreio,
    validate_lancamento_dietas_medicao_recreio,
)
from src.medicao_inicial.utils import process_anexos_from_request
from src.perfil.models import Usuario
from src.terceirizada.models import Edital

from ...cardapio.base.models import TipoAlimentacao
from ...dados_comuns.constants import (
    DIETA_ESPECIAL_TIPO_A,
    DIETA_ESPECIAL_TIPO_B,
    DIRETOR_UE,
    TIPOS_ALIMENTACAO,
    TIPOS_UNIDADE_ESCOLAR,
    PayloadVariaveis,
    StringsValoresMedicao,
)
from ...inclusao_alimentacao.models import InclusaoAlimentacaoContinua
from ..recreio_nas_ferias.models import (
    RecreioNasFerias,
    RecreioNasFeriasUnidadeParticipante,
)
from ..utils import (
    atualiza_alunos_periodo_parcial,
    log_alteracoes_escola_corrige_periodo,
    substitui_criador_system_por_usuario_real,
)
from ..validators import (
    get_filtro_inclusao_continua_ativa,
    get_filtro_quantidade_periodo_ativa,
    valida_medicoes_inexistentes_cei,
    valida_medicoes_inexistentes_emebs,
    valida_medicoes_inexistentes_escola_sem_alunos_regulares,
    validate_finalizacao_sem_lancamentos_escola_aberta,
    validate_lancamento_alimentacoes_escola_aberta,
    validate_lancamento_alimentacoes_inclusoes_escola_sem_alunos_regulares,
    validate_lancamento_alimentacoes_medicao,
    validate_lancamento_alimentacoes_medicao_cei,
    validate_lancamento_alimentacoes_medicao_emebs,
    validate_lancamento_dietas_cei,
    validate_lancamento_dietas_emebs,
    validate_lancamento_dietas_emef,
    validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares,
    validate_lancamento_inclusoes,
    validate_lancamento_inclusoes_cei,
    validate_lancamento_inclusoes_dietas_cei,
    validate_lancamento_inclusoes_dietas_emef_emebs,
    validate_lancamento_kit_lanche,
    validate_lanche_emergencial,
    validate_lanches_emergenciais_diarios,
    validate_medicao_cemei_cei,
    validate_medicao_cemei_emei,
    validate_medicao_cemei_programas_e_projetos,
    validate_solicitacoes_etec,
    validate_solicitacoes_etec_escola_sem_alunos_regulares,
    validate_solicitacoes_programas_e_projetos,
    validate_solicitacoes_programas_e_projetos_emebs,
    validate_solicitacoes_programas_e_projetos_escola_sem_alunos_regulares,
    validate_ultimo_dia_mes_letivo,
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
    tipo = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=TipoSobremesaDoce.objects.all(),
        required=True,
    )

    class Meta:
        model = DiaSobremesaDoce
        fields = ("tipo_unidades", "editais", "tipo")


class DiaSobremesaDoceCreateManySerializer(serializers.ModelSerializer):
    cadastros_calendario = CadastroSobremesaDoceCreateSerializer(
        many=True, required=True
    )

    def validate(self, attrs):
        tipos_por_combinacao = {}

        for cadastro in attrs["cadastros_calendario"]:
            tipo = cadastro["tipo"]
            for tipo_unidade in cadastro["tipo_unidades"]:
                for edital in cadastro["editais"]:
                    chave = (tipo_unidade.uuid, edital.uuid)
                    tipo_existente = tipos_por_combinacao.get(chave)
                    if tipo_existente and tipo_existente.uuid != tipo.uuid:
                        raise serializers.ValidationError(
                            "Não é possível realizar o cadastro. Já existe "
                            f"uma {tipo_existente.nome} cadastrada "
                            "para esta Data, Edital e Tipo de Unidade."
                        )
                    tipos_por_combinacao[chave] = tipo

        return attrs

    def create(self, validated_data):
        return self._save_dias_sobremesa(validated_data)

    def update(self, instance, validated_data):
        return self._save_dias_sobremesa(validated_data)

    def _save_dias_sobremesa(self, validated_data):
        DiaSobremesaDoce.objects.filter(data=validated_data["data"]).delete()
        dia_sobremesa_doce = None
        for cadastro in validated_data["cadastros_calendario"]:
            for tipo_unidade in cadastro["tipo_unidades"]:
                for edital in cadastro["editais"]:
                    if not DiaSobremesaDoce.objects.filter(
                        data=validated_data["data"],
                        tipo_unidade=tipo_unidade,
                        edital=edital,
                        tipo=cadastro["tipo"],
                    ):
                        dia_sobremesa_doce = DiaSobremesaDoce(
                            criado_por=self.context["request"].user,
                            data=validated_data["data"],
                            tipo_unidade=tipo_unidade,
                            edital=edital,
                            tipo=cadastro["tipo"],
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
    recreio_nas_ferias = serializers.SlugRelatedField(
        slug_field="uuid",
        required=False,
        queryset=RecreioNasFerias.objects.all(),
        allow_null=True,
        default=None,
    )
    descricao_metodo = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        escola = attrs.get("escola")
        recreio = attrs.get("recreio_nas_ferias")

        if recreio and escola:
            participacao = recreio.unidades_participantes.filter(
                unidade_educacional=escola
            ).first()

            if not participacao or not participacao.liberar_medicao:
                raise serializers.ValidationError(
                    {
                        "recreio_nas_ferias": "A medição não está liberada para esta escola"
                    }
                )

        return attrs

    def create(self, validated_data):
        validated_data["criado_por"] = self.context["request"].user
        responsaveis_dict = validated_data.pop("responsaveis", [])
        alunos_periodo_parcial = validated_data.pop("alunos_periodo_parcial", [])
        tipos_contagem_alimentacao = validated_data.pop(
            "tipos_contagem_alimentacao", []
        )

        escola = validated_data.pop("escola")
        mes = validated_data.pop("mes")
        ano = validated_data.pop("ano")
        recreio = validated_data.pop("recreio_nas_ferias", None)

        solicitacao, criado = SolicitacaoMedicaoInicial.objects.get_or_create(
            escola=escola,
            mes=mes,
            ano=ano,
            recreio_nas_ferias=recreio,
            defaults=validated_data,
        )

        if not criado:
            raise serializers.ValidationError(
                {
                    "detail": "Já existe uma solicitação de medição inicial para esta escola, mês e ano."
                }
            )

        solicitacao.tipos_contagem_alimentacao.set(tipos_contagem_alimentacao)
        for responsavel in responsaveis_dict:
            Responsavel.objects.create(
                solicitacao_medicao_inicial=solicitacao,
                nome=responsavel.get("nome", ""),
                rf=responsavel.get("rf", ""),
            )
        if alunos_periodo_parcial:
            escola_associada = escola
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
        lista_erros = validate_lanches_emergenciais_diarios(instance, lista_erros)
        lista_erros = validate_lancamento_alimentacoes_escola_aberta(
            instance, lista_erros
        )

        if lista_erros:
            raise serializers.ValidationError(lista_erros)

    def valida_finalizar_medicao_cemei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_cemei
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        lista_erros = validate_medicao_cemei_cei(instance, lista_erros)
        lista_erros = validate_medicao_cemei_programas_e_projetos(instance, lista_erros)
        lista_erros = validate_medicao_cemei_emei(instance, lista_erros)
        lista_erros = validate_lanches_emergenciais_diarios(instance, lista_erros)
        if lista_erros:
            raise serializers.ValidationError(lista_erros)

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

    def valida_finalizar_medicao_escola_sem_alunos_regulares(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola_possui_alunos_regulares = instance.escola.possui_alunos_regulares
        if (
            escola_possui_alunos_regulares
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = valida_medicoes_inexistentes_escola_sem_alunos_regulares(
            instance, lista_erros
        )
        lista_erros = (
            validate_lancamento_alimentacoes_inclusoes_escola_sem_alunos_regulares(
                instance, lista_erros
            )
        )
        lista_erros = validate_lancamento_dietas_inclusoes_escola_sem_alunos_regulares(
            instance, lista_erros
        )
        lista_erros = (
            validate_solicitacoes_programas_e_projetos_escola_sem_alunos_regulares(
                instance, lista_erros
            )
        )
        lista_erros = validate_solicitacoes_etec_escola_sem_alunos_regulares(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        lista_erros = validate_lanches_emergenciais_diarios(instance, lista_erros)
        lista_erros = validate_lancamento_alimentacoes_escola_aberta(
            instance, lista_erros
        )

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
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes(instance, lista_erros, True)
        lista_erros = validate_lancamento_dietas_emebs(instance, lista_erros)
        lista_erros = validate_lancamento_inclusoes_dietas_emef_emebs(
            instance, lista_erros, True
        )
        lista_erros = validate_solicitacoes_programas_e_projetos_emebs(
            instance, lista_erros
        )
        lista_erros = validate_lanches_emergenciais_diarios(instance, lista_erros)

        if lista_erros:
            raise serializers.ValidationError(lista_erros)

    def valida_finalizar_medicao_ultimo_dia_mes(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return

        lista_erros = []
        lista_erros = validate_ultimo_dia_mes_letivo(instance, lista_erros)

        if lista_erros:
            raise serializers.ValidationError(lista_erros)

    def cria_valores_medicao_logs_alunos_matriculados_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        categoria = CategoriaMedicao.objects.get(nome=CategoriaMedicao.ALIMENTACAO)
        dias = self._dias_do_mes(instance)
        periodos_escolares = list(
            escola.periodos_escolares(ano=instance.ano, mes=instance.mes).values_list(
                "nome", flat=True
            )
        )
        medicoes = self._medicoes_por_periodo(instance, periodos_escolares)
        existentes = self._valores_existentes_por_medicao(
            medicoes,
            categoria,
            StringsValoresMedicao.MATRICULADOS.value,
            dias,
        )
        logs_por_periodo_dia = self._logs_matriculados_por_periodo_e_dia(instance)

        valores_medicao_a_criar = []
        for dia in dias:
            for periodo_escolar in periodos_escolares:
                medicao = medicoes[periodo_escolar]
                if (medicao.id, dia) in existentes:
                    continue
                valores_medicao_a_criar.append(
                    ValorMedicao(
                        medicao=medicao,
                        categoria_medicao=categoria,
                        dia=dia,
                        nome_campo=StringsValoresMedicao.MATRICULADOS.value,
                        valor=logs_por_periodo_dia.get((periodo_escolar, int(dia)), 0),
                    )
                )

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    @staticmethod
    def _dias_do_mes(instance: SolicitacaoMedicaoInicial) -> list[str]:
        """Retorna os dias do mês da solicitação no formato ``DD``."""
        quantidade_dias_mes = calendar.monthrange(int(instance.ano), int(instance.mes))[
            1
        ]
        return [f"{dia:02d}" for dia in range(1, quantidade_dias_mes + 1)]

    def _medicoes_por_periodo(
        self, instance: SolicitacaoMedicaoInicial, periodos_escolares: list[str]
    ) -> dict:
        """Retorna (criando quando necessário) a medição de cada período."""
        medicoes = {}
        for nome_periodo in periodos_escolares:
            medicao, _ = Medicao.objects.get_or_create(
                solicitacao_medicao_inicial=instance,
                periodo_escolar=PeriodoEscolar.objects.get(nome=nome_periodo),
            )
            medicoes[nome_periodo] = medicao
        return medicoes

    @staticmethod
    def _valores_existentes_por_medicao(
        medicoes: dict,
        categoria: CategoriaMedicao,
        nome_campo: str,
        dias: list[str],
    ) -> set:
        """Retorna as chaves ``(medicao_id, dia)`` já lançadas."""
        return set(
            ValorMedicao.objects.filter(
                medicao__in=medicoes.values(),
                categoria_medicao=categoria,
                nome_campo=nome_campo,
                dia__in=dias,
            ).values_list("medicao_id", "dia")
        )

    @staticmethod
    def _logs_matriculados_por_periodo_e_dia(
        instance: SolicitacaoMedicaoInicial,
    ) -> dict:
        """Agrupa a quantidade de alunos do mês por período e dia.

        O dicionário preserva a ordenação padrão do modelo (mais recente
        primeiro), replicando o ``first()`` usado anteriormente.
        """
        logs = defaultdict(int)
        logs_do_mes = instance.escola.logs_alunos_matriculados_por_periodo.filter(
            criado_em__month=instance.mes,
            criado_em__year=instance.ano,
            tipo_turma="REGULAR",
        ).values_list("periodo_escolar__nome", "criado_em__day", "quantidade_alunos")
        for periodo_escolar, dia, quantidade in logs_do_mes:
            logs.setdefault((periodo_escolar, dia), quantidade)
        return logs

    def cria_valores_medicao_logs_alunos_matriculados_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        categoria = CategoriaMedicao.objects.get(nome=CategoriaMedicao.ALIMENTACAO)
        dias = self._dias_do_mes(instance)
        periodos_escolares = list(
            escola.periodos_escolares(ano=instance.ano, mes=instance.mes).values_list(
                "nome", flat=True
            )
        )
        if instance.ue_possui_alunos_periodo_parcial:
            periodos_escolares.append("PARCIAL")

        medicoes = self._medicoes_por_periodo(instance, periodos_escolares)
        existentes = self._valores_existentes_por_medicao_faixa(
            medicoes, categoria, StringsValoresMedicao.MATRICULADOS.value, dias
        )
        logs_do_mes = escola.logs_alunos_matriculados_por_faixa_etaria.filter(
            data__month=instance.mes,
            data__year=instance.ano,
        ).values_list(
            "periodo_escolar__nome",
            "data__day",
            "faixa_etaria_id",
            "quantidade",
        )

        valores_medicao_a_criar = []
        for periodo_escolar, dia, faixa_etaria_id, quantidade in logs_do_mes:
            medicao = medicoes.get(periodo_escolar)
            if not medicao:
                continue
            dia_formatado = f"{dia:02d}"
            if (medicao.id, dia_formatado, faixa_etaria_id) in existentes:
                continue
            valores_medicao_a_criar.append(
                ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=dia_formatado,
                    nome_campo=StringsValoresMedicao.MATRICULADOS.value,
                    valor=quantidade,
                    faixa_etaria_id=faixa_etaria_id,
                )
            )

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    @staticmethod
    def _valores_existentes_por_medicao_faixa(
        medicoes: dict,
        categoria: CategoriaMedicao,
        nome_campo: str,
        dias: list[str],
    ) -> set:
        """Retorna as chaves ``(medicao_id, dia, faixa_etaria_id)`` existentes."""
        return set(
            ValorMedicao.objects.filter(
                medicao__in=medicoes.values(),
                categoria_medicao=categoria,
                nome_campo=nome_campo,
                dia__in=dias,
            ).values_list("medicao_id", "dia", "faixa_etaria_id")
        )

    @staticmethod
    def _medicoes_existentes_por_periodo(
        instance: SolicitacaoMedicaoInicial, periodos_escolares: list[str]
    ) -> dict:
        """Retorna a medição já existente de cada período informado."""
        return {
            nome_periodo: instance.medicoes.get(periodo_escolar__nome=nome_periodo)
            for nome_periodo in periodos_escolares
        }

    @staticmethod
    def _valores_existentes_por_medicao_categoria(
        medicoes: dict,
        categorias: list[CategoriaMedicao],
        nome_campo: str,
        dias: list[str],
    ) -> set:
        """Retorna as chaves ``(medicao_id, categoria_id, dia)`` existentes."""
        return set(
            ValorMedicao.objects.filter(
                medicao__in=medicoes.values(),
                categoria_medicao__in=categorias,
                nome_campo=nome_campo,
                dia__in=dias,
            ).values_list("medicao_id", "categoria_medicao_id", "dia")
        )

    @staticmethod
    def _valores_existentes_por_medicao_categoria_faixa(
        medicoes: dict,
        categorias: list[CategoriaMedicao],
        nome_campo: str,
        dias: list[str],
    ) -> set:
        """Retorna as chaves ``(medicao_id, categoria_id, dia, faixa_id)``."""
        return set(
            ValorMedicao.objects.filter(
                medicao__in=medicoes.values(),
                categoria_medicao__in=categorias,
                nome_campo=nome_campo,
                dia__in=dias,
            ).values_list(
                "medicao_id", "categoria_medicao_id", "dia", "faixa_etaria_id"
            )
        )

    @staticmethod
    def _logs_dietas_autorizadas_por_periodo_e_dia(
        logs_do_mes: QuerySet,
    ) -> tuple:
        """Agrupa os logs de dietas por período e por ``(período, dia)``."""
        por_periodo = defaultdict(list)
        por_periodo_e_dia = defaultdict(list)
        itens = logs_do_mes.values_list(
            "periodo_escolar__nome", "data__day", "classificacao__nome", "quantidade"
        )
        for periodo_escolar, dia, classificacao, quantidade in itens:
            item = (classificacao, quantidade)
            por_periodo[periodo_escolar].append(item)
            por_periodo_e_dia[(periodo_escolar, dia)].append(item)
        return por_periodo, por_periodo_e_dia

    @staticmethod
    def _logs_dietas_autorizadas_cei_por_periodo_e_dia(
        logs_do_mes: QuerySet,
    ) -> tuple:
        """Agrupa os logs CEI por período e por ``(período, dia)``."""
        por_periodo = defaultdict(list)
        por_periodo_e_dia = defaultdict(list)
        itens = logs_do_mes.values_list(
            "periodo_escolar__nome",
            "data__day",
            "classificacao__nome",
            "faixa_etaria_id",
            "quantidade",
        )
        for periodo_escolar, dia, classificacao, faixa_etaria_id, quantidade in itens:
            item = (classificacao, faixa_etaria_id, quantidade)
            por_periodo[periodo_escolar].append(item)
            por_periodo_e_dia[(periodo_escolar, dia)].append(item)
        return por_periodo, por_periodo_e_dia

    @staticmethod
    def _classificacao_corresponde_a_categoria(
        classificacao: str, categoria: CategoriaMedicao
    ) -> bool:
        """Replica o filtro de classificação usado para detectar lançamentos."""
        nome_classificacao = classificacao.lower()
        tipo_dieta = categoria.nome.split(" - ")[1].lower()
        return (
            tipo_dieta in nome_classificacao
            and ClassificacaoDieta.CLASSIFICACAO_CONTEM_ENTERAL.lower()
            not in nome_classificacao
            and ClassificacaoDieta.CLASSIFICACAO_CONTEM_AMINOACIDOS.lower()
            not in nome_classificacao
        )

    def _possui_log_positivo(
        self, categoria: CategoriaMedicao, logs_do_periodo: list
    ) -> bool:
        """Indica se o período possui algum log com quantidade positiva.

        A quantidade é o último item da tupla, pois os logs de EMEF/EMEI não
        possuem faixa etária e os do CEI possuem.
        """
        logs_com_quantidade = [
            (log[0], log[-1]) for log in logs_do_periodo if log[-1] > 0
        ]
        if (
            categoria.nome
            == CategoriaMedicao.DIETA_ESPECIAL_TIPO_A_ENTERAL_RESTRICAO_AMINOACIDOS
        ):
            classificacoes = {
                ClassificacaoDieta.TIPO_A_ENTERAL,
                ClassificacaoDieta.TIPO_A_RESTRICAO_AMINOACIDOS,
            }
            return any(
                classificacao in classificacoes
                for classificacao, _ in logs_com_quantidade
            )
        return any(
            self._classificacao_corresponde_a_categoria(classificacao, categoria)
            for classificacao, _ in logs_com_quantidade
        )

    def _valor_log_dieta_autorizada(
        self, categoria: CategoriaMedicao, logs_do_dia: list
    ) -> int:
        """Calcula o valor do dia a partir dos logs de dietas autorizadas."""
        if (
            categoria.nome
            == CategoriaMedicao.DIETA_ESPECIAL_TIPO_A_ENTERAL_RESTRICAO_AMINOACIDOS
        ):
            return self._primeira_quantidade_por_classificacao(
                logs_do_dia, ClassificacaoDieta.CLASSIFICACAO_CONTEM_ENTERAL
            ) + self._primeira_quantidade_por_classificacao(
                logs_do_dia, ClassificacaoDieta.CLASSIFICACAO_CONTEM_AMINOACIDOS
            )
        return self._primeira_quantidade_da_categoria(categoria, logs_do_dia)

    @staticmethod
    def _primeira_quantidade_por_classificacao(
        logs_do_dia: list, termo_classificacao: str
    ) -> int:
        """Retorna a quantidade do primeiro log cuja classificação contém o termo."""
        termo_classificacao = termo_classificacao.lower()
        for classificacao, quantidade in logs_do_dia:
            if termo_classificacao in classificacao.lower():
                return quantidade
        return 0

    def _primeira_quantidade_da_categoria(
        self, categoria: CategoriaMedicao, logs_do_dia: list
    ) -> int:
        """Retorna a quantidade do primeiro log correspondente à categoria."""
        for classificacao, quantidade in logs_do_dia:
            if self._classificacao_corresponde_a_categoria(classificacao, categoria):
                return quantidade
        return 0

    def cria_valores_medicao_logs_dietas_autorizadas_emef_emei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        dias = self._dias_do_mes(instance)
        categorias = list(CategoriaMedicao.objects.filter(nome__icontains="dieta"))
        periodos_escolares = list(
            escola.periodos_escolares(ano=instance.ano, mes=instance.mes).values_list(
                "nome", flat=True
            )
        )
        medicoes = self._medicoes_existentes_por_periodo(instance, periodos_escolares)
        existentes = self._valores_existentes_por_medicao_categoria(
            medicoes, categorias, StringsValoresMedicao.DIETAS_AUTORIZADAS.value, dias
        )
        logs_por_periodo, logs_por_periodo_e_dia = (
            self._logs_dietas_autorizadas_por_periodo_e_dia(
                escola.logs_dietas_autorizadas.filter(
                    data__month=instance.mes, data__year=instance.ano
                )
            )
        )

        valores_medicao_a_criar = []
        for dia in dias:
            for categoria in categorias:
                for periodo_escolar in periodos_escolares:
                    medicao = medicoes[periodo_escolar]
                    if not self._possui_log_positivo(
                        categoria, logs_por_periodo[periodo_escolar]
                    ):
                        continue
                    if (medicao.id, categoria.id, dia) in existentes:
                        continue
                    valores_medicao_a_criar.append(
                        ValorMedicao(
                            medicao=medicao,
                            categoria_medicao=categoria,
                            dia=dia,
                            nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
                            valor=self._valor_log_dieta_autorizada(
                                categoria,
                                logs_por_periodo_e_dia[(periodo_escolar, int(dia))],
                            ),
                        )
                    )

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    @staticmethod
    def _logs_filtrados_dietas_cei(
        categoria: CategoriaMedicao, logs_do_dia: list
    ) -> list:
        """Replica o filtro de logs de dietas autorizadas do CEI."""
        if categoria.nome == DIETA_ESPECIAL_TIPO_A:
            return [
                log
                for log in logs_do_dia
                if SolicitacaoMedicaoInicialCreateSerializer._classificacao_contem_tipo_a(
                    log[0]
                )
            ]
        return [
            log
            for log in logs_do_dia
            if SolicitacaoMedicaoInicialCreateSerializer._log_corresponde_dieta_cei(
                categoria, log[0]
            )
        ]

    @staticmethod
    def _classificacao_contem_tipo_a(classificacao: str) -> bool:
        return (
            ClassificacaoDieta.CLASSIFICACAO_CONTEM_TIPO_A.lower()
            in classificacao.lower()
        )

    @staticmethod
    def _log_corresponde_dieta_cei(
        categoria: CategoriaMedicao, classificacao: str
    ) -> bool:
        tipo_dieta = categoria.nome.split(" - ")[1].lower()
        nome_classificacao = classificacao.lower()
        return (
            tipo_dieta in nome_classificacao
            and ClassificacaoDieta.CLASSIFICACAO_CONTEM_TIPO_A.lower()
            not in nome_classificacao
        )

    @staticmethod
    def _somas_por_faixa_etaria(logs_do_dia: list) -> dict:
        """Soma as quantidades dos logs agrupando por faixa etária."""
        somas = defaultdict(int)
        for _, faixa_etaria_id, quantidade in logs_do_dia:
            somas[faixa_etaria_id] += quantidade
        return somas

    @staticmethod
    def _valor_dieta_cei(
        eh_tipo_a: bool, somas_por_faixa: dict, faixa_etaria_id: int, quantidade: int
    ) -> int:
        """Retorna o valor do log, somando o tipo A por faixa etária."""
        if eh_tipo_a:
            return somas_por_faixa[faixa_etaria_id]
        return quantidade

    def _cria_valores_dieta_cei_do_periodo(
        self,
        dia: str,
        categoria: CategoriaMedicao,
        periodo_escolar: str,
        medicoes: dict,
        logs_por_periodo_e_dia: dict,
        existentes: set,
        adicionados_tipo_a: set,
    ) -> list:
        """Cria os valores de dietas do CEI de um período em um dia."""
        medicao = medicoes[periodo_escolar]
        logs_do_dia = self._logs_filtrados_dietas_cei(
            categoria, logs_por_periodo_e_dia[(periodo_escolar, int(dia))]
        )
        eh_tipo_a = categoria.nome == DIETA_ESPECIAL_TIPO_A
        somas_por_faixa = self._somas_por_faixa_etaria(logs_do_dia)
        nome_periodo_grupo = medicao.nome_periodo_grupo

        valores_medicao_a_criar = []
        for _, faixa_etaria_id, quantidade in logs_do_dia:
            if (medicao.id, categoria.id, dia, faixa_etaria_id) in existentes:
                continue
            chave_pendente = (
                categoria.id,
                nome_periodo_grupo,
                faixa_etaria_id,
                dia,
            )
            if eh_tipo_a and chave_pendente in adicionados_tipo_a:
                continue
            if eh_tipo_a:
                adicionados_tipo_a.add(chave_pendente)
            valores_medicao_a_criar.append(
                ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=dia,
                    nome_campo=StringsValoresMedicao.DIETAS_AUTORIZADAS.value,
                    valor=self._valor_dieta_cei(
                        eh_tipo_a, somas_por_faixa, faixa_etaria_id, quantidade
                    ),
                    faixa_etaria_id=faixa_etaria_id,
                )
            )
        return valores_medicao_a_criar

    def _cria_valores_dieta_cei_da_categoria(
        self,
        dia: str,
        categoria: CategoriaMedicao,
        periodos_escolares: list[str],
        medicoes: dict,
        logs_por_periodo: dict,
        logs_por_periodo_e_dia: dict,
        existentes: set,
        adicionados_tipo_a: set,
    ) -> list:
        """Cria os valores de dietas do CEI de uma categoria em um dia."""
        valores_medicao_a_criar = []
        for periodo_escolar in periodos_escolares:
            if not self._possui_log_positivo(
                categoria, logs_por_periodo[periodo_escolar]
            ):
                continue
            valores_medicao_a_criar.extend(
                self._cria_valores_dieta_cei_do_periodo(
                    dia,
                    categoria,
                    periodo_escolar,
                    medicoes,
                    logs_por_periodo_e_dia,
                    existentes,
                    adicionados_tipo_a,
                )
            )
        return valores_medicao_a_criar

    def cria_valores_medicao_logs_dietas_autorizadas_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        escola = instance.escola
        dias = self._dias_do_mes(instance)
        categorias = list(
            CategoriaMedicao.objects.filter(
                nome__in=[DIETA_ESPECIAL_TIPO_A, DIETA_ESPECIAL_TIPO_B]
            )
        )
        periodos_escolares = list(
            escola.periodos_escolares(ano=instance.ano, mes=instance.mes).values_list(
                "nome", flat=True
            )
        )
        if instance.ue_possui_alunos_periodo_parcial:
            periodos_escolares.append("PARCIAL")

        medicoes = self._medicoes_existentes_por_periodo(instance, periodos_escolares)
        existentes = self._valores_existentes_por_medicao_categoria_faixa(
            medicoes, categorias, StringsValoresMedicao.DIETAS_AUTORIZADAS.value, dias
        )
        logs_por_periodo, logs_por_periodo_e_dia = (
            self._logs_dietas_autorizadas_cei_por_periodo_e_dia(
                escola.logs_dietas_autorizadas_cei.filter(
                    data__month=instance.mes,
                    data__year=instance.ano,
                    faixa_etaria__isnull=False,
                )
            )
        )

        valores_medicao_a_criar = []
        adicionados_tipo_a = set()
        for dia in dias:
            for categoria in categorias:
                valores_medicao_a_criar.extend(
                    self._cria_valores_dieta_cei_da_categoria(
                        dia,
                        categoria,
                        periodos_escolares,
                        medicoes,
                        logs_por_periodo,
                        logs_por_periodo_e_dia,
                        existentes,
                        adicionados_tipo_a,
                    )
                )

        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def retorna_medicao_por_nome_grupo(
        self, instance: SolicitacaoMedicaoInicial, nome_grupo: str
    ) -> Medicao:
        return instance.get_or_create_medicao_por_periodo_e_ou_grupo(nome_grupo)

    def retorna_numero_alunos_dia(
        self, inclusao: InclusaoAlimentacaoContinua, data: date
    ) -> int:
        dia_semana = data.weekday()
        numero_alunos = 0
        for quantidade_periodo in inclusao.quantidades_periodo.filter(
            get_filtro_quantidade_periodo_ativa(data),
            dias_semana__icontains=dia_semana,
            cancelado=False,
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
        inclusoes_do_motivo = inclusoes_continuas.filter(
            motivo__nome__icontains=nome_motivo
        )
        if not inclusoes_do_motivo.exists():
            return
        valores_por_dia = self._valores_numero_alunos_inclusoes_continuas_por_dia(
            instance, inclusoes_do_motivo, quantidade_dias_mes
        )
        if not valores_por_dia:
            return
        categoria = CategoriaMedicao.objects.get(nome=CategoriaMedicao.ALIMENTACAO)
        medicao = self.retorna_medicao_por_nome_grupo(instance, nome_grupo)
        dias = [f"{dia:02d}" for dia in valores_por_dia]
        existentes = set(
            medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                nome_campo=StringsValoresMedicao.NUMERO_DE_ALUNOS.value,
                dia__in=dias,
            ).values_list("dia", flat=True)
        )
        valores_medicao_a_criar = []
        for dia, numero_alunos in valores_por_dia.items():
            if f"{dia:02d}" in existentes:
                continue
            valores_medicao_a_criar = self.cria_valor_medicao(
                numero_alunos,
                medicao,
                categoria,
                dia,
                StringsValoresMedicao.NUMERO_DE_ALUNOS.value,
                valores_medicao_a_criar,
            )
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    def _valores_numero_alunos_inclusoes_continuas_por_dia(
        self,
        instance: SolicitacaoMedicaoInicial,
        inclusoes_do_motivo: QuerySet,
        quantidade_dias_mes: int,
    ) -> dict:
        inclusoes = list(inclusoes_do_motivo.prefetch_related("quantidades_periodo"))
        valores_por_dia = {}
        for dia in range(1, quantidade_dias_mes + 1):
            data = date(year=int(instance.ano), month=int(instance.mes), day=dia)
            numero_alunos = self._numero_alunos_do_dia(inclusoes, data)
            if numero_alunos > 0:
                valores_por_dia[dia] = numero_alunos
        return valores_por_dia

    def _numero_alunos_do_dia(
        self, inclusoes: list[InclusaoAlimentacaoContinua], data: date
    ) -> int:
        """Soma os alunos das inclusões contínuas ativas na data informada."""
        dia_semana = data.weekday()
        numero_alunos = 0
        for inclusao in inclusoes:
            if not (inclusao.data_inicial <= data <= inclusao.data_final):
                continue
            numero_alunos += self._soma_quantidades_ativas(inclusao, data, dia_semana)
        return numero_alunos

    @staticmethod
    def _soma_quantidades_ativas(
        inclusao: InclusaoAlimentacaoContinua, data: date, dia_semana: int
    ) -> int:
        numero_alunos = 0
        for quantidade_periodo in inclusao.quantidades_periodo.all():
            if not SolicitacaoMedicaoInicialCreateSerializer._quantidade_periodo_ativa(
                quantidade_periodo, data, dia_semana
            ):
                continue
            numero_alunos += quantidade_periodo.numero_alunos
        return numero_alunos

    @staticmethod
    def _quantidade_periodo_ativa(
        quantidade_periodo, data: date, dia_semana: int
    ) -> bool:
        """Replica em memória o filtro de quantidade por período ativa."""
        if quantidade_periodo.cancelado:
            return False
        if dia_semana not in (quantidade_periodo.dias_semana or []):
            return False
        return (
            quantidade_periodo.encerrado_a_partir_de is None
            or quantidade_periodo.encerrado_a_partir_de >= data
        )

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
        inclusoes_continuas = (
            escola.inclusoes_alimentacao_continua.filter(
                status="CODAE_AUTORIZADO",
                data_inicial__lte=ultimo_dia_mes,
            )
            .filter(get_filtro_inclusao_continua_ativa(primeiro_dia_mes))
            .distinct()
        )
        if not inclusoes_continuas.count():
            return
        self.cria_valores_medicao_logs_numero_alunos_inclusoes_continuas(
            instance,
            inclusoes_continuas,
            quantidade_dias_mes,
            "Programas/Projetos",
            GrupoMedicao.PROGRAMAS_E_PROJETOS,
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

    def cria_valores_medicao_kit_lanches_emef_emei_escola_sem_alunos_regulares(
        self, instance, kits_lanche, kits_lanche_unificado
    ):
        medicao = self.retorna_medicao_por_nome_grupo(
            instance, GrupoMedicao.SOLICITACOES_DE_ALIMENTACAO
        )
        categoria = CategoriaMedicao.objects.get(
            nome=CategoriaMedicao.SOLICITACOES_DE_ALIMENTACAO
        )
        dias = self._dias_do_mes(instance)
        existentes = set(
            medicao.valores_medicao.filter(
                categoria_medicao=categoria,
                nome_campo=StringsValoresMedicao.KIT_LANCHE.value,
                dia__in=dias,
            ).values_list("dia", flat=True)
        )
        totais_por_dia = self._totais_kit_lanche_por_dia(
            kits_lanche, kits_lanche_unificado
        )

        valores_medicao_a_criar = []
        for dia in dias:
            total_dia = totais_por_dia.get(int(dia), 0)
            if dia in existentes or total_dia <= 0:
                continue
            valores_medicao_a_criar.append(
                ValorMedicao(
                    medicao=medicao,
                    categoria_medicao=categoria,
                    dia=dia,
                    nome_campo=StringsValoresMedicao.KIT_LANCHE.value,
                    valor=total_dia,
                )
            )
        ValorMedicao.objects.bulk_create(valores_medicao_a_criar)

    @staticmethod
    def _totais_kit_lanche_por_dia(
        kits_lanche: QuerySet, kits_lanche_unificado: QuerySet
    ) -> dict:
        """Totaliza os kits lanche (avulsos e unificados) por dia do mês."""
        totais_por_dia = defaultdict(int)
        kits_avulsos = kits_lanche.prefetch_related("solicitacao_kit_lanche__kits")
        for kit_lanche in kits_avulsos:
            totais_por_dia[
                kit_lanche.solicitacao_kit_lanche.data.day
            ] += kit_lanche.quantidade_alimentacoes
        for kit_lanche in kits_lanche_unificado.prefetch_related("kits"):
            data = kit_lanche.solicitacao_unificada.solicitacao_kit_lanche.data
            totais_por_dia[data.day] += kit_lanche.total_kit_lanche
        return totais_por_dia

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
            motivo__nome=TIPOS_ALIMENTACAO.LANCHE_EMERGENCIAL.value,
            status="CODAE_AUTORIZADO",
            datas_intervalo__data__month=instance.mes,
            datas_intervalo__data__year=instance.ano,
            datas_intervalo__cancelado=False,
        )

        mes = int(instance.mes)
        ano = int(instance.ano)
        inicio_mes = date(ano, mes, 1)
        fim_mes = date(ano, mes, calendar.monthrange(ano, mes)[1])

        periodos_recreio = RecreioNasFeriasUnidadeParticipante.objects.filter(
            unidade_educacional=instance.escola,
            liberar_medicao=True,
            recreio_nas_ferias__data_inicio__lte=fim_mes,
            recreio_nas_ferias__data_fim__gte=inicio_mes,
        ).values_list(
            "recreio_nas_ferias__data_inicio",
            "recreio_nas_ferias__data_fim",
        )

        if periodos_recreio:
            filtro_kit = Q()
            filtro_unificado = Q()
            filtro_lanche = Q()
            for data_inicio, data_fim in periodos_recreio:
                filtro_kit &= Q(solicitacao_kit_lanche__data__lt=data_inicio) | Q(
                    solicitacao_kit_lanche__data__gt=data_fim
                )
                filtro_unificado &= Q(
                    solicitacao_unificada__solicitacao_kit_lanche__data__lt=data_inicio
                ) | Q(solicitacao_unificada__solicitacao_kit_lanche__data__gt=data_fim)
                filtro_lanche &= Q(datas_intervalo__data__lt=data_inicio) | Q(
                    datas_intervalo__data__gt=data_fim
                )

            kits_lanche = kits_lanche.filter(filtro_kit)
            kits_lanche_unificado = kits_lanche_unificado.filter(filtro_unificado)
            lanches_emergenciais = lanches_emergenciais.filter(filtro_lanche)

        if (
            not kits_lanche.exists()
            and not kits_lanche_unificado.exists()
            and not lanches_emergenciais.exists()
        ):
            return

        self.cria_valores_medicao_kit_lanches_emef_emei_escola_sem_alunos_regulares(
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
        instance.save(update_fields=["logs_salvos"])

    def cria_valores_medicao_logs_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if not instance.escola.eh_cei or instance.logs_salvos:
            return

        self.cria_valores_medicao_logs_alunos_matriculados_cei(instance)
        self.cria_valores_medicao_logs_dietas_autorizadas_cei(instance)

        instance.logs_salvos = True
        instance.save(update_fields=["logs_salvos"])

    def update(self, instance, validated_data):
        self._check_user_permission()
        usuario = self.context["request"].user
        substitui_criador_system_por_usuario_real(instance, usuario)
        justificativa_sem_lancamentos = validated_data.pop(
            "justificativa_sem_lancamentos", None
        )
        validated_data.pop("alunos_periodo_parcial", None)
        self._update_instance_fields(instance, validated_data)
        self._update_responsaveis(instance)
        self._update_alunos(instance, validated_data)
        self._update_tipos_contagem_alimentacao(instance)
        self._finaliza_medicao_se_necessario(
            instance, validated_data, justificativa_sem_lancamentos
        )
        self._finaliza_medicao_sem_lancamentos(instance, justificativa_sem_lancamentos)
        self._finaliza_recreio_nas_ferias(instance, validated_data)
        return instance

    def _check_user_permission(self):
        vinculo_usuario = self.context["request"].user.vinculo_atual
        eh_escola = isinstance(vinculo_usuario.instituicao, Escola)
        eh_diretor = vinculo_usuario.perfil.nome == DIRETOR_UE
        escola_possui_alunos_regulares = (
            eh_escola and vinculo_usuario.instituicao.possui_alunos_regulares
        )
        escola_p_fom = eh_escola and vinculo_usuario.instituicao.eh_p_fom
        if (
            eh_escola
            and not eh_diretor
            and escola_possui_alunos_regulares
            and not escola_p_fom
        ):
            raise PermissionDenied(StringsValidationErrors.PERMISSAO_NEGADA.value)

    def _update_instance_fields(self, instance, validated_data):
        if "dre_ciencia_correcao_data" in validated_data:
            validated_data["dre_ciencia_correcao_usuario"] = self.context[
                "request"
            ].user
        update_instance_from_dict(instance, validated_data)
        update_fields = self._campos_para_atualizacao(instance, validated_data)
        if update_fields:
            instance.save(update_fields=update_fields)

    @staticmethod
    def _campos_para_atualizacao(instance, validated_data):
        """Lista os campos que um salvamento comum pode gravar.

        Campos controlados pelo fluxo de aprovação (``status``) são ignorados,
        pois uma instância carregada antes de uma transição concorrente
        sobrescreveria o novo status com o valor antigo.

        Args:
            instance (SolicitacaoMedicaoInicial): Instância em atualização.
            validated_data (dict): Campos recebidos na requisição.

        Returns:
            list[str]: Nomes dos campos concretos que devem ser persistidos.
        """
        update_fields = []
        for nome in validated_data:
            try:
                campo = instance._meta.get_field(nome)
            except FieldDoesNotExist:
                continue
            if not campo.concrete or campo.primary_key:
                continue
            if nome in CAMPOS_CONTROLADOS_PELO_FLUXO:
                continue
            update_fields.append(nome)
        return update_fields

    def _update_responsaveis(self, instance):
        responsaveis_dict = self.context["request"].data.get("responsaveis")
        if responsaveis_dict:
            instance.responsaveis.all().delete()
            if isinstance(responsaveis_dict, str):
                responsaveis_dict = json.loads(responsaveis_dict)
            for responsavel_data in responsaveis_dict:
                Responsavel.objects.create(
                    solicitacao_medicao_inicial=instance, **responsavel_data
                )

    def _update_alunos(self, instance, validated_data):
        alunos_periodo_parcial = self.context["request"].data.get(
            "alunos_periodo_parcial"
        )
        if alunos_periodo_parcial:
            escola_associada = validated_data.get("escola")
            if isinstance(alunos_periodo_parcial, str):
                alunos_periodo_parcial = json.loads(alunos_periodo_parcial)

            if self.context["request"].data.get("alunos_parcial_alterado") in [
                "true",
                True,
            ]:
                atualiza_alunos_periodo_parcial(instance, alunos_periodo_parcial)
            instance.alunos_periodo_parcial.all().delete()
            for aluno in alunos_periodo_parcial:
                dia, mes, ano = aluno.get("data", "").split("/")
                dia = int(dia)
                mes = int(mes)
                ano = int(ano)
                if aluno.get("data_removido", ""):
                    dia_, mes_, ano_ = aluno.get("data_removido", "").split("/")
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
        if (
            PayloadVariaveis.TIPOS_CONTAGEM_ALIMENTACAO.value
            in self.context["request"].data
        ):
            return self.context["request"].data.getlist(
                PayloadVariaveis.TIPOS_CONTAGEM_ALIMENTACAO.value
            )
        return self.context["request"].data.get("tipos_contagem_alimentacao")

    def _process_anexos(self, instance):
        anexos_processados = process_anexos_from_request(self.context["request"])
        for anexo in anexos_processados:
            if ".pdf" in anexo.get("nome", "").lower():
                arquivo_final = convert_base64_to_contentfile(anexo["base64"])
                OcorrenciaMedicaoInicial.objects.update_or_create(
                    solicitacao_medicao_inicial=instance,
                    defaults={
                        "ultimo_arquivo": arquivo_final,
                        "nome_ultimo_arquivo": anexo.get("nome"),
                    },
                )
        return anexos_processados

    def _finaliza_medicao_se_necessario(
        self, instance, validated_data, justificativa_sem_lancamentos
    ):
        if justificativa_sem_lancamentos or instance.recreio_nas_ferias:
            return
        key_com_ocorrencias = validated_data.get("com_ocorrencias", None)
        if key_com_ocorrencias is not None and self.context["request"].data.get(
            "finaliza_medicao"
        ):
            self.cria_valores_medicao_logs_emef_emei(instance)
            self.cria_valores_medicao_logs_cei(instance)
            self.valida_finalizar_medicao_ultimo_dia_mes(instance)
            self.valida_finalizar_medicao_emef_emei(instance)
            self.valida_finalizar_medicao_cemei(instance)
            self.valida_finalizar_medicao_cei(instance)
            self.valida_finalizar_medicao_escola_sem_alunos_regulares(instance)
            self.valida_finalizar_medicao_emebs(instance)
            instance.ue_envia(user=self.context["request"].user)
            anexos = self._process_anexos(instance)
            if hasattr(instance, "ocorrencia"):
                instance.ocorrencia.ue_envia(
                    user=self.context["request"].user, anexos=anexos
                )
            for medicao in instance.medicoes.all():
                medicao.ue_envia(user=self.context["request"].user)

    def _checa_se_medicao_possui_algum_lancamento(
        self, instance: SolicitacaoMedicaoInicial, lista_erros: list[dict]
    ) -> list:
        medicoes_instancias_nomes = instance.medicoes.values_list(
            "periodo_escolar__nome", "grupo__nome"
        )
        nomes_normalizados = list(
            {nome for tupla in medicoes_instancias_nomes for nome in tupla if nome}
        )
        for medicao_nome in nomes_normalizados:
            medicao = instance.get_medicao_por_periodo_e_ou_grupo(medicao_nome)
            if not medicao:
                continue
            if medicao.possui_algum_lancamento():
                lista_erros.append(
                    {
                        "periodo_escolar": medicao_nome,
                        "erro": "Existem lançamentos no período. "
                        "Não é possível finalizar sem lançamentos.",
                    }
                )
        return lista_erros

    def _checa_se_pode_finalizar_sem_lancamentos(self, instance) -> None:
        medicoes_nomes_com_solicitacoes_autorizadas = (
            instance.escola.get_lista_medicoes_solicitacoes_autorizadas_no_mes(
                int(instance.mes), int(instance.ano)
            )
        )
        lista_erros = []
        lista_erros = self._checa_se_medicao_possui_algum_lancamento(
            instance, lista_erros
        )
        lista_erros = validate_finalizacao_sem_lancamentos_escola_aberta(
            instance, lista_erros
        )

        if not medicoes_nomes_com_solicitacoes_autorizadas and not lista_erros:
            return
        for medicao_nome in medicoes_nomes_com_solicitacoes_autorizadas:
            medicao = instance.get_or_create_medicao_por_periodo_e_ou_grupo(
                medicao_nome
            )
            if medicao_nome in [GrupoMedicao.PROGRAMAS_E_PROJETOS, "ETEC"]:
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

    def _finaliza_medicao_sem_lancamentos(
        self, instance, justificativa_sem_lancamentos
    ):
        if not justificativa_sem_lancamentos or instance.recreio_nas_ferias:
            return
        usuario = self.context["request"].user
        self._checa_se_pode_finalizar_sem_lancamentos(instance)
        instance.cria_medicoes_dos_periodos()
        instance.ue_envia_sem_lancamentos(
            user=usuario,
            justificativa_sem_lancamentos=justificativa_sem_lancamentos,
        )
        for medicao in instance.medicoes.all():
            medicao.medicao_sem_lancamentos(
                user=usuario,
                justificativa_sem_lancamentos=justificativa_sem_lancamentos,
            )

    def _finaliza_recreio_nas_ferias(self, instance, validated_data):
        if not instance.recreio_nas_ferias:
            return
        key_com_ocorrencias = validated_data.get("com_ocorrencias", None)
        if key_com_ocorrencias is not None and self.context["request"].data.get(
            "finaliza_medicao"
        ):
            if date.today() <= instance.recreio_nas_ferias.data_fim:
                raise serializers.ValidationError(
                    "A medição só pode ser finalizada 1 dia após a data fim do Recreio nas Férias."
                )
            self.cria_valores_medicao_recreio_emef_emei_cieja_ceugestao(instance)
            self.valida_finalizar_medicao_recreio_emef_emei_cieja_ceugestao(instance)
            self.cria_valores_medicao_recreio_cei(instance)
            self.valida_finalizar_medicao_recreio_cei(instance)
            self.cria_valores_medicao_recreio_cemei(instance)
            self.valida_finalizar_medicao_recreio_cemei(instance)

            instance.ue_envia(user=self.context["request"].user)
            anexos = self._process_anexos(instance)
            if hasattr(instance, "ocorrencia"):
                instance.ocorrencia.ue_envia(
                    user=self.context["request"].user, anexos=anexos
                )
            for medicao in instance.medicoes.all():
                medicao.ue_envia(user=self.context["request"].user)

    def cria_valores_medicao_recreio_emef_emei_cieja_ceugestao(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not (instance.escola.eh_emef_emei_cieja or instance.escola.eh_ceu_gestao)
            or instance.logs_salvos
        ):
            return

        cria_valores_medicao_participantes_emef_emei_cieja_ceugestao(instance)
        cria_valores_medicao_participantes_dietas_autorizadas_emef_emei_cieja_ceugestao(
            instance
        )
        instance.logs_salvos = True
        instance.save(update_fields=["logs_salvos"])

    def valida_finalizar_medicao_recreio_emef_emei_cieja_ceugestao(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not (instance.escola.eh_emef_emei_cieja or instance.escola.eh_ceu_gestao)
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return
        lista_erros = []
        lista_erros = validate_lancamento_alimentacoes_medicao_recreio(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_dietas_medicao_recreio(instance, lista_erros)
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        if lista_erros:
            raise serializers.ValidationError(lista_erros)

    def cria_valores_medicao_recreio_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if not instance.escola.eh_cei or instance.logs_salvos:
            return

        cria_valores_medicao_participantes_cei(instance)
        cria_valores_medicao_participantes_dietas_autorizadas_cei(instance)

        instance.logs_salvos = True
        instance.save(update_fields=["logs_salvos"])

    def valida_finalizar_medicao_recreio_cei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_cei
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return
        lista_erros = []
        lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cei(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_dietas_medicao_recreio_cei(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        if lista_erros:
            raise serializers.ValidationError(lista_erros)

    def cria_valores_medicao_recreio_cemei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if not instance.escola.eh_cemei or instance.logs_salvos:
            return

        cria_valores_medicao_participantes_cemei(instance)
        cria_valores_medicao_participantes_dietas_autorizadas_cemei(instance)
        instance.logs_salvos = True
        instance.save(update_fields=["logs_salvos"])

    def valida_finalizar_medicao_recreio_cemei(
        self, instance: SolicitacaoMedicaoInicial
    ) -> None:
        if (
            not instance.escola.eh_cemei
            or instance.status
            != SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        ):
            return
        lista_erros = []
        lista_erros = validate_lancamento_alimentacoes_medicao_recreio_cemei(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_dietas_medicao_recreio_cemei(
            instance, lista_erros
        )
        lista_erros = validate_lancamento_kit_lanche(instance, lista_erros)
        lista_erros = validate_lanche_emergencial(instance, lista_erros)
        if lista_erros:
            raise serializers.ValidationError(lista_erros)

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

    def _apenas_observacoes_em_correcao(self, instance, valores):
        """Impede que salvamentos comuns/autosaves regravem valores em correção."""
        status_correcao = (
            instance.workflow_class.MEDICAO_CORRECAO_SOLICITADA,
            instance.workflow_class.MEDICAO_CORRIGIDA_PELA_UE,
            instance.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE,
            instance.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE,
        )
        if instance.status not in status_correcao or not valores:
            return valores
        return [
            valor
            for valor in valores
            if valor and valor.get("nome_campo") == "observacoes"
        ]

    def create(self, validated_data):
        usuario = self.context["request"].user
        validated_data["criado_por"] = usuario
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
        substitui_criador_system_por_usuario_real(
            medicao.solicitacao_medicao_inicial, usuario
        )

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
        validated_data["valores_medicao"] = self._apenas_observacoes_em_correcao(
            instance, validated_data.get("valores_medicao", None)
        )
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
        instance.save(update_fields=["alterado_em"])

        return instance

    class Meta:
        model = Medicao
        exclude = (
            "id",
            "criado_por",
        )
        validators = []


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
    tipo_valor = serializers.SlugRelatedField(
        slug_field="nome", queryset=TipoValorParametrizacaoFinanceira.objects.all()
    )

    def to_internal_value(self, data):
        if data.get("tipo_alimentacao") == "Kit Lanche":
            data = data.copy()
            data["tipo_alimentacao"] = None

        return super().to_internal_value(data)

    class Meta:
        model = ParametrizacaoFinanceiraTabelaValor
        fields = [
            "nome_campo",
            "faixa_etaria",
            "tipo_alimentacao",
            "tipo_valor",
            "valor",
        ]


class ParametrizacaoFinanceiraTabelaWriteModelSerializer(serializers.ModelSerializer):
    periodo_escolar = serializers.SlugRelatedField(
        slug_field="nome",
        required=False,
        allow_null=True,
        queryset=PeriodoEscolar.objects.all(),
    )
    valores = ParametrizacaoFinanceiraTabelaValorWriteModelSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceiraTabela
        fields = ["nome", "periodo_escolar", "valores"]


class ParametrizacaoFinanceiraWriteModelSerializer(serializers.ModelSerializer):
    edital = serializers.SlugRelatedField(
        slug_field="uuid", queryset=Edital.objects.all()
    )
    lote = serializers.SlugRelatedField(slug_field="uuid", queryset=Lote.objects.all())
    grupo_unidade_escolar = serializers.SlugRelatedField(
        slug_field="uuid", queryset=GrupoUnidadeEscolar.objects.all()
    )
    tabelas = ParametrizacaoFinanceiraTabelaWriteModelSerializer(many=True)

    class Meta:
        model = ParametrizacaoFinanceira
        fields = [
            "edital",
            "lote",
            "grupo_unidade_escolar",
            "data_inicial",
            "data_final",
            "legenda",
            "tabelas",
        ]

    def validate(self, attrs):
        if self.instance:
            return attrs

        existe_ativa = (
            ParametrizacaoFinanceira.objects.filter(
                edital=attrs["edital"],
                lote=attrs["lote"],
                grupo_unidade_escolar=attrs["grupo_unidade_escolar"],
            )
            .filter(
                Q(data_final__isnull=True) | Q(data_final__gte=timezone.now().date())
            )
            .exists()
        )

        if existe_ativa:
            raise ValidationError(
                "Já existe uma parametrização financeira ativa para este edital, lote e grupo de unidades."
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
        tabelas = validated_data.pop("tabelas", None)

        instance = super().update(instance, validated_data)

        if not tabelas:
            return instance

        for tabela in tabelas:
            valores = tabela.pop("valores")

            _tabela, created = ParametrizacaoFinanceiraTabela.objects.get_or_create(
                **tabela,
                parametrizacao_financeira=instance,
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
                    nome_campo=valor.get("nome_campo"),
                    tipo_alimentacao_id=tipo_alimentacao_id,
                    faixa_etaria_id=faixa_etaria_id,
                    tipo_valor=valor.get("tipo_valor"),
                    defaults=valor,
                )

        return instance


class InformacoesBasicasMedicaoInicialUpdateSerializer(
    SolicitacaoMedicaoInicialCreateSerializer
):
    """
    Serializer para atualização básica (responsáveis, alunos, tipos de contagem).
    Reutiliza métodos privados do CreateSerializer.
    """

    class Meta:
        model = SolicitacaoMedicaoInicial
        exclude = ("id", "criado_por")

    def update(self, instance, validated_data):
        self._update_responsaveis(instance)
        validated_data.pop("responsaveis", None)

        self._update_tipos_contagem_alimentacao(instance)
        validated_data.pop("tipos_contagem_alimentacao", None)

        validated_data.pop("alunos_periodo_parcial", None)

        self._update_instance_fields(instance, validated_data)
        self._update_alunos(instance, validated_data)

        usuario = self.context["request"].user
        substitui_criador_system_por_usuario_real(instance, usuario)

        return instance


class DescontoFinanceiroUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para criação e atualização de DescontoFinanceiro.

    Attributes:
        relatorio_financeiro_id (UUID):
            UUID do relatório financeiro associado ao registro.

        unidades_educacionais (list[UUID]):
            Lista de UUIDs das escolas vinculadas ao desconto financeiro.

        faixa_etaria_id (UUID, optional):
            UUID da faixa etária associada ao desconto financeiro.
            Pode ser nulo.

        periodo_escolar_id (UUID, optional):
            UUID do período escolar associado ao desconto financeiro.
            Pode ser nulo.

        clausula_desconto_id (UUID):
            UUID da cláusula de desconto aplicada.

        tipo_lancamento (str):
            Tipo de lançamento do desconto financeiro.
            Deve ser um dos valores definidos em `TIPO_LANCAMENTO_CHOICES`.

        quantidade (int):
            Quantidade relacionada ao lançamento do desconto financeiro.

    Notes:
        - Todos os campos *_id utilizam SlugRelatedField com UUID.
        - O campo `unidades_educacionais` aceita múltiplos valores.
        - Campos com sufixo `_id` são write-only e não aparecem na resposta da API.
        - Quando não houver tipo de alimentação e faixa etária, o desconto é de um kit lanche.
    """

    relatorio_financeiro_id = serializers.SlugRelatedField(
        queryset=RelatorioFinanceiro.objects.all(),
        slug_field="uuid",
        source="relatorio_financeiro",
        write_only=True,
    )
    unidades_educacionais = serializers.SlugRelatedField(
        many=True,
        queryset=Escola.objects.all(),
        slug_field="uuid",
        write_only=True,
    )
    tipo_alimentacao = serializers.SlugRelatedField(
        queryset=TipoAlimentacao.objects.all(),
        slug_field="uuid",
        write_only=True,
        required=False,
        allow_null=True,
    )
    faixa_etaria = serializers.SlugRelatedField(
        queryset=FaixaEtaria.objects.all(),
        slug_field="uuid",
        write_only=True,
        required=False,
        allow_null=True,
    )
    periodo_escolar = serializers.SlugRelatedField(
        queryset=PeriodoEscolar.objects.all(),
        slug_field="nome",
        write_only=True,
        required=False,
        allow_null=True,
    )
    clausula_desconto = serializers.SlugRelatedField(
        queryset=ClausulaDeDesconto.objects.all(),
        slug_field="uuid",
        write_only=True,
    )

    class Meta:
        model = DescontoFinanceiro
        fields = [
            "uuid",
            "relatorio_financeiro_id",
            "unidades_educacionais",
            "tipo_lancamento",
            "tipo_alimentacao",
            "faixa_etaria",
            "periodo_escolar",
            "cei_ou_emei",
            "clausula_desconto",
            "infantil_ou_fundamental",
            "quantidade",
            "criado_em",
            "alterado_em",
        ]

    def validate(self, attrs):
        relatorio = attrs.get("relatorio_financeiro") or getattr(
            self.instance, "relatorio_financeiro", None
        )

        if not relatorio:
            return attrs

        grupo_nome = (
            getattr(relatorio.grupo_unidade_escolar, "nome", "") or ""
        ).upper()

        if GrupoUnidadeEscolar.GRUPO_1.upper() == grupo_nome:
            self._validar_grupo_cei(attrs)

        elif GrupoUnidadeEscolar.GRUPO_2.upper() == grupo_nome:
            self._validar_grupo_cemei(attrs)

        elif GrupoUnidadeEscolar.GRUPO_5.upper() == grupo_nome:
            self._validar_grupo_emebs(attrs)

        else:
            self._validar_grupo_emei(attrs)

        return attrs

    def _validar_grupo_cei(self, attrs, verifica_instancia=True):
        errors = {}

        faixa_etaria = attrs.get("faixa_etaria")
        if faixa_etaria is None and verifica_instancia:
            faixa_etaria = getattr(self.instance, "faixa_etaria", None)

        periodo_escolar = attrs.get("periodo_escolar")
        if periodo_escolar is None and verifica_instancia:
            periodo_escolar = getattr(self.instance, "periodo_escolar", None)

        if not faixa_etaria:
            errors["faixa_etaria"] = (
                StringsValidationErrors.CAMPO_OBRIGATORIO_PARA_O_GRUPO.value
            )

        if not periodo_escolar:
            errors["periodo_escolar"] = (
                StringsValidationErrors.CAMPO_OBRIGATORIO_PARA_O_GRUPO.value
            )

        if errors:
            raise serializers.ValidationError(errors)

    def _validar_grupo_emei(self, attrs, verifica_instancia=True):
        faixa_etaria = attrs.get("faixa_etaria")
        if faixa_etaria is None and verifica_instancia:
            faixa_etaria = getattr(self.instance, "faixa_etaria", None)

        errors = {}
        if faixa_etaria:
            errors["faixa_etaria"] = (
                "Não é permitido informar faixa etária para este grupo."
            )

        if errors:
            raise serializers.ValidationError(errors)

    def _validar_grupo_cemei(self, attrs):
        cei_ou_emei = attrs.get("cei_ou_emei")
        if not cei_ou_emei or cei_ou_emei == "N/A":
            raise serializers.ValidationError(
                {
                    "cei_ou_emei": StringsValidationErrors.CAMPO_OBRIGATORIO_PARA_O_GRUPO.value
                }
            )

        if cei_ou_emei == TIPOS_UNIDADE_ESCOLAR.CEI.value:
            self._validar_grupo_cei(attrs, False)
        else:
            self._validar_grupo_emei(attrs, False)

    def _validar_grupo_emebs(self, attrs):
        infantil_ou_fundamental = attrs.get("infantil_ou_fundamental")
        if not infantil_ou_fundamental or infantil_ou_fundamental == "N/A":
            raise serializers.ValidationError(
                {
                    "infantil_ou_fundamental": StringsValidationErrors.CAMPO_OBRIGATORIO_PARA_O_GRUPO.value
                }
            )
        self._validar_grupo_emei(attrs)


class GerarMedicaoFinalSerializer(serializers.ModelSerializer):
    """Entrada do modal "Gerar Medição Final".

    Espera ``relatorio_financeiro`` e ``request`` no contexto. O nome do
    responsável não é aceito do cliente: vem da consulta do RF.
    """

    rf_responsavel_conferencia = serializers.CharField(
        max_length=20, validators=[somente_digitos]
    )

    class Meta:
        model = MedicaoFinal
        fields = ("rf_responsavel_conferencia", "numero_processo_pagamento")

    def validate(self, attrs):
        relatorio = self.context["relatorio_financeiro"]
        if hasattr(relatorio, "medicao_final"):
            raise serializers.ValidationError(
                "A Medição Final já foi gerada para este Relatório Financeiro."
            )
        if relatorio.status != relatorio.workflow_class.EM_ANALISE:
            raise serializers.ValidationError(
                "Só é possível gerar a Medição Final de um Relatório Financeiro com "
                'status "Em análise".'
            )

        nome = EOLServicoSGP.get_nome_servidor(attrs["rf_responsavel_conferencia"])
        if not nome:
            raise serializers.ValidationError(
                {"rf_responsavel_conferencia": MENSAGEM_RF_NAO_LOCALIZADO}
            )
        attrs["nome_responsavel_conferencia"] = nome
        return attrs

    def create(self, validated_data):
        relatorio = self.context["relatorio_financeiro"]
        usuario = self.context["request"].user
        medicao_final = MedicaoFinal.objects.create(
            relatorio_financeiro=relatorio, gerado_por=usuario, **validated_data
        )
        relatorio.gerar_medicao_final(user=usuario)
        return medicao_final
