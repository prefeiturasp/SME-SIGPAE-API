from sme_sigpae_api.dados_comuns.models import LogSolicitacoesUsuario

from ..dados_comuns.fluxo_status import (
    HomologacaoProdutoWorkflow,
    ReclamacaoProdutoWorkflow,
)

NOVA_RECLAMACAO_HOMOLOGACOES_STATUS = [
    HomologacaoProdutoWorkflow.CODAE_HOMOLOGADO,
    HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
    HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
]

AVALIAR_RECLAMACAO_HOMOLOGACOES_STATUS = [
    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
    HomologacaoProdutoWorkflow.ESCOLA_OU_NUTRICIONISTA_RECLAMOU,
    HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
    HomologacaoProdutoWorkflow.CODAE_AUTORIZOU_RECLAMACAO,
]

AVALIAR_RECLAMACAO_RECLAMACOES_STATUS = [
    ReclamacaoProdutoWorkflow.AGUARDANDO_AVALIACAO,
    ReclamacaoProdutoWorkflow.RESPONDIDO_TERCEIRIZADA,
]

RESPONDER_RECLAMACAO_HOMOLOGACOES_STATUS = [
    HomologacaoProdutoWorkflow.CODAE_PEDIU_ANALISE_RECLAMACAO,
    HomologacaoProdutoWorkflow.TERCEIRIZADA_RESPONDEU_RECLAMACAO,
]

RESPONDER_RECLAMACAO_RECLAMACOES_STATUS = [
    ReclamacaoProdutoWorkflow.AGUARDANDO_RESPOSTA_TERCEIRIZADA
]


STATUS_DICT = dict(LogSolicitacoesUsuario.STATUS_POSSIVEIS)
RELATORIO_RECLAMACOES_PRODUTOS = {
    "rotulo_data_log": {
        STATUS_DICT[LogSolicitacoesUsuario.UE_RESPONDEU_RECLAMACAO]: "Data resposta UE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_PEDIU_ANALISE_SENSORIAL
        ]: "Data req. análise sens.",
        STATUS_DICT[
            LogSolicitacoesUsuario.NUTRISUPERVISOR_RESPONDEU_RECLAMACAO
        ]: "Data resposta nutricionista",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_QUESTIONOU_NUTRISUPERVISOR
        ]: "Data questionamento CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_QUESTIONOU_TERCEIRIZADA
        ]: "Data questionamento CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_QUESTIONOU_UE
        ]: "Data questionamento CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO
        ]: "Data resposta terceirizada",
        STATUS_DICT[
            LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_ANALISE_SENSORIAL
        ]: "Data resposta terceirizada",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO
        ]: "Data avaliação CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO
        ]: "Data avaliação CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_RESPONDEU_RECLAMACAO
        ]: "Data resposta CODAE",
    },
    "titulo_log": {
        STATUS_DICT[
            LogSolicitacoesUsuario.TERCEIRIZADA_RESPONDEU_RECLAMACAO
        ]: "Resposta terceirizada",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_QUESTIONOU_TERCEIRIZADA
        ]: "Questionamento CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_AUTORIZOU_RECLAMACAO
        ]: "Justificativa avaliação CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_RECUSOU_RECLAMACAO
        ]: "Justificativa avaliação CODAE",
        STATUS_DICT[
            LogSolicitacoesUsuario.CODAE_RESPONDEU_RECLAMACAO
        ]: "Resposta CODAE",
    },
}
