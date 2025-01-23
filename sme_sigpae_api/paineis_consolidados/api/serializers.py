import datetime

from rest_framework import serializers

from ...dados_comuns.utils import remove_tags_html_from_string
from ...escola.models import Escola, TipoUnidadeEscolar
from ...kit_lanche.api.serializers.serializers import EscolaQuantidadeSerializerSimples
from ..models import SolicitacoesCODAE
from ..utils.utils import get_dias_inclusao


class SolicitacoesSerializer(serializers.ModelSerializer):
    data_log = serializers.SerializerMethodField()
    descricao = serializers.SerializerMethodField()
    numero_alunos = serializers.SerializerMethodField()
    descricao_dieta_especial = serializers.SerializerMethodField()
    prioridade = serializers.CharField()
    id_externo = serializers.CharField()
    escolas_quantidades = serializers.SerializerMethodField()
    tipo_unidade_escolar = serializers.SerializerMethodField()

    def get_descricao_dieta_especial(self, obj):
        return f'{obj.codigo_eol_aluno if obj.codigo_eol_aluno else "(Aluno não matriculado)"} - {obj.nome_aluno}'

    def get_escolas_quantidades(self, obj):
        usuario = self.context["request"].user
        if obj.tipo_doc == "KIT_LANCHE_UNIFICADA":
            escolas_quantidades = obj.get_raw_model.objects.get(
                uuid=obj.uuid
            ).escolas_quantidades
            serialized = EscolaQuantidadeSerializerSimples(
                escolas_quantidades.filter(
                    escola__uuid=usuario.vinculo_atual.instituicao.uuid
                ),
                many=True,
            )
            return serialized.data
        return None

    def get_numero_alunos(self, obj):
        return obj.get_raw_model.objects.get(uuid=obj.uuid).numero_alunos

    def get_descricao(self, obj):
        uuid = str(obj.uuid)
        lote_nome = obj.lote_nome[:20] if obj.lote_nome else "Sem Lote (Parceira)"
        descricao = f"{uuid.upper()[:5]} - {lote_nome} - {obj.desc_doc}"
        if obj.tipo_solicitacao_dieta == "ALUNO_NAO_MATRICULADO":
            descricao = f"{descricao} - Não matriculados"
        if obj.tipo_solicitacao_dieta == "ALTERACAO_UE":
            descricao = f"{descricao} - Alteração U.E"
        return descricao

    def get_data_log(self, obj):
        if obj.data_log.date() == datetime.date.today():
            return obj.data_log.strftime("%d/%m/%Y %H:%M")
        return obj.data_log.strftime("%d/%m/%Y")

    def get_tipo_unidade_escolar(self, obj):
        tipo_unidade = TipoUnidadeEscolar.objects.filter(
            uuid=obj.escola_tipo_unidade_uuid
        )
        if tipo_unidade:
            return {
                "iniciais": tipo_unidade.first().iniciais,
                "uuid": tipo_unidade.first().uuid,
            }
        return None

    class Meta:
        fields = "__all__"
        model = SolicitacoesCODAE


class SolicitacoesExportXLSXSerializer(serializers.ModelSerializer):
    lote_nome = serializers.CharField()
    escola_ou_terceirizada_nome = serializers.SerializerMethodField()
    desc_doc = serializers.CharField()
    data_evento = serializers.SerializerMethodField()
    tipo_alteracao = serializers.SerializerMethodField()
    numero_alunos = serializers.SerializerMethodField()
    observacoes = serializers.SerializerMethodField()
    data_autorizacao_negacao_cancelamento = serializers.SerializerMethodField()
    id_externo = serializers.CharField()

    def get_escola_ou_terceirizada_nome(self, obj):
        if self.context["status"] == "RECEBIDAS":
            return obj.terceirizada_nome
        elif "Unificada" in str(obj.get_raw_model):
            if isinstance(self.context["instituicao"], Escola):
                return self.context["instituicao"].nome
            else:
                solicitacao_unificada = obj.get_raw_model.objects.get(uuid=obj.uuid)
                return (
                    f"{solicitacao_unificada.escolas_quantidades.count()} Escolas"
                    if solicitacao_unificada.escolas_quantidades.count() > 1
                    else solicitacao_unificada.escolas_quantidades.first().escola.nome
                )
        return obj.escola_nome

    def get_numero_alunos(self, obj):
        if "Unificada" in str(obj.get_raw_model) and isinstance(
            self.context["instituicao"], Escola
        ):
            solicitacao_unificada = obj.get_raw_model.objects.get(uuid=obj.uuid)
            return solicitacao_unificada.escolas_quantidades.get(
                escola=self.context["instituicao"]
            ).quantidade_alunos
        return obj.get_raw_model.objects.get(uuid=obj.uuid).numero_alunos

    def get_data_evento(self, obj):
        if (
            obj.data_evento_fim
            and obj.data_evento
            and obj.data_evento != obj.data_evento_fim
        ):
            return f"{obj.data_evento.strftime('%d/%m/%Y')} - {obj.data_evento_fim.strftime('%d/%m/%Y')}"
        elif obj.tipo_doc in [
            "ALT_CARDAPIO",
            "ALT_CARDAPIO_CEMEI",
            "INC_ALIMENTA",
            "SUSP_ALIMENTACAO",
            "INC_ALIMENTA_CEMEI",
            "INC_ALIMENTA_CEI",
        ]:
            return obj.get_raw_model.objects.get(uuid=obj.uuid).datas
        return obj.data_evento.strftime("%d/%m/%Y") if obj.data_evento else None

    def get_tipo_alteracao(self, obj):
        if "ALT_CARDAPIO" not in obj.tipo_doc:
            return "-"
        return obj.motivo

    def get_data_autorizacao_negacao_cancelamento(self, obj):
        map_data = {
            "AUTORIZADOS": "data_autorizacao",
            "CANCELADOS": "data_cancelamento",
            "NEGADOS": "data_negacao",
            "RECEBIDAS": "data_autorizacao",
        }
        return getattr(
            obj.get_raw_model.objects.get(uuid=obj.uuid),
            map_data[self.context["status"]],
        )

    def get_observacoes(self, obj):
        model_obj = obj.get_raw_model.objects.get(uuid=obj.uuid)
        if obj.tipo_doc in [
            "INC_ALIMENTA_CEMEI",
            "INC_ALIMENTA_CEI",
            "INC_ALIMENTA",
            "ALT_CARDAPIO",
            "ALT_CARDAPIO_CEMEI",
            "SUSP_ALIMENTACAO",
        ]:
            dias = get_dias_inclusao(obj, model_obj)
            if model_obj.status == "ESCOLA_CANCELOU":
                return ("cancelado, " * len(dias))[:-2]
            if model_obj.existe_dia_cancelado:
                return ", ".join(
                    ["cancelado" if dia.cancelado else "autorizado" for dia in dias]
                )
        if hasattr(model_obj, "observacao"):
            return (
                remove_tags_html_from_string(model_obj.observacao)
                if model_obj.observacao
                else None
            )
        elif hasattr(model_obj, "observacoes"):
            return (
                remove_tags_html_from_string(model_obj.observacoes)
                if model_obj.observacoes
                else None
            )
        return None

    class Meta:
        model = SolicitacoesCODAE
        fields = (
            "lote_nome",
            "escola_ou_terceirizada_nome",
            "desc_doc",
            "id_externo",
            "data_evento",
            "tipo_alteracao",
            "numero_alunos",
            "observacoes",
            "data_autorizacao_negacao_cancelamento",
        )
