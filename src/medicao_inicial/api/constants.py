from ..models import SolicitacaoMedicaoInicial

STATUS_RELACAO_DRE_UE = [
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_ENVIADA_PELA_UE,
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA,
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PELA_UE,
]

STATUS_RELACAO_DRE_CODAE = [
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_DRE,
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRECAO_SOLICITADA_CODAE,
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_CORRIGIDA_PARA_CODAE,
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_APROVADA_PELA_CODAE,
]

STATUS_RELACAO_DRE_MEDICAO = [
    SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
] + STATUS_RELACAO_DRE_CODAE

STATUS_RELACAO_DRE = (
    [SolicitacaoMedicaoInicial.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE]
    + STATUS_RELACAO_DRE_UE
    + STATUS_RELACAO_DRE_CODAE
)

ALIMENTACOES_LANCAMENTOS_ESPECIAIS = [
    "2_lanche_4h",
    "2_lanche_5h",
    "lanche_extra",
    "2_refeicao_1_oferta",
    "repeticao_2_refeicao",
    "2_sobremesa_1_oferta",
    "repeticao_2_sobremesa",
]

ORDEM_NAME_LANCAMENTOS_ESPECIAIS = {
    "2_lanche_4h": 1,
    "2_lanche_5h": 2,
    "lanche_extra": 3,
    "2_refeicao_1_oferta": 4,
    "repeticao_2_refeicao": 5,
    "2_sobremesa_1_oferta": 6,
    "repeticao_2_sobremesa": 7,
}

USUARIOS_VISAO_CODAE = [
    "gestao_alimentacao_terceirizada",
    "nutricao_manifestacao",
    "codae_gabinete",
]
