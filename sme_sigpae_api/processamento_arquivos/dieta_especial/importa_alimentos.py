import logging

from django.db import transaction
from django.db.models import Q
from openpyxl import load_workbook

from sme_sigpae_api.dieta_especial.models import (
    Alimento,
    ArquivoCargaAlimentosSubstitutos,
)

from .schemas import ArquivoCargaAlimentosSchema

logger = logging.getLogger("sigpae.importa_dietas_especiais")


# TODO: Melhorar essas duplicações de códigos nos processmantos das planilhas
class ProcessadorPlanilha:
    def __init__(self, arquivo: ArquivoCargaAlimentosSubstitutos) -> None:
        """Prepara atributos importantes para o processamento da planilha."""
        self.arquivo = arquivo
        self.erros = []
        self.nomes_processados = set()

    @property
    def path(self):
        return self.arquivo.conteudo.path

    def processamento(self):  # noqa C901
        self.arquivo.inicia_processamento()
        if not self.validacao_inicial():
            return

        workbook = load_workbook(self.path)
        logger.info(f"Quantidade de worksheets: {len(workbook.worksheets)}")
        if len(workbook.worksheets) != 2:
            self.arquivo.log = "Erro: Número de abas na planilha é diferente de 2"
            self.arquivo.erro_no_processamento()
            return

        worksheet_alimentos = workbook.worksheets[0]
        worksheet_substitutos = workbook.worksheets[1]
        self.processa_alimentos(
            worksheet=worksheet_alimentos, tipo_listagem=Alimento.SO_ALIMENTOS
        )
        self.processa_alimentos(
            worksheet=worksheet_substitutos, tipo_listagem=Alimento.SO_SUBSTITUTOS
        )
        if not self.erros:
            self.inativa_alimentos_ausentes()

    def validacao_inicial(self) -> bool:
        return self.existe_conteudo() and self.extensao_do_arquivo_esta_correta()

    def existe_conteudo(self) -> bool:
        if not self.arquivo.conteudo:
            self.arquivo.log = "Não foi feito o upload da planilha"
            self.arquivo.erro_no_processamento()
            return False
        return True

    def extensao_do_arquivo_esta_correta(self) -> bool:
        if not self.path.endswith(".xlsx"):
            self.arquivo.log = "Planilha precisa ter extensão .xlsx"
            self.arquivo.erro_no_processamento()
            return False
        return True

    def monta_dicionario_de_dados(self, linha: tuple) -> dict:
        return {
            key: linha[index].value
            for index, key in enumerate(
                ArquivoCargaAlimentosSchema.schema()["properties"].keys()
            )
        }

    @transaction.atomic  # noqa C901
    def processa_alimentos(
        self, worksheet, tipo_listagem=Alimento.SO_ALIMENTOS
    ):  # noqa C901
        linhas = list(worksheet.rows)
        for ind, linha in enumerate(
            linhas[1:], 2
        ):  # Começando em 2 pois a primeira linha é o cabeçalho da planilha
            try:
                dicionario_dados = self.monta_dicionario_de_dados(linha)

                # Faz validações dos campos usando o schema para o alimento
                alimentos_schema = ArquivoCargaAlimentosSchema(**dicionario_dados)
                alimento: Alimento = Alimento.objects.filter(
                    Q(nome=alimentos_schema.nome)
                    | Q(nome=alimentos_schema.nome.upper())
                ).first()
                if not alimento:
                    alimento = Alimento.objects.create(
                        nome=alimentos_schema.nome.upper(),
                        ativo=True,
                        tipo_listagem_protocolo=tipo_listagem,
                    )
                else:
                    alimento.nome = alimentos_schema.nome.upper()

                    if alimento.tipo_listagem_protocolo != tipo_listagem:
                        alimento.tipo_listagem_protocolo = Alimento.AMBOS
                    alimento.save()

                self.nomes_processados.add(alimentos_schema.nome.upper())
            except Exception as exc:
                self.erros.append(f"Linha {ind} - {exc}")

    def inativa_alimentos_ausentes(self) -> None:
        """Inativa os alimentos que não foram encontrados em nenhuma das abas da planilha."""
        inativados = (
            Alimento.objects.filter(ativo=True)
            .exclude(nome__in=self.nomes_processados)
            .update(ativo=False)
        )
        if inativados:
            logger.info(
                f"{inativados} alimento(s) inativado(s) por não constarem na planilha."
            )

    def finaliza_processamento(self) -> None:
        if self.erros:
            self.arquivo.log = "\n".join(self.erros)
            self.arquivo.processamento_com_erro()
        else:
            self.arquivo.log = "Planilha processada com sucesso."
            self.arquivo.processamento_com_sucesso()


def importa_alimentos(arquivo: ArquivoCargaAlimentosSubstitutos) -> None:
    logger.debug(f"Iniciando o processamento do arquivo: {arquivo.uuid}")

    try:
        processador = ProcessadorPlanilha(arquivo)
        processador.processamento()
        processador.finaliza_processamento()
    except Exception as exc:
        logger.error(f"Erro genérico: {exc}")
