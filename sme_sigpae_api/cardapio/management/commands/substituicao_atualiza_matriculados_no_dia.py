from django.core.management.base import BaseCommand

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cei.models import (
    AlteracaoCardapioCEI,
    FaixaEtariaSubstituicaoAlimentacaoCEI,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.models import (
    AlteracaoCardapioCEMEI,
    FaixaEtariaSubstituicaoAlimentacaoCEMEICEI,
    SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI,
)
from sme_sigpae_api.escola.models import EscolaPeriodoEscolar


class Command(BaseCommand):
    help = """
    Popular coluna matriculados_quando_criado com base na data das solicitações de alteracao.
    """

    def handle(self, *args, **options):
        self.stdout.write("Iniciando processo de popular matriculados_quando_criado.")
        self.popular_substituicao_alimentacao_cei()
        self.popular_substituicao_cemei_emei()
        self.popular_substituicao_cemei_cei()

    def popular_substituicao_alimentacao_cei(self):
        self.stdout.write("+++ INICIANDO SUBSTITUICOES CEI +++")
        class_substituicao = FaixaEtariaSubstituicaoAlimentacaoCEI
        solicitacoes_pks = class_substituicao.objects.filter(
            matriculados_quando_criado=None
        )
        solicitacoes_pks = solicitacoes_pks.values_list(
            "substituicao_alimentacao__alteracao_cardapio", flat=True
        ).distinct()
        solicitacoes = AlteracaoCardapioCEI.objects.filter(id__in=solicitacoes_pks)
        for solicitacao in solicitacoes:
            escola_periodo = EscolaPeriodoEscolar.objects.get(
                periodo_escolar__nome="INTEGRAL", escola__uuid=solicitacao.escola.uuid
            )
            faixa_alunos = escola_periodo.alunos_por_faixa_etaria(solicitacao.data)
            substituicoes_faixas_pks = solicitacao.substituicoes_cei_periodo_escolar
            substituicoes_faixas_pks = substituicoes_faixas_pks.values_list(
                "faixas_etarias", flat=True
            ).distinct()
            substituicoes_faixas = FaixaEtariaSubstituicaoAlimentacaoCEI.objects.filter(
                id__in=substituicoes_faixas_pks
            )
            for faixa in substituicoes_faixas:
                matriculados_quando_criado = faixa_alunos[faixa.faixa_etaria.uuid]
                faixa.matriculados_quando_criado = matriculados_quando_criado
                uuid = faixa.faixa_etaria.uuid
                self.stdout.write(
                    f"Faixa uuid: {uuid} - matriculados quando criado: {matriculados_quando_criado}"
                )
                faixa.save()
        self.stdout.write("+++ FINALIZANDO SUBSTITUICOES CEI +++")

    def popular_substituicao_cemei_emei(self):
        self.stdout.write("+++ INICIANDO SUBSTITUICOES CEMEI EMEI +++")
        class_substituicao = SubstituicaoAlimentacaoNoPeriodoEscolarCEMEIEMEI
        solicitacoes_pks = class_substituicao.objects.filter(
            matriculados_quando_criado=None
        )
        solicitacoes_pks = solicitacoes_pks.values_list(
            "alteracao_cardapio", flat=True
        ).distinct()
        solicitacoes = AlteracaoCardapioCEMEI.objects.filter(id__in=solicitacoes_pks)
        for solicitacao in solicitacoes:
            faixa_alunos = solicitacao.escola.quantidade_alunos_por_cei_emei(False)
            substituicoes_faixas = (
                solicitacao.substituicoes_cemei_emei_periodo_escolar.all()
            )
            for faixa in substituicoes_faixas:
                for periodo_matriculas in faixa_alunos:
                    if periodo_matriculas["nome"] == faixa.periodo_escolar.nome:
                        faixa.matriculados_quando_criado = periodo_matriculas["EMEI"]
                        uuid = faixa.uuid
                        qtd = periodo_matriculas["EMEI"]
                        self.stdout.write(
                            f"Substituicao CEMEI EMEI uuid: {uuid} - matriculados quando criado: {qtd}"
                        )
                        faixa.save()
        self.stdout.write("+++ FINALIZANDO SUBSTITUICOES CEMEI EMEI +++")

    def popular_substituicao_cemei_cei(self):
        self.stdout.write("+++ INICIANDO SUBSTITUICOES CEMEI CEI +++")

        solicitacoes = self._get_solicitacoes()

        for solicitacao in solicitacoes:
            faixa_alunos = solicitacao.escola.quantidade_alunos_por_cei_emei(False)
            substituicoes_faixas = self._get_substituicoes_faixas(solicitacao)

            for faixa in substituicoes_faixas:
                self._atualizar_matriculados(faixa, faixa_alunos)

        self.stdout.write("+++ FINALIZANDO SUBSTITUICOES CEMEI CEI +++")

    def _get_solicitacoes(self):
        """Retorna solicitações de alteração de cardápio sem matriculados registrados."""
        substituicoes_sem_matricula = (
            FaixaEtariaSubstituicaoAlimentacaoCEMEICEI.objects.filter(
                matriculados_quando_criado=None
            )
            .values_list("substituicao_alimentacao__alteracao_cardapio", flat=True)
            .distinct()
        )
        return AlteracaoCardapioCEMEI.objects.filter(id__in=substituicoes_sem_matricula)

    def _get_substituicoes_faixas(self, solicitacao):
        """Retorna faixas etárias vinculadas à substituição do cardápio."""
        substituicoes_faixas_pks = (
            solicitacao.substituicoes_cemei_cei_periodo_escolar.values_list(
                "faixas_etarias", flat=True
            ).distinct()
        )
        return FaixaEtariaSubstituicaoAlimentacaoCEMEICEI.objects.filter(
            id__in=substituicoes_faixas_pks
        )

    def _atualizar_matriculados(self, faixa, faixa_alunos):
        """Atualiza o campo matriculados_quando_criado se encontrar correspondência."""
        for periodo_matriculas in faixa_alunos:
            if (
                periodo_matriculas["nome"]
                != faixa.substituicao_alimentacao.periodo_escolar.nome
            ):
                continue

            for faixa_matriculados in periodo_matriculas["CEI"]:
                if faixa_matriculados["uuid"] != str(faixa.faixa_etaria.uuid):
                    continue

                faixa.matriculados_quando_criado = faixa_matriculados[
                    "quantidade_alunos"
                ]
                faixa.save()

                self.stdout.write(
                    f"Faixa uuid: {faixa.faixa_etaria.uuid} - "
                    f"matriculados quando criado: {faixa.matriculados_quando_criado}"
                )
