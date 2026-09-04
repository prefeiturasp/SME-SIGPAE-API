import io
import mimetypes
import zipfile
from typing import Any
from uuid import UUID

from src.dados_comuns.models import AnexoLogSolicitacoesUsuario, LogSolicitacoesUsuario
from src.produto.models import AnexoReclamacaoDeProduto, ReclamacaoDeProduto

TipoAnexoHistorico = AnexoReclamacaoDeProduto | AnexoLogSolicitacoesUsuario

ACOES_COM_ARQUIVOS_NO_HISTORICO = {
    LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
    LogSolicitacoesUsuario.NUTRISUPERVISOR_RESPONDEU_RECLAMACAO,
    LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
    LogSolicitacoesUsuario.UE_RESPONDEU_RECLAMACAO,
}


class ServicoHistoricoReclamacaoProduto:
    @staticmethod
    def obter_reclamacao(uuid_reclamacao: UUID | str) -> ReclamacaoDeProduto:
        return ReclamacaoDeProduto.objects.get(uuid=uuid_reclamacao)

    @staticmethod
    def obter_log(
        reclamacao: ReclamacaoDeProduto,
        uuid_log: UUID | str,
    ) -> LogSolicitacoesUsuario:
        return LogSolicitacoesUsuario.objects.get(
            uuid=uuid_log,
            uuid_original=reclamacao.uuid,
            solicitacao_tipo=LogSolicitacoesUsuario.RECLAMACAO_PRODUTO,
        )

    @classmethod
    def obter_anexos_acao(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> list[TipoAnexoHistorico]:
        reclamacao = cls.obter_reclamacao(uuid_reclamacao)
        if str(reclamacao.uuid) == str(uuid_log):
            return list(reclamacao.anexos.all())

        log = cls.obter_log(reclamacao, uuid_log)
        if log.status_evento not in ACOES_COM_ARQUIVOS_NO_HISTORICO:
            return []
        if (
            log.status_evento
            == LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ):
            return list(reclamacao.anexos.all())
        return list(log.anexos.all())

    @classmethod
    def obter_anexos_log_para_resumo(
        cls,
        log: LogSolicitacoesUsuario,
        anexos_iniciais: list[AnexoReclamacaoDeProduto],
    ) -> list[TipoAnexoHistorico]:
        if log.status_evento not in ACOES_COM_ARQUIVOS_NO_HISTORICO:
            return []
        if (
            log.status_evento
            == LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
        ):
            return anexos_iniciais
        return list(log.anexos.all())

    @classmethod
    def obter_pdfs_acao(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> list[TipoAnexoHistorico]:
        anexos = cls.obter_anexos_acao(uuid_reclamacao, uuid_log)
        pdfs = [
            anexo
            for anexo in anexos
            if cls._obter_tipo_mime(anexo) == "application/pdf"
        ]
        return pdfs

    @classmethod
    def obter_imagens_acao(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> list[TipoAnexoHistorico]:
        return [
            anexo
            for anexo in cls.obter_anexos_acao(uuid_reclamacao, uuid_log)
            if cls._eh_imagem(anexo)
        ]

    @staticmethod
    def _obter_tipo_mime(anexo: TipoAnexoHistorico) -> str | None:
        nome_arquivo = anexo.nome or anexo.arquivo.name
        tipo_mime, _ = mimetypes.guess_type(nome_arquivo)
        return tipo_mime

    @staticmethod
    def obter_nome_anexo(anexo: TipoAnexoHistorico) -> str:
        nome_arquivo = anexo.nome or anexo.arquivo.name
        return nome_arquivo.rsplit("/", maxsplit=1)[-1]

    @classmethod
    def obter_nome_download_pdfs(
        cls,
        pdfs: list[TipoAnexoHistorico],
        uuid_log: UUID | str,
    ) -> str:
        if len(pdfs) == 1:
            return cls.obter_nome_anexo(pdfs[0])
        return f"documentos_reclamacao_{uuid_log}.zip"

    @classmethod
    def obter_nome_download_imagens(
        cls,
        imagens: list[TipoAnexoHistorico],
        uuid_log: UUID | str,
    ) -> str:
        if len(imagens) == 1:
            return cls.obter_nome_anexo(imagens[0])
        return f"imagens_reclamacao_{uuid_log}.zip"

    @classmethod
    def _eh_imagem(cls, anexo: TipoAnexoHistorico) -> bool:
        tipo_mime = cls._obter_tipo_mime(anexo)
        return bool(tipo_mime and tipo_mime.startswith("image/"))

    @classmethod
    def obter_resumo_arquivos(
        cls,
        anexos: list[TipoAnexoHistorico],
    ) -> dict[str, bool | int]:
        tipos_mime = [cls._obter_tipo_mime(anexo) for anexo in anexos]
        return {
            "possui_pdf": "application/pdf" in tipos_mime,
            "quantidade_imagens": sum(
                1
                for tipo_mime in tipos_mime
                if tipo_mime and tipo_mime.startswith("image/")
            ),
        }

    @classmethod
    def obter_resumo_arquivos_acao(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> dict[str, bool | int]:
        return cls.obter_resumo_arquivos(
            cls.obter_anexos_acao(uuid_reclamacao, uuid_log)
        )

    @classmethod
    def obter_dados_acao_inicial_legada(
        cls,
        reclamacao: ReclamacaoDeProduto,
        logs: list[LogSolicitacoesUsuario],
        anexos: list[AnexoReclamacaoDeProduto],
    ) -> dict[str, Any] | None:
        possui_log_inicial = any(
            log.status_evento
            == LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
            for log in logs
        )
        if possui_log_inicial:
            return None
        return {
            "uuid": str(reclamacao.uuid),
            "anexos": anexos,
            "status_evento": (
                LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU
            ),
            "status_evento_explicacao": dict(
                LogSolicitacoesUsuario.STATUS_POSSIVEIS
            )[LogSolicitacoesUsuario.ESCOLA_OU_NUTRICIONISTA_RECLAMOU],
            "usuario": reclamacao.criado_por,
            "criado_em": reclamacao.criado_em.strftime("%d/%m/%Y %H:%M:%S"),
            "descricao": str(reclamacao),
            "justificativa": reclamacao.reclamacao,
            "resposta_sim_nao": False,
            "tipo_solicitacao_explicacao": "Reclamação de Produto",
            "arquivos_disponiveis": cls.obter_resumo_arquivos(anexos),
        }

    @classmethod
    def gerar_arquivo_pdfs(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> tuple[str, bytes, str]:
        pdfs = cls.obter_pdfs_acao(uuid_reclamacao, uuid_log)
        if not pdfs:
            raise ValueError("Não há PDF disponível para esta ação do histórico.")
        nome_download = cls.obter_nome_download_pdfs(pdfs, uuid_log)
        return cls._gerar_arquivo(pdfs, nome_download)

    @classmethod
    def gerar_arquivo_imagens(
        cls,
        uuid_reclamacao: UUID | str,
        uuid_log: UUID | str,
    ) -> tuple[str, bytes, str]:
        imagens = cls.obter_imagens_acao(uuid_reclamacao, uuid_log)
        if not imagens:
            raise ValueError(
                "Não há imagens disponíveis para esta ação do histórico."
            )
        nome_download = cls.obter_nome_download_imagens(imagens, uuid_log)
        return cls._gerar_arquivo(imagens, nome_download)

    @classmethod
    def _gerar_arquivo(
        cls,
        anexos: list[TipoAnexoHistorico],
        nome_download: str,
    ) -> tuple[str, bytes, str]:
        if len(anexos) == 1:
            anexo = anexos[0]
            tipo_mime = cls._obter_tipo_mime(anexo)
            return (
                nome_download,
                cls._ler_conteudo_anexo(anexo),
                tipo_mime or "application/octet-stream",
            )
        return nome_download, cls._gerar_zip(anexos), "application/zip"

    @staticmethod
    def _ler_conteudo_anexo(anexo: TipoAnexoHistorico) -> bytes:
        anexo.arquivo.open("rb")
        try:
            return anexo.arquivo.read()
        finally:
            anexo.arquivo.close()

    @classmethod
    def _gerar_zip(cls, anexos: list[TipoAnexoHistorico]) -> bytes:
        arquivo_zip = io.BytesIO()
        with zipfile.ZipFile(
            arquivo_zip,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as zip_arquivos:
            nomes_utilizados: set[str] = set()
            for anexo in anexos:
                nome_anexo = cls.obter_nome_anexo(anexo)
                if nome_anexo in nomes_utilizados:
                    nome_anexo = f"{anexo.uuid}_{nome_anexo}"
                nomes_utilizados.add(nome_anexo)
                zip_arquivos.writestr(
                    nome_anexo,
                    cls._ler_conteudo_anexo(anexo),
                )
        return arquivo_zip.getvalue()
