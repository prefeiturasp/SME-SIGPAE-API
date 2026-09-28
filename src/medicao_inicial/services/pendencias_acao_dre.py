from django.db.models import (
    BooleanField,
    Case,
    Exists,
    OuterRef,
    Q,
    QuerySet,
    Value,
    When,
)

from src.medicao_inicial.models import (
    Medicao,
    OcorrenciaMedicaoInicial,
    SolicitacaoMedicaoInicial,
)


def anotar_pendencia_acao_dre(queryset: QuerySet) -> QuerySet:
    workflow_solicitacao = SolicitacaoMedicaoInicial.workflow_class
    workflow_ocorrencia = OcorrenciaMedicaoInicial.workflow_class
    medicoes_nao_aprovadas = Medicao.objects.filter(
        solicitacao_medicao_inicial=OuterRef("pk")
    ).exclude(status=Medicao.workflow_class.MEDICAO_APROVADA_PELA_CODAE)

    queryset = queryset.annotate(
        possui_medicao_nao_aprovada_codae=Exists(medicoes_nao_aprovadas)
    )

    return queryset.annotate(
        pendente_acao_dre=Case(
            When(
                Q(
                    status=workflow_solicitacao.MEDICAO_CORRIGIDA_PARA_CODAE,
                    dre_ciencia_correcao_data__isnull=True,
                    possui_medicao_nao_aprovada_codae=False,
                )
                & (
                    Q(ocorrencia__isnull=True)
                    | Q(
                        ocorrencia__status=(
                            workflow_ocorrencia.MEDICAO_APROVADA_PELA_CODAE
                        ),
                    )
                ),
                then=Value(True),
            ),
            default=Value(False),
            output_field=BooleanField(),
        )
    )
