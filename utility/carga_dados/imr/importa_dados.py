import logging

from src.dados_comuns.behaviors import StatusAtivoInativo
from src.imr.models import (
    CategoriaOcorrencia,
    ImportacaoPlanilhaTipoOcorrencia,
    ImportacaoPlanilhaTipoPenalidade,
    ObrigacaoPenalidade,
    TipoGravidade,
    TipoOcorrencia,
    TipoPenalidade,
)
from src.perfil.models import Usuario
from src.terceirizada.models import Edital
from utility.carga_dados.imr.schemas import (
    ImportacaoPlanilhaTipoOcorrenciaSchema,
    ImportacaoPlanilhaTipoPenalidadeSchema,
)
from utility.carga_dados.processador_planilha_generico.models import (
    ProcessadorDePlanilha,
)


def importa_tipos_penalidade(
    usuario: Usuario, arquivo: ImportacaoPlanilhaTipoPenalidade
) -> None:
    logger = logging.getLogger("sigpae.carga_dados_tipo_penalidade_importa_dados")
    logger.debug(f"Iniciando o processamento do arquivo: {arquivo.uuid}")

    try:
        processador = ProcessadorPlanilhaTipoPenalidade(
            usuario,
            arquivo,
            ImportacaoPlanilhaTipoPenalidadeSchema,
            "edital",
            "numero_clausula",
            logger,
        )
        processador.processamento()
        processador.finaliza_processamento()
    except Exception as exc:
        logger.error(f"Erro genérico: {exc}")


class ProcessadorPlanilhaTipoPenalidade(ProcessadorDePlanilha):
    def get_edital(self, numero_edital: str):
        return Edital.objects.get(numero=numero_edital)

    def get_tipo_gravidade(self, tipo_gravidade: str):
        return TipoGravidade.objects.get(tipo=tipo_gravidade)

    def cria_tipo_penalidade_obj(
        self,
        usuario_schema: ImportacaoPlanilhaTipoPenalidadeSchema,
    ):
        edital = self.get_edital(usuario_schema.edital)
        gravidade = self.get_tipo_gravidade(usuario_schema.gravidade)
        status = usuario_schema.status == StatusAtivoInativo.ATIVO
        tipo_penalidade, _ = TipoPenalidade.objects.update_or_create(
            edital=edital,
            numero_clausula=usuario_schema.numero_clausula,
            defaults={
                "criado_por": self.usuario,
                "gravidade": gravidade,
                "descricao": usuario_schema.descricao_clausula,
                "status": status,
            },
        )
        return tipo_penalidade

    def normaliza_obrigacoes(self, obrigacoes: str):
        if obrigacoes[-1] == ";":
            obrigacoes = obrigacoes[: len(obrigacoes) - 1]
        return obrigacoes.split(";")

    def cria_obrigacao_penalidade(
        self, tipo_penalidade: TipoPenalidade, descricao: str
    ):
        ObrigacaoPenalidade.objects.create(
            tipo_penalidade=tipo_penalidade, descricao=descricao
        )

    def cria_objeto(
        self, index: int, usuario_schema: ImportacaoPlanilhaTipoPenalidadeSchema
    ):
        tipo_penalidade = self.cria_tipo_penalidade_obj(usuario_schema)
        lista_obrigacoes = self.normaliza_obrigacoes(usuario_schema.obrigacoes)
        for descricao_obrigacao in lista_obrigacoes:
            self.cria_obrigacao_penalidade(tipo_penalidade, descricao_obrigacao)


def importa_tipos_ocorrencia(
    usuario: Usuario, arquivo: ImportacaoPlanilhaTipoOcorrencia
) -> None:
    logger = logging.getLogger("sigpae.carga_dados_tipo_ocorrencia_importa_dados")
    logger.debug(f"Iniciando o processamento do arquivo: {arquivo.uuid}")

    try:
        processador = ProcessadorPlanilhaTipoOcorrencia(
            usuario,
            arquivo,
            ImportacaoPlanilhaTipoOcorrenciaSchema,
            "categoria_ocorrencia",
            "titulo",
            logger,
        )
        processador.processamento()
        processador.finaliza_processamento()
    except Exception as exc:
        logger.error(f"Erro genérico: {exc}")


class ProcessadorPlanilhaTipoOcorrencia(ProcessadorDePlanilha):
    def get_perfis(self, perfis: str):
        perfis_ = []
        if "DIRETOR" in perfis:
            perfis_.append("DIRETOR")
        if "SUPERVISAO" in perfis:
            perfis_.append("SUPERVISAO")
        return perfis_

    def get_edital(self, numero_edital: str):
        return Edital.objects.get(numero=numero_edital)

    def get_categoria(self, nome_categoria: str):
        return CategoriaOcorrencia.objects.get(nome=nome_categoria)

    def get_penalidade(self, numero_clausula: str, edital: Edital):
        try:
            return TipoPenalidade.objects.get(
                numero_clausula=numero_clausula.split(" - ")[1], edital=edital
            )
        except TipoPenalidade.DoesNotExist:
            raise Exception(
                "O edital do tipo de penalidade precisa ser o mesmo selecionado na coluna Edital"
            )

    def cria_objeto(
        self, index: int, tipo_ocorrencia_schema: ImportacaoPlanilhaTipoOcorrenciaSchema
    ):
        perfis = self.get_perfis(tipo_ocorrencia_schema.perfis)
        edital = self.get_edital(tipo_ocorrencia_schema.edital)
        categoria = self.get_categoria(tipo_ocorrencia_schema.categoria_ocorrencia)
        penalidade = self.get_penalidade(tipo_ocorrencia_schema.penalidade, edital)
        eh_imr = tipo_ocorrencia_schema.eh_imr == "SIM"
        status = tipo_ocorrencia_schema.status == StatusAtivoInativo.ATIVO
        aceita_multiplas_respostas = (
            tipo_ocorrencia_schema.aceita_multiplas_respostas == "Sim"
        )
        tipo_ocorrencia, _ = TipoOcorrencia.objects.update_or_create(
            edital=edital,
            categoria=categoria,
            penalidade=penalidade,
            titulo=tipo_ocorrencia_schema.titulo,
            defaults={
                "criado_por": self.usuario,
                "posicao": tipo_ocorrencia_schema.posicao,
                "perfis": perfis,
                "edital": edital,
                "descricao": tipo_ocorrencia_schema.descricao,
                "eh_imr": eh_imr,
                "pontuacao": tipo_ocorrencia_schema.pontuacao,
                "tolerancia": tipo_ocorrencia_schema.tolerancia,
                "porcentagem_desconto": tipo_ocorrencia_schema.porcentagem_desconto,
                "status": status,
                "aceita_multiplas_respostas": aceita_multiplas_respostas,
            },
        )
        return tipo_ocorrencia
