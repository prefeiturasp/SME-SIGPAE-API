from ...dados_comuns.constants import DAQUI_A_SETE_DIAS, DAQUI_A_TRINTA_DIAS, SEM_FILTRO

PENDENTES_CIENCIA = "pendentes-ciencia"
PENDENTES_AUTORIZACAO = "pendentes-autorizacao"
PENDENTES_AUTORIZACAO_DIETA_ESPECIAL = "pendentes-autorizacao-dieta"
AUTORIZADOS_DIETA_ESPECIAL = "autorizados-dieta"
AUTORIZADAS_TEMPORARIAMENTE_DIETA_ESPECIAL = "autorizadas-temporariamente-dieta"
AGUARDANDO_INICIO_VIGENCIA_DIETA_ESPECIAL = "aguardando-vigencia-dieta"
INATIVAS_TEMPORARIAMENTE_DIETA_ESPECIAL = "inativas-temporariamente-dieta"
INATIVAS_DIETA_ESPECIAL = "inativas-dieta"
NEGADOS_DIETA_ESPECIAL = "negados-dieta"
CANCELADOS_DIETA_ESPECIAL = "cancelados-dieta"
PENDENTES_VALIDACAO_DRE = "pendentes-validacao"
AUTORIZADOS = "autorizados"
CEU_GESTAO_PERIODOS_COM_SOLICITACOES_AUTORIZADAS = (
    "ceu-gestao-periodos-com-solicitacoes-autorizadas"
)
INCLUSOES_AUTORIZADAS = "inclusoes-autorizadas"
INCLUSOES_ETEC_AUTORIZADAS = "inclusoes-etec-autorizadas"
SUSPENSOES_AUTORIZADAS = "suspensoes-autorizadas"
ALTERACOES_ALIMENTACAO_AUTORIZADAS = "alteracoes-alimentacao-autorizadas"
KIT_LANCHES_AUTORIZADAS = "kit-lanches-autorizadas"
AGUARDANDO_CODAE = "aguardando-codae"
QUESTIONAMENTOS = "questionamentos"
_NEGADOS = "cancelados"
NEGADOS = "negados"
CANCELADOS = "cancelados"
PESQUISA = "pesquisa"
RELATORIO_PERIODO = "relatorio-periodo"
RELATORIO_RESUMO_MES_ANO = "relatorio-resumo-mes-ano"
RESUMO_MES = "resumo-mes"
RESUMO_ANO = "resumo-ano"

FILTRO_CODIGO_EOL_ALUNO = "(?P<codigo_eol_aluno>[^/.]+)"

FILTRO_ESCOLA_UUID = "(?P<escola_uuid>[^/.]+)"
FILTRO_DRE_UUID = "(?P<dre_uuid>[^/.]+)"
FILTRO_TERCEIRIZADA_UUID = "(?P<terceirizada_uuid>[^/.]+)"

FILTRO_PERIOD_UUID_DRE = f"(?P<dre_uuid>[^/.]+)/(?P<filtro_aplicado>({SEM_FILTRO}|{DAQUI_A_SETE_DIAS}|{DAQUI_A_TRINTA_DIAS})+)"  # noqa E501

TIPO_VISAO_DRE = "dre"
TIPO_VISAO_LOTE = "lote"
TIPO_VISAO_SOLICITACOES = "tipo_solicitacao"

TIPO_VISAO = (
    f"(?P<tipo_visao>({TIPO_VISAO_DRE}|{TIPO_VISAO_LOTE}|{TIPO_VISAO_SOLICITACOES})+)"
)

FILTRO_DATA_INICIAL = (
    "(?P<filtro_aplicado>(sem_filtro|daqui_a_7_dias|daqui_a_30_dias)+)"
)
TIPO_SOLICITACAO = "(?P<tipo_solicitacao>(ALT_CARDAPIO|INV_CARDAPIO|INC_ALIMENTA|INC_ALIMENTA_CONTINUA|KIT_LANCHE_AVULSA|SUSP_ALIMENTACAO|KIT_LANCHE_UNIFICADA|TODOS)+)"  # noqa
STATUS_SOLICITACAO = (
    "(?P<status_solicitacao>(AUTORIZADOS|NEGADOS|CANCELADOS|RECEBIDAS|TODOS)+)"
)
DATA_INICIAL = "(?P<data_inicial>.*)"
DATA_FINAL = "(?P<data_final>.*)"

# constants para o export XLSX do relatório de solicitações de alimentação
ROW_IDX_TITULO_ARQUIVO = 0
ROW_IDX_FILTROS_PT1 = 1
ROW_IDX_FILTROS_PT2 = 2
ROW_IDX_HEADER_CAMPOS = 3

COL_IDX_N = 0
COL_IDX_LOTE = 1
COL_IDX_UNIDADE_EDUCACIONAL = 2
COL_IDX_TIPO_DE_SOLICITACAO = 3
COL_IDX_ID_SOLICITACAO = 4
COL_IDX_DATA_EVENTO = 5
COL_IDX_DIA_DA_SEMANA = 6
COL_IDX_PERIODO = 7
COL_IDX_TIPO_DE_ALIMENTACAO = 8
COL_IDX_TIPO_DE_ALTERACAO = 9
COL_IDX_NUMERO_DE_ALUNOS = 10
COL_IDX_NUMERO_TOTAL_KITS = 11
COL_IDX_OBSERVACOES = 12
COL_IDX_DATA_LOG = 13
