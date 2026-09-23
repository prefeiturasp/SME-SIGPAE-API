import datetime
from enum import Enum

import environ
from workalendar.america import BrazilSaoPauloCity

calendar = BrazilSaoPauloCity()
env = environ.Env()


def obter_dias_uteis_apos_hoje(quantidade_dias: int):
    """Retorna o próximo dia útil após quantidade_dias."""
    dia = datetime.date.today()

    return calendar.add_working_days(dia, quantidade_dias)


DJANGO_EOL_API_TOKEN = env("DJANGO_EOL_API_TOKEN")
DJANGO_EOL_API_URL = env("DJANGO_EOL_API_URL")

DJANGO_EOL_SGP_API_TOKEN = env("DJANGO_EOL_SGP_API_TOKEN")
DJANGO_EOL_SGP_API_URL = env("DJANGO_EOL_SGP_API_URL")

DJANGO_NOVO_SGP_API_TOKEN = env("DJANGO_NOVO_SGP_API_TOKEN")
DJANGO_NOVO_SGP_API_URL = env("DJANGO_NOVO_SGP_API_URL")
DJANGO_NOVO_SGP_API_LOGIN = env("DJANGO_NOVO_SGP_API_LOGIN")
DJANGO_NOVO_SGP_API_PASSWORD = env("DJANGO_NOVO_SGP_API_PASSWORD")

DJANGO_EOL_PAPA_API_URL = env("DJANGO_EOL_PAPA_API_URL")
DJANGO_EOL_PAPA_API_USUARIO = f'{env("DJANGO_EOL_PAPA_API_USUARIO")}'
DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO = (
    f'{env("DJANGO_EOL_PAPA_API_SENHA_CANCELAMENTO")}'
)
DJANGO_EOL_PAPA_API_SENHA_ENVIO = f'{env("DJANGO_EOL_PAPA_API_SENHA_ENVIO")}'

DJANGO_ADMIN_PASSWORD = f'{env("DJANGO_ADMIN_PASSWORD")}'
DJANGO_ADMIN_TREINAMENTO_PASSWORD = f'{env("DJANGO_ADMIN_TREINAMENTO_PASSWORD")}'

DJANGO_AUTENTICA_CORESSO_API_TOKEN = env(
    "DJANGO_AUTENTICA_CORESSO_API_TOKEN", default=""
)
DJANGO_AUTENTICA_CORESSO_API_URL = env("DJANGO_AUTENTICA_CORESSO_API_URL", default="")

PRIORITARIO = 2
LIMITE_INFERIOR = 3
LIMITE_SUPERIOR = 5
REGULAR = 6

MINIMO_DIAS_PARA_PEDIDO = obter_dias_uteis_apos_hoje(PRIORITARIO)
DIAS_UTEIS_LIMITE_INFERIOR = obter_dias_uteis_apos_hoje(LIMITE_INFERIOR)
DIAS_UTEIS_LIMITE_SUPERIOR = obter_dias_uteis_apos_hoje(LIMITE_SUPERIOR)
DIAS_DE_PRAZO_REGULAR_EM_DIANTE = obter_dias_uteis_apos_hoje(REGULAR)

#
# PEDIDOS
#

SEM_FILTRO = "sem_filtro"
DAQUI_A_SETE_DIAS = "daqui_a_7_dias"
DAQUI_A_TRINTA_DIAS = "daqui_a_30_dias"

PEDIDOS_CODAE = "pedidos-codae"
PEDIDOS_TERCEIRIZADA = "pedidos-terceirizadas"
PEDIDOS_DRE = "pedidos-diretoria-regional"
FILTRO_PADRAO_PEDIDOS = (
    f"(?P<filtro_aplicado>({SEM_FILTRO}|{DAQUI_A_SETE_DIAS}|{DAQUI_A_TRINTA_DIAS})+)"
)

RASCUNHO = "rascunho"
CODAE_PENDENTE_HOMOLOGACAO = "codae_pendente_homologacao"  # INICIO
CODAE_HOMOLOGADO = "codae_homologado"
CODAE_NAO_HOMOLOGADO = "codae_nao_homologado"
CODAE_QUESTIONADO = "codae_questionado"
CODAE_PEDIU_ANALISE_SENSORIAL = "codae_pediu_analise_sensorial"
TERCEIRIZADA_CANCELOU = "terceirizada_cancelou"
CODAE_SUSPENDEU = "codae_suspendeu"
ESCOLA_OU_NUTRICIONISTA_RECLAMOU = "escola_ou_nutricionista_reclamou"
CODAE_PEDIU_ANALISE_RECLAMACAO = "codae_pediu_analise_reclamacao"
CODAE_AUTORIZOU_RECLAMACAO = "codae_autorizou_reclamacao"
RESPONDER_QUESTIONAMENTO_DA_CODAE = "responder_questionamentos_da_codae"


FILTRO_STATUS_HOMOLOGACAO = (
    f"(?P<filtro_aplicado>({RASCUNHO}|{CODAE_PENDENTE_HOMOLOGACAO}|{CODAE_HOMOLOGADO}|"
    f"{CODAE_NAO_HOMOLOGADO}|{CODAE_QUESTIONADO}|{CODAE_PEDIU_ANALISE_SENSORIAL}|"
    f"{TERCEIRIZADA_CANCELOU}|{CODAE_SUSPENDEU}|{ESCOLA_OU_NUTRICIONISTA_RECLAMOU}|"
    f"{CODAE_PEDIU_ANALISE_RECLAMACAO}|{CODAE_AUTORIZOU_RECLAMACAO}|"
    f"{RESPONDER_QUESTIONAMENTO_DA_CODAE})+)"
)

RELATORIO = "relatorio"
RELATORIO_HISTORICO = "relatorio-historico"
RELATORIO_ANALISE = "relatorio-analise-sensorial"
RELATORIO_SUSPENSOS = "relatorio-produtos-suspensos"
RELATORIO_RECEBIMENTO = "relatorio-analise-sensorial-recebimento"
RELATORIO_HISTORICO_DIETA = "relatorio-historico-dieta"
PROTOCOLO = "protocolo"

#
# FLUXO, usados nas actions de transição de status nas viewsets dos pedidos/informações do sistema
#
# TODO: trocar pedido por solicitação
ESCOLA_INICIO_PEDIDO = "inicio-pedido"
ESCOLA_REVISA_PEDIDO = "escola-revisa-pedido"
ESCOLA_CANCELA = "escola-cancela-pedido-48h-antes"
CANCELA_SUSPENSAO_CEI = "cancela-suspensao-cei"
ESCOLA_INFORMA_SUSPENSAO = "informa-suspensao"
ESCOLA_SOLICITA_INATIVACAO = "escola-solicita-inativacao"

ESCOLA_CANCELA_DIETA_ESPECIAL = "escola-cancela-dieta-especial"
CODAE_NEGA_CANCELAMENTO_DIETA = "negar-cancelamento-dieta-especial"

DRE_INICIO_PEDIDO = "inicio-pedido"
DRE_VALIDA_PEDIDO = "diretoria-regional-valida-pedido"
DRE_NAO_VALIDA_PEDIDO = "diretoria-regional-nao-valida-pedido"
DRE_PEDE_REVISAO = "diretoria-regional-pede-revisao"
DRE_REVISA_PEDIDO = "diretoria-regional-revisa"
DRE_CANCELA = "diretoria-regional-cancela"

CODAE_AUTORIZA_PEDIDO = "codae-autoriza-pedido"
CODAE_ATUALIZA_PROTOCOLO = "codae-atualiza-protocolo"
CODAE_AUTORIZA_INATIVACAO = "codae-autoriza-inativacao"
CODAE_NEGA_PEDIDO = "codae-cancela-pedido"
CODAE_NEGA_INATIVACAO = "codae-nega-inativacao"
CODAE_PEDE_REVISAO = "codae-pediu-revisao"
CODAE_QUESTIONA_PEDIDO = "codae-questiona-pedido"
CODAE_HOMOLOGA = "codae-homologa"
CODAE_NAO_HOMOLOGA = "codae-nao-homologa"
CODAE_PEDE_ANALISE_SENSORIAL = "codae-pede-analise-sensorial"
CODAE_CANCELA_ANALISE_SENSORIAL = "codae-cancela-analise-sensorial"
TERCEIRIZADA_INATIVA_HOMOLOGACAO = "terceirizada-inativa"
ESCOLA_OU_NUTRI_RECLAMA = "escola-ou-nutri-reclama"
ESCOLA_RESPONDE = "escola-responde"
NUTRISUPERVISOR_RESPONDE = "nutrisupervisor-responde"
SUSPENDER_PRODUTO = "suspender"
ATIVAR_PRODUTO = "ativar"
GERAR_PDF = "gerar-pdf"
GERAR_PDF_FICHA_IDENTIFICACAO_PRODUTO = "gerar-pdf-ficha-identificacao-produto"
AGUARDANDO_ANALISE_SENSORIAL = "aguardando-analise-sensorial"
TERCEIRIZADA_RESPONDE_ANALISE_SENSORIAL = "terceirizada-responde-analise-sensorial"
TERCEIRIZADA_RESPONDE_RECLAMACAO = "terceirizada-responde-reclamacao"
TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO = "cancela-solicitacao-homologacao"
TERCEIRIZADA_RESPONDE = "terceirizada-responde"
CODAE_PEDE_ANALISE_RECLAMACAO = "codae-pede-analise-reclamacao"
CODAE_RECUSA_RECLAMACAO = "codae-recusa-reclamacao"
CODAE_ACEITA_RECLAMACAO = "codae-aceita-reclamacao"
CODAE_ACEITA = "codae-aceita"
CODAE_RECUSA = "codae-recusa"
CODAE_QUESTIONA_TERCEIRIZADA = "codae-questiona-terceirizada"
CODAE_QUESTIONA_UE = "codae-questiona-ue"
CODAE_QUESTIONA_NUTRISUPERVISOR = "codae-questiona-nutrisupervisor"
CODAE_RESPONDE = "codae-responde"
CODAE_CANCELA_SOLICITACAO_CORRECAO = "codae-cancela-solicitacao-correcao"
TERCEIRIZADA_CANCELA_SOLICITACAO_CORRECAO = "terceirizada-cancela-solicitacao-correcao"
VINCULOS_ATIVOS_PRODUTO_EDITAL = "vinculos-ativos-produto-edital"

TERCEIRIZADA_RESPONDE_QUESTIONAMENTO = "terceirizada-responde-questionamento"
TERCEIRIZADA_TOMOU_CIENCIA = "terceirizada-toma-ciencia"
TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO = "terceirizada-toma-ciencia-inativacao"
MARCAR_CONFERIDA = "marcar-conferida"
VINCULOS_INCLUSOES_EVENTO_ESPECIFICO_AUTORIZADAS = (
    "vinculos-inclusoes-evento-especifico-autorizadas"
)

#
# FILTROS
#

SOLICITACOES_DO_USUARIO = "minhas-solicitacoes"

#
# TIPO DE GESTÃO
#

DIRETA = "DIRETA"
PARCEIRA = "PARCEIRA"

#
# PERFIS
#
DIRETOR_UE = "DIRETOR_UE"
ADMINISTRADOR_UE = "ADMINISTRADOR_UE"
COGESTOR_DRE = "COGESTOR_DRE"
COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA = (
    "COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA"
)
ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA = (
    "ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA"
)
COORDENADOR_DIETA_ESPECIAL = "COORDENADOR_DIETA_ESPECIAL"
ADMINISTRADOR_DIETA_ESPECIAL = "ADMINISTRADOR_DIETA_ESPECIAL"
COORDENADOR_GESTAO_PRODUTO = "COORDENADOR_GESTAO_PRODUTO"
COORDENADOR_LOGISTICA = "COORDENADOR_LOGISTICA"
ADMINISTRADOR_GESTAO_PRODUTO = "ADMINISTRADOR_GESTAO_PRODUTO"
ADMINISTRADOR_EMPRESA = "ADMINISTRADOR_EMPRESA"
USUARIO_EMPRESA = "USUARIO_EMPRESA"
COORDENADOR_SUPERVISAO_NUTRICAO = "COORDENADOR_SUPERVISAO_NUTRICAO"
COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO = (
    "COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO"
)
ADMINISTRADOR_SUPERVISAO_NUTRICAO = "ADMINISTRADOR_SUPERVISAO_NUTRICAO"
COORDENADOR_CODAE_DILOG_LOGISTICA = "COORDENADOR_CODAE_DILOG_LOGISTICA"
ADMINISTRADOR_CODAE_GABINETE = "ADMINISTRADOR_CODAE_GABINETE"
ADMINISTRADOR_CODAE_DILOG_CONTABIL = "ADMINISTRADOR_CODAE_DILOG_CONTABIL"
ADMINISTRADOR_CODAE_DILOG_JURIDICO = "ADMINISTRADOR_CODAE_DILOG_JURIDICO"
ADMINISTRADOR_MEDICAO = "ADMINISTRADOR_MEDICAO"
DILOG_CRONOGRAMA = "DILOG_CRONOGRAMA"
DILOG_QUALIDADE = "DILOG_QUALIDADE"
DILOG_DIRETORIA = "DILOG_DIRETORIA"
DILOG_VISUALIZACAO = "DILOG_VISUALIZACAO"
DINUTRE_DIRETORIA = "DINUTRE_DIRETORIA"
ADMINISTRADOR_REPRESENTANTE_CODAE = "ADMINISTRADOR_REPRESENTANTE_CODAE"
ORGAO_FISCALIZADOR = "ORGAO_FISCALIZADOR"
USUARIO_RELATORIOS = "USUARIO_RELATORIOS"
USUARIO_GTIC_CODAE = "USUARIO_GTIC_CODAE"
ADMINISTRADOR_CONTRATOS = "ADMINISTRADOR_CONTRATOS"
DILOG_ABASTECIMENTO = "DILOG_ABASTECIMENTO"

#
# TIPOS DE USUARIO
#
TIPO_USUARIO_TERCEIRIZADA = "terceirizada"
TIPO_USUARIO_GESTAO_PRODUTO = "gestao_produto"
TIPO_USUARIO_ESCOLA = "escola"
TIPO_USUARIO_DIRETORIA_REGIONAL = "diretoriaregional"
TIPO_USUARIO_NUTRISUPERVISOR = "supervisao_nutricao"
TIPO_USUARIO_GESTAO_ALIMENTACAO_TERCEIRIZADA = "gestao_alimentacao_terceirizada"
TIPO_USUARIO_NUTRIMANIFESTACAO = "nutricao_manifestacao"
TIPO_USUARIO_ORGAO_FISCALIZADOR = "orgao_fiscalizador"
TIPO_USUARIO_CODAE_GABINETE = "codae_gabinete"
TIPO_USUARIO_ADMINISTRADOR_CONTRATOS = "administrador_contratos"
TIPO_USUARIO_DILOG_ABASTECIMENTO = "dilog_abastecimento"

#
# DOMINIOS USADOS APENAS EM DESENVOLVIMENTO
#
DOMINIOS_DEV = [
    "@admin.com",
    "@dev.prefeitura.sp.gov.br",
    "@emailteste.sme.prefeitura.sp.gov.br",
]

# CACHE
TEMPO_CACHE_6H = 60 * 60 * 6
TEMPO_CACHE_1H = 60 * 60 * 6

DEZ_MB = 10485760


CODAE_AUTORIZOU_RECLAMACAO = "CODAE autorizou reclamação"
CODAE_RECUSOU_RECLAMACAO = "CODAE recusou reclamação"
CODAE_QUESTIONOU_TERCEIRIZADA = "CODAE questionou terceirizada sobre reclamação"
CODAE_QUESTIONOU_UE = "CODAE questionou U.E. sobre reclamação"
CODAE_RESPONDEU_RECLAMACAO = "CODAE respondeu ao reclamante da reclamação"
TERCEIRIZADA_RESPONDEU_RECLAMACAO = "Terceirizada respondeu a reclamação"
UE_RESPONDEU_RECLAMACAO = "U.E. respondeu a reclamação"
ESCOLA_CANCELOU_LABEL = "Escola cancelou"
EM_ANALISE_LABEL = "Em análise"
ERRO_SALVAR_LOG_TRANSICAO = "Deve criar um método salvar_log_transicao"

TIPO_SOLICITACAO_DIETA = {
    "COMUM": "COMUM",
    "ALTERACAO_UE": "ALTERACAO_UE",
    "ALUNO_NAO_MATRICULADO": "ALUNO_NAO_MATRICULADO",
}

TIPOS_TURMAS_EMEBS = ["INFANTIL", "FUNDAMENTAL"]

#
# NOMES DE GRUPOS DE MEDICAÇÃO E DIETAS (reutilizados no módulo medicao_inicial)
#

GRUPO_INFANTIL_MANHA = "Infantil MANHA"
GRUPO_INFANTIL_TARDE = "Infantil TARDE"
GRUPO_INFANTIL_INTEGRAL = "Infantil INTEGRAL"
GRUPO_PROGRAMAS_E_PROJETOS = "Programas e Projetos"
GRUPO_SOLICITACOES_ALIMENTACAO = "Solicitações de Alimentação"
GRUPO_RECREIO_NAS_FERIAS = "Recreio nas Férias"
GRUPO_RECREIO_NAS_FERIAS_0_A_3 = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
GRUPO_RECREIO_NAS_FERIAS_4_A_14 = "Recreio nas Férias - 4 a 14 anos"
DIETA_ESPECIAL_TIPO_A = "DIETA ESPECIAL - TIPO A"
DIETA_ESPECIAL_TIPO_B = "DIETA ESPECIAL - TIPO B"

ORDEM_PERIODOS_GRUPOS_EMEBS = {
    "MANHA - INFANTIL": 1,
    "MANHA - FUNDAMENTAL": 2,
    "TARDE - INFANTIL": 3,
    "TARDE - FUNDAMENTAL": 4,
    "INTEGRAL - INFANTIL": 5,
    "INTEGRAL - FUNDAMENTAL": 6,
    "VESPERTINO - INFANTIL": 7,
    "VESPERTINO - FUNDAMENTAL": 8,
    "INTERMEDIARIO - INFANTIL": 9,
    "INTERMEDIARIO - FUNDAMENTAL": 10,
    "NOITE - INFANTIL": 11,
    "NOITE - FUNDAMENTAL": 12,
    "Programas e Projetos - INFANTIL": 13,
    "Programas e Projetos - FUNDAMENTAL": 14,
    "Solicitações de Alimentação - INFANTIL": 15,
    "Solicitações de Alimentação - FUNDAMENTAL": 16,
}

ORDEM_PERIODOS_GRUPOS = {
    "MANHA": 1,
    GRUPO_INFANTIL_MANHA: 1,
    "TARDE": 2,
    GRUPO_INFANTIL_TARDE: 2,
    "INTEGRAL": 3,
    GRUPO_INFANTIL_INTEGRAL: 3,
    "NOITE": 4,
    "Infantil NOITE": 4,
    "INTERMEDIARIO": 5,
    "VESPERTINO": 6,
    GRUPO_PROGRAMAS_E_PROJETOS: 7,
    GRUPO_SOLICITACOES_ALIMENTACAO: 8,
    "ETEC": 9,
    GRUPO_RECREIO_NAS_FERIAS: 10,
    "Colaboradores": 11,
}

ORDEM_PERIODOS_GRUPOS_CEI = {
    "INTEGRAL": 1,
    "PARCIAL": 2,
    "MANHA": 3,
    "TARDE": 4,
    GRUPO_RECREIO_NAS_FERIAS: 5,
    "Colaboradores": 6,
}

ORDEM_PERIODOS_GRUPOS_CEMEI = {
    "INTEGRAL": 1,
    "PARCIAL": 2,
    GRUPO_INFANTIL_INTEGRAL: 3,
    GRUPO_INFANTIL_MANHA: 4,
    GRUPO_INFANTIL_TARDE: 5,
    GRUPO_PROGRAMAS_E_PROJETOS: 6,
    GRUPO_RECREIO_NAS_FERIAS: 7,
    GRUPO_RECREIO_NAS_FERIAS_0_A_3: 8,
    GRUPO_RECREIO_NAS_FERIAS_4_A_14: 9,
    GRUPO_SOLICITACOES_ALIMENTACAO: 10,
    "Colaboradores": 11,
}

ORDEM_PERIODOS_GRUPOS_RECREIO_NAS_FERIAS = {
    GRUPO_RECREIO_NAS_FERIAS: 1,
    GRUPO_RECREIO_NAS_FERIAS_0_A_3: 2,
    GRUPO_RECREIO_NAS_FERIAS_4_A_14: 3,
    "Colaboradores": 4,
    GRUPO_SOLICITACOES_ALIMENTACAO: 5,
}

MAX_COLUNAS = 15

#
# MEDICAO INICIAL - EXCEL RELATÓRIO CONSOLIDADO
#

ORDEM_CAMPOS = [
    "numero_de_alunos",
    "participantes",
    "matriculados",
    "aprovadas",
    "frequencia",
    "solicitado",
    "consumido",
    "desjejum",
    "lanche",
    "lanche_4h",
    "2_lanche_4h",
    "2_lanche_5h",
    "lanche_extra",
    "colacao",
    "refeicao",
    "repeticao_refeicao",
    "2_refeicao_1_oferta",
    "repeticao_2_refeicao",
    "kit_lanche",
    "total_refeicoes_pagamento",
    "sobremesa",
    "repeticao_sobremesa",
    "2_sobremesa_1_oferta",
    "repeticao_2_sobremesa",
    "total_sobremesas_pagamento",
    "lanche_emergencial",
]

NOMES_CAMPOS = {
    "lanche": "Lanche",
    "lanche_4h": "Lanche 4h",
    "2_lanche_4h": "2º Lanche 4h",
    "2_lanche_5h": "2º Lanche 5h",
    "lanche_extra": "Lanche Extra",
    "refeicao": "Refeição",
    "repeticao_refeicao": "Repetição de Refeição",
    "2_refeicao_1_oferta": "2ª Refeição 1ª Oferta",
    "repeticao_2_refeicao": "Repetição 2ª Refeição",
    "kit_lanche": "Kit Lanche",
    "total_refeicoes_pagamento": "Total de Refeições para Pagamento",
    "sobremesa": "Sobremesa",
    "repeticao_sobremesa": "Repetição de Sobremesa",
    "2_sobremesa_1_oferta": "2ª Sobremesa 1ª Oferta",
    "repeticao_2_sobremesa": "Repetição 2ª Sobremesa",
    "total_sobremesas_pagamento": "Total de Sobremesas para Pagamento",
    "lanche_emergencial": "Lanche Emerg.",
    "colacao": "Colação",
    "desjejum": "Desjejum",
    "frequencia": "Frequência",
}

ORDEM_UNIDADES_GRUPO_EMEF = {
    "EMEF": 1,
    "CEU EMEF": 2,
    "EMEFM": 3,
    "EMEF P FOM": 4,
    "CEU GESTAO": 5,
}

ORDEM_UNIDADES_GRUPO_EMEI = {
    "EMEI": 1,
    "CEU EMEI": 2,
    "EMEI P FOM": 3,
}

ORDEM_UNIDADES_GRUPO_CEI = {
    "CEI DIRET": 1,
    "CEI CEU": 2,
    "CEU CEI": 3,
    "CCI": 4,
    "CCI/CIPS": 5,
    "CEI": 6,
}

ORDEM_UNIDADES_GRUPO_CEMEI = {
    "CEMEI": 1,
    "CEU CEMEI": 2,
}

ORDEM_UNIDADES_GRUPO_EMEBS = {
    "EMEBS": 1,
}

ORDEM_UNIDADES_GRUPO_CIEJA_CMCT = {"CIEJA": 1, "CMCT": 2}


ORDEM_HEADERS_EMEI_EMEF = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    "MANHA": 2,
    "TARDE": 3,
    "INTEGRAL": 4,
    "NOITE": 5,
    "INTERMEDIARIO": 6,
    "VESPERTINO": 7,
    GRUPO_PROGRAMAS_E_PROJETOS: 8,
    "ETEC": 9,
    DIETA_ESPECIAL_TIPO_A: 10,
    DIETA_ESPECIAL_TIPO_B: 11,
}

ORDEM_HEADERS_CEI = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    "INTEGRAL": 2,
    "DIETA ESPECIAL - TIPO A - INTEGRAL": 3,
    "DIETA ESPECIAL - TIPO B - INTEGRAL": 4,
    "PARCIAL": 5,
    "DIETA ESPECIAL - TIPO A - PARCIAL": 6,
    "DIETA ESPECIAL - TIPO B - PARCIAL": 7,
    "MANHA": 8,
    "TARDE": 9,
    DIETA_ESPECIAL_TIPO_A: 10,
    DIETA_ESPECIAL_TIPO_B: 11,
}

ORDEM_HEADERS_CEMEI = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    "INTEGRAL": 2,
    "DIETA ESPECIAL - TIPO A - INTEGRAL": 3,
    "DIETA ESPECIAL - TIPO B - INTEGRAL": 4,
    "PARCIAL": 5,
    "DIETA ESPECIAL - TIPO A - PARCIAL": 6,
    "DIETA ESPECIAL - TIPO B - PARCIAL": 7,
    GRUPO_INFANTIL_INTEGRAL: 8,
    GRUPO_INFANTIL_MANHA: 9,
    GRUPO_INFANTIL_TARDE: 10,
    "DIETA ESPECIAL - TIPO A - INFANTIL": 11,
    "DIETA ESPECIAL - TIPO B - INFANTIL": 12,
    GRUPO_PROGRAMAS_E_PROJETOS: 13,
    "DIETA ESPECIAL - TIPO A - PROGRAMAS E PROJETOS": 14,
    "DIETA ESPECIAL - TIPO B - PROGRAMAS E PROJETOS": 15,
}

ORDEM_HEADERS_EMEBS = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    "MANHA": 2,
    "TARDE": 3,
    "INTEGRAL": 4,
    "NOITE": 5,
    "INTERMEDIARIO": 6,
    "VESPERTINO": 7,
    GRUPO_PROGRAMAS_E_PROJETOS: 8,
    DIETA_ESPECIAL_TIPO_A: 9,
    DIETA_ESPECIAL_TIPO_B: 10,
}

ORDEM_HEADERS_CIEJA_CMCT = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    "MANHA": 2,
    "TARDE": 3,
    "INTEGRAL": 4,
    "NOITE": 5,
    "INTERMEDIARIO": 6,
    "VESPERTINO": 7,
    GRUPO_PROGRAMAS_E_PROJETOS: 8,
    "ETEC": 9,
    DIETA_ESPECIAL_TIPO_A: 10,
    DIETA_ESPECIAL_TIPO_B: 11,
}

# Para o recreio nas Férias
ORDEM_CAMPOS_RECREIO = [
    "numero_de_alunos",
    "participantes",
    "matriculados",
    "aprovadas",
    "frequencia",
    "solicitado",
    "consumido",
    "desjejum",
    "lanche",
    "lanche_4h",
    "2_lanche_4h",
    "2_lanche_5h",
    "lanche_extra",
    "colacao",
    "refeicao",
    "repeticao_refeicao",
    "2_refeicao_1_oferta",
    "repeticao_2_refeicao",
    "total_refeicoes_pagamento",
    "sobremesa",
    "repeticao_sobremesa",
    "2_sobremesa_1_oferta",
    "repeticao_2_sobremesa",
    "total_sobremesas_pagamento",
    "lanche_emergencial",
    "kit_lanche",
]

ORDEM_HEADERS_RECREIO_EMEI_EMEF = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    GRUPO_RECREIO_NAS_FERIAS: 2,
    DIETA_ESPECIAL_TIPO_A: 3,
    DIETA_ESPECIAL_TIPO_B: 4,
    "Colaboradores": 5,
}

ORDEM_HEADERS_RECREIO_CEI = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    GRUPO_RECREIO_NAS_FERIAS: 2,
    DIETA_ESPECIAL_TIPO_A: 3,
    DIETA_ESPECIAL_TIPO_B: 4,
    "Colaboradores": 5,
}

ORDEM_HEADERS_RECREIO_CEMEI = {
    GRUPO_SOLICITACOES_ALIMENTACAO: 1,
    GRUPO_RECREIO_NAS_FERIAS_0_A_3: 2,
    "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - DE 0 A 3 ANOS E 11 MESES": 3,
    "DIETA ESPECIAL - TIPO B - RECREIO NAS FÉRIAS - DE 0 A 3 ANOS E 11 MESES": 4,
    GRUPO_RECREIO_NAS_FERIAS_4_A_14: 5,
    "DIETA ESPECIAL - TIPO A - RECREIO NAS FÉRIAS - 4 A 14 ANOS": 6,
    "DIETA ESPECIAL - TIPO B - RECREIO NAS FÉRIAS - 4 A 14 ANOS": 7,
    "Colaboradores": 8,
}


class FaixasEtarias(Enum):
    ZERO_A_UM_MES = "0 a 1 mes"
    UM_A_TRES_MESES = "01 a 03 meses"
    QUATRO_A_CINCO_MESES = "04 a 05 meses"
    SEIS_MESES = "06 meses"
    SEIS_A_SETE_MESES = "06 a 07 meses"
    SETE_A_ONZE_MESES = "07 a 11 meses"
    OITO_A_ONZE_MESES = "08 a 11 meses"
    UM_ANO_A_UM_ANO_E_ONZE_MESES = "01 ano a 01 ano e 11 meses"
    UM_ANO_A_TRES_ANOS_E_ONZE_MESES = "01 ano a 03 anos e 11 meses"
    DOIS_ANOS_A_TRES_ANOS_E_ONZE_MESES = "02 anos a 03 anos e 11 meses"
    QUATRO_ANOS_A_SEIS_ANOS = "04 anos a 06 anos"
    ZERO_MESES_A_CINCO_MESES = "0 meses a 05 meses"
    ZERO_MESES_A_ONZE_MESES = "0 meses a 11 meses"
    UM_A_NOVE_MESES = "01 a 09 meses"
    UM_A_DOIS_MESES = "01 a 02 meses"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class ClassificacoesDietasDeprecadas(Enum):
    TIPO_B_LANCHE = "Tipo B - LANCHE"
    TIPO_B_LANCHE_REFEICAO = "Tipo B - LANCHE e REFEIÇÃO"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class NomesParaTesteDiretoriaRegional(Enum):
    DIRETORIA_REGIONAL_TESTE = "DIRETORIA REGIONAL TESTE"
    DIRETORIA_REGIONAL_GUAIANASES = "DIRETORIA REGIONAL GUAIANASES"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class NomesParaTesteEscola(Enum):
    EMEI_ALUISIO_DE_ALMEIDA = "EMEI ALUISIO DE ALMEIDA"
    EMEF_TESTE = "EMEF TESTE"
    EMEI_TESTE = "EMEI TESTE"
    CEI_DIRET_TESTE = "CEI DIRET TESTE"
    CEMEI_TESTE = "CEMEI TESTE"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsCabecalhoXLSXGuiaDaRemessa(Enum):
    AGRUP = "Agrup"
    AGRUPAMENTO = "Agrupamento"
    ALIMENTO = "Alimento"
    BAIRRO_UE = "Bairro UE"
    BAIRRO_DA_UE = "Bairro da UE"
    CEP_UE = "CEP UE"
    CEP_DA_UE = "CEP da UE"
    CAPACIDADE_EMBALAGEM_FECHADA = "Capacidade (Embalagem Fechada)"
    CAPACIDADE_EMBALAGEM_FRACIONADA = "Capacidade (Embalagem Fracionada)"
    CAPACIDADE_DA_EMBALAGEM_FECHADA = "Capacidade da Embalagem Fechada"
    CAPACIDADE_DA_EMBALAGEM_FRACIONADA = "Capacidade da Embalagem Fracionada"
    CEP_DA_UE_2 = "Cep da UE"
    CIDADE_UE = "Cidade UE"
    CONTATO_DA_ENTREGA = "Contato da Entrega"
    CONTATO_DE_ENTREGA = "Contato de Entrega"
    CODIGO_CODAE = "Código CODAE"
    CODIGO_CODAE_DA_UE = "Código CODAE da UE"
    CODIGO_EOL = "Código EOL"
    CODIGO_EOL_DA_UE = "Código EOL da UE"
    CODIGO_PAPA = "Código PAPA"
    CODIGO_SUPRI = "Código SUPRI"
    CODIGO_SUPRI_2 = "Código Supri"
    DATA_DE_ENTREGA = "Data de Entrega"
    DATA_DE_REGISTRO_DO_INSUCESSO = "Data de Registro do Insucesso"
    DATA_DE_REGISTRO_DA_REPOSICAO_COM_HORA = "Data de registro da reposição (com hora)"
    DATA_E_HORA_DE_REGISTRO_REPOSICAO = "Data e Hora de Registro (Reposição)"
    DATA_E_HORA_DO_RECEBIMENTO_1A_CONFERENCIA = (
        "Data e Hora do Recebimento (1ª Conferência)"
    )
    DATA_E_HORA_DO_RECEBIMENTO_1A_CONFERENCIA_2 = (
        "Data e Hora do Recebimento (1ª Conferência) "
    )
    DATA_E_HORA_DO_RECEBIMENTO_REPOSICAO = "Data e Hora do Recebimento (Reposição)"
    DATA_E_HORA_DO_REGISTRO_1A_CONFERENCIA = "Data e Hora do Registro (1ª Conferência)"
    DATA_E_HORA_DO_REGISTRO_REPOSICAO = "Data e Hora do Registro (Reposição)"
    DATA_E_HORA_DO_RECEBIMENTO_1A_CONFERENCIA_3 = (
        "Data e Hora do recebimento (1ª Conferência)"
    )
    DATA_E_HORA_DO_REGISTRO_1A_CONFERENCIA_2 = (
        "Data e hora do Registro (1ª Conferência) "
    )
    DESCRICAO_EMBALAGEM_FECHADA = "Descrição Embalagem Fechada"
    DESCRICAO_EMBALAGEM_FRACIONADA = "Descrição Embalagem Fracionada"
    DOCUMENTO_DO_CONFERENTE = "Documento do Conferente"
    ENDERECO_UE = "Endereço UE"
    ENDERECO_DA_UE = "Endereço da UE"
    ENDERECO_DA_UE_2 = "Endereço da UE "
    ESTADO_UE = "Estado UE"
    HORA_DA_TENTATIVA_DE_ENTREGA = "Hora da tentativa de entrega"
    HORA_DE_REGISTRO_DO_INSUCESSO = "Hora de Registro do Insucesso"
    JUSTIFICATIVA = "Justificativa"
    MOTIVO = "Motivo"
    NOME_COMPLETO_DO_CONFERENTE = "Nome Completo do Conferente"
    NOME_COMPLETO_DO_CONFERENTE_1A_CONFERENCIA = (
        "Nome Completo do Conferente (1ª Conferência)"
    )
    NOME_COMPLETO_DO_CONFERENTE_REPOSICAO = "Nome Completo do Conferente (Reposição)"
    NOME_UE = "Nome UE"
    NOME_COMPLETO_DO_CONFERENTE_1A_CONFERENCIA_2 = (
        "Nome completo do conferente (1ª Conferência)"
    )
    NOME_COMPLETO_DO_CONFERENTE_REPOSICAO_2 = "Nome completo do conferente (Reposição)"
    NOME_DA_UE = "Nome da UE"
    NOME_DO_ALIMENTO = "Nome do Alimento"
    NOME_DO_DISTRIBUIDOR = "Nome do Distribuidor"
    NOME_DO_MOTORISTA = "Nome do Motorista"
    NOME_DO_MOTORISTA_1A_CONFERENCIA = "Nome do Motorista (1ª Conferência)"
    NOME_DO_MOTORISTA_REPOSICAO = "Nome do Motorista (Reposição)"
    NOME_DO_MOTORISTA_1A_CONFERENCIA_2 = "Nome do motorista (1ª Conferência)"
    NOME_DO_MOTORISTA_REPOSICAO_2 = "Nome do motorista (Reposição)"
    NO_DA_REQUISICAO = "Nº da Requisição"
    NUMERO_UE = "Número UE"
    NUMERO_DA_GUIA = "Número da Guia"
    NUMERO_DA_GUIA_DE_REMESSA = "Número da Guia de Remessa"
    NUMERO_DA_REQUISICAO = "Número da Requisição"
    OBSERVACAO_1A_CONFERENCIA = "Observação (1ª Conferência)"
    OBSERVACOES_1A_CONFERENCIA = "Observações (1ª Conferência)"
    OBSERVACOES_REPOSICAO = "Observações (Reposição)"
    OCORRENCIAS_1A_CONFERENCIA = "Ocorrências (1ª Conferência)"
    OCORRENCIAS_REPOSICAO = "Ocorrências (Reposição)"
    PLACA_DO_VEICULO = "Placa do Veículo"
    PLACA_DO_VEICULO_1A_CONFERENCIA = "Placa do Veículo (1ª Conferência)"
    PLACA_DO_VEICULO_REPOSICAO = "Placa do Veículo (Reposição)"
    PLACA_DO_VEICULO_1A_CONFERENCIA_2 = "Placa do veículo (1ª Conferência)"
    PLACA_DO_VEICULO_REPOSICAO_2 = "Placa do veículo (Reposição)"
    QUANTIDADE = "Quantidade"
    QUANTIDADE_FRACIONADA = "Quantidade (Fracionada)"
    QUANTIDADE_PREVISTA_EMBALAGEM_FECHADA = "Quantidade Prevista (Embalagem Fechada)"
    QUANTIDADE_PREVISTA_EMBALAGEM_FECHADA_2 = "Quantidade Prevista (Embalagem Fechada) "
    QUANTIDADE_PREVISTA_EMBALAGEM_FRACIONADA = (
        "Quantidade Prevista (Embalagem Fracionada)"
    )
    QUANTIDADE_PREVISTA_EMBALAGEM_FRACIONADA_2 = (
        "Quantidade Prevista (Embalagem Fracionada) "
    )
    QUANTIDADE_PREVISTA_VOLUMES_DA_EMBALAGEM_FECHADA = (
        "Quantidade Prevista (Volumes da Embalagem Fechada)"
    )
    QUANTIDADE_PREVISTA_VOLUMES_DA_EMBALAGEM_FRACIONADA = (
        "Quantidade Prevista (Volumes da Embalagem Fracionada)"
    )
    QUANTIDADE_RECEBIDA_EMBALAGEM_FECHADA = "Quantidade Recebida (Embalagem Fechada)"
    QUANTIDADE_RECEBIDA_EMBALAGEM_FRACIONADA = (
        "Quantidade Recebida (Embalagem Fracionada)"
    )
    QUANTIDADE_REPOSTA_EMBALAGEM_FECHADA = "Quantidade Reposta (Embalagem Fechada)"
    QUANTIDADE_REPOSTA_EMBALAGEM_FRACIONADA = (
        "Quantidade Reposta (Embalagem Fracionada)"
    )
    QUANTIDADE_TOTAL_DE_GUIAS = "Quantidade Total de Guias"
    QUANTIDADE_A_REPOR_EMBALAGEM_FECHADA = "Quantidade a Repor (Embalagem Fechada)"
    QUANTIDADE_A_REPOR_EMBALAGEM_FRACIONADA = (
        "Quantidade a Repor (Embalagem Fracionada)"
    )
    QUANTIDADE_A_RECEBER_EMBALAGEM_FECHADA = (
        "Quantidade a \u200bReceber (Embalagem Fechada)"
    )
    QUANTIDADE_A_RECEBER_EMBALAGEM_FRACIONADA = (
        "Quantidade a \u200bReceber (Embalagem Fracionada)"
    )
    QUANTIDADE_A_REPOR_REFERENTE_A_QUANTIDADE_A_RECEBER_EMBALAGEM_FRACIONADA = "Quantidade a \u200brepor, referente a quantidade a receber (Embalagem Fracionada)"
    QUANTIDADE_A_REPOR_REFERENTE_A_QUANTIDADE_A_RECEBER_EMBALAGEM_FECHADA = (
        "Quantidade a \u200brepor, referente a quantidade a receber(Embalagem Fechada)"
    )
    QUANTIDADE_DE_VOLUMES_DA_EMBALAGEM_FECHADA = (
        "Quantidade de Volumes da Embalagem Fechada"
    )
    QUANTIDADE_DE_VOLUMES_DA_EMBALAGEM_FRACIONADA = (
        "Quantidade de Volumes da Embalagem Fracionada"
    )
    QUANTIDADE_PREVISTA_EMBALAGEM_FECHADA_3 = "Quantidade prevista (Embalagem Fechada)"
    QUANTIDADE_PREVISTA_EMBALAGEM_FRACIONADA_3 = (
        "Quantidade prevista (Embalagem Fracionada)"
    )
    QUANTIDADE_RECEBIDA_EMBALAGEM_FECHADA_2 = "Quantidade recebida (Embalagem Fechada)"
    QUANTIDADE_RECEBIDA_EMBALAGEM_FRACIONADA_2 = (
        "Quantidade recebida (Embalagem Fracionada)"
    )
    QUANTIDADE_REPOSTA_EMBALAGEM_FECHADA_2 = "Quantidade reposta (Embalagem Fechada)"
    QUANTIDADE_REPOSTA_EMBALAGEM_FRACIONADA_2 = (
        "Quantidade reposta (Embalagem Fracionada)"
    )
    REPOSICAO_DATA_E_HORA_DO_RECEBIMENTO = "Reposição (Data e Hora do recebimento)"
    STATUS_DA_GUIA = "Status da Guia"
    STATUS_DA_GUIA_DE_REMESSA = "Status da Guia de Remessa"
    STATUS_DA_REQUISICAO = "Status da Requisição"
    STATUS_DE_RECEBIMENTO_DO_ALIMENTO_1A_CONFERENCIA = (
        "Status de Recebimento do Alimento (1ª Conferência)"
    )
    STATUS_DE_RECEBIMENTO_DO_ALIMENTO_REPOSICAO = (
        "Status de Recebimento do Alimento (Reposição)"
    )
    STATUS_DE_RECEBIMENTO_DO_ALIMENTO_1A_CONFERENCIA_2 = (
        "Status de Recebimento do alimento (1ª Conferência)"
    )
    STATUS_DE_RECEBIMENTO_DO_ALIMENTO_REPOSICAO_2 = (
        "Status de recebimento do alimento (Reposição)"
    )
    TELEFONE_UE = "Telefone UE"
    TELEFONE_DA_UE = "Telefone da UE"
    UNIDADE_DE_MEDIDA_DA_EMBALAGEM_FECHADA = "Unidade de Medida da Embalagem Fechada"
    UNIDADE_DE_MEDIDA_DA_EMBALAGEM_FRACIONADA = (
        "Unidade de Medida da Embalagem Fracionada"
    )

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsPatterns(Enum):
    CNPJ = "########0001##"
    CODIGO_UNIDADE = "UNI####"
    CODIGO_PAPA = "PAPA####"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsNomesAbasXLSX(Enum):
    RELATORIO_DE_CONFERENCIA = "Relatório de Conferência"
    VISAO_ANALITICA_ABASTECIMENTO = "Visão Analítica Abastecimento"
    RELATORIO_DE_INSUCESSO = "Relatório de Insucesso"
    DIETAS_NAO_RELACIONADAS = "Dietas não relacionadas"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsSourceSerializers(Enum):
    ESCOLA_UUID = "escola.uuid"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsObservacaoValorMedicao(Enum):
    OBSERVACAO_FUNDAMENTAL_DIA_01 = "observação FUNDAMENTAL dia 01"
    OBSERVACAO_FUNDAMENTAL_DIA_02 = "observação FUNDAMENTAL dia 02"
    OBSERVACAO_FUNDAMENTAL_DIA_03 = "observação FUNDAMENTAL dia 03"
    OBSERVACAO_FUNDAMENTAL_DIA_04 = "observação FUNDAMENTAL dia 04"
    OBSERVACAO_FUNDAMENTAL_DIA_05 = "observação FUNDAMENTAL dia 05"
    OBSERVACAO_INFANTIL_DIA_01 = "observação INFANTIL dia 01"
    OBSERVACAO_INFANTIL_DIA_02 = "observação INFANTIL dia 02"
    OBSERVACAO_INFANTIL_DIA_03 = "observação INFANTIL dia 03"
    OBSERVACAO_INFANTIL_DIA_04 = "observação INFANTIL dia 04"
    OBSERVACAO_INFANTIL_DIA_05 = "observação INFANTIL dia 05"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsNomesArquivos(Enum):
    ARQUIVO_TESTE_PDF = "arquivo_teste.pdf"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsModelosGestaoAlimentacao(Enum):
    INCLUSAO_DE_ALIMENTACAO = "Inclusão de Alimentação"
    KIT_LANCHE_PASSEIO = "Kit Lanche Passeio"
    KIT_LANCHE_UNIFICADO = "Kit Lanche Unificado"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsInformacoesPessoais(Enum):
    NOME_ALUNO_PADRAO = "Roberto Alves da Silva"
    CODIGO_ALUNO = "1234567"
    NOME_ALUNO = "MARIA CLARA DOS SANTOS"
    NOME_RESPONSAVEL = "JOSE CARLOS DOS SANTOS"
    CODIGO_ALUNO_SHEILA = "7654321"
    NOME_ALUNO_SHEILA = "ANA PAULA MENEZES"
    NOME_RESPONSAVEL_SHEILA = "ANA PAULA MENEZES"
    CELULAR_RESPONSAVEL_SHEILA = "11999998888"
    ENDERECO_UNIDADE = "Rua Alvaro de Azevedo Antunes"
    BAIRRO_UNIDADE = "VILA CAMPESINA"
    NOME_MOTORISTA = "José da Silva"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsDatasISO(Enum):
    DATA_NASCIMENTO_2017_11_17 = "2017-11-17T00:00:00"
    DATA_SITUACAO_2022_02_09 = "2022-02-09T08:27:35.887"
    DATA_SITUACAO_2022_10_31 = "2022-10-31T12:46:58.16"
    DATA_SITUACAO_2022_12_13 = "2022-12-13T13:44:02.94"
    DATA_SITUACAO_2023_04_24_09053 = "2023-04-24T12:42:09.053"
    DATA_SITUACAO_2023_04_24_0841 = "2023-04-24T12:42:08.41"
    DATA_SITUACAO_2023_04_24_0891 = "2023-04-24T12:42:08.91"
    DATA_SITUACAO_2023_05_11 = "2023-05-11T06:50:17.84"
    DATA_SITUACAO_2023_06_14 = "2023-06-14T08:25:08.59"
    DATA_SITUACAO_2023_07_07 = "2023-07-07T12:29:21.54"
    DATA_SITUACAO_2023_11_06 = "2023-11-06T14:58:22.7"
    DATA_SITUACAO_2023_12_29_38720 = "2023-12-29T07:38:40.72"
    DATA_SITUACAO_2023_12_29_38720623 = "2023-12-29T07:38:40.623"
    DATA_NASCIMENTO_1983_12_25 = "1983-12-25T00:00:00"
    DATA_SITUACAO_2022_09_02 = "2022-09-02T15:14:52.56"
    DATA_SITUACAO_2022_11_03 = "2022-11-03T19:49:01.807"
    DATA_SITUACAO_2022_12_14_1615 = "2022-12-14T16:15:54.233"
    DATA_SITUACAO_2022_12_14_1456 = "2022-12-14T14:56:58.12"
    DATA_SITUACAO_2023_01_27_1218 = "2023-01-27T12:18:04.147"
    DATA_SITUACAO_2023_01_27_1221 = "2023-01-27T12:21:02.407"
    DATA_SITUACAO_2023_08_07 = "2023-08-07T11:37:06.47"
    DATA_SITUACAO_2023_08_11 = "2023-08-11T10:43:15.697"
    DATA_SITUACAO_2023_08_16_1031 = "2023-08-16T10:31:30.36"
    DATA_SITUACAO_2023_08_16_1031423 = "2023-08-16T10:31:30.423"
    DATA_SITUACAO_2023_08_16_1031578 = "2023-08-16T10:31:57.8"
    DATA_SITUACAO_2023_08_17_1319 = "2023-08-17T13:19:36.69"
    DATA_SITUACAO_2023_08_17_1319563 = "2023-08-17T13:19:36.563"
    DATA_SITUACAO_2023_08_17_1320 = "2023-08-17T13:20:55.113"
    DATA_SITUACAO_2023_08_17_1325 = "2023-08-17T13:25:18.753"
    DATA_SITUACAO_2023_08_17_1325707 = "2023-08-17T13:25:18.707"
    DATA_SITUACAO_2023_11_09 = "2023-11-09T19:47:32.76"
    DATA_SITUACAO_2023_12_01_1029 = "2023-12-01T10:29:04.48"
    DATA_SITUACAO_2023_12_01_1029387 = "2023-12-01T10:29:04.387"
    DATA_SITUACAO_2023_12_01_1031 = "2023-12-01T10:31:47.18"
    DATA_NASCIMENTO_2010_01_01 = "2010-01-01T00:00:00"
    DATA_PADRAO_0001_01_01 = "0001-01-01T00:00:00"
    DATA_PADRAO_2025_01_01 = "2025-01-01T00:00:00"
    FORMATO_ISO_MEIA_NOITE = "%Y-%m-%dT00:00:00"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsValidationErrors(Enum):
    CODIGO_EOL_ESCOLA_OBRIGATORIO = "`codigo_eol_escola` como query_param é obrigatório"
    PERMISSAO_NEGADA = "Você não tem permissão para executar essa ação."
    ESCOLHA_UMA_PLANILHA = "Escolha somente uma planilha."
    DIETA_ESPECIAL_PENDENTE = "Aluno já possui Solicitação de Dieta Especial pendente"
    CAMPO_OBRIGATORIO_EXCLAMACAO = "Este campo é obrigatório!"
    CAMPO_OBRIGATORIO_PONTO_FINAL = "Este campo é obrigatório."
    EXCLUSAO_SOMENTE_RASCUNHO = "Você só pode excluir quando o status for RASCUNHO."
    GUIA_DE_REMESSA_NAO_EXISTE = "Guia de remessa não existe."
    INFORMAR_NUMERO_REQUISICAO = (
        "É necessario informar o número da requisição ao qual a(s) guia(s) pertece(m)."
    )
    CAMPO_OBRIGATORIO_PARA_O_GRUPO = "Campo obrigatório para o grupo."

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class PayloadVariaveis(Enum):
    LOTES = "lotes[]"
    EDITAIS = "editais[]"
    ESCOLA_UUID = "escola__uuid[]"
    TIPO_CONTAGEM_ALIMENTACOES = "tipo_contagem_alimentacoes[]"
    LOTES_SELECIONADOS = "lotes_selecionados[]"
    TIPOS_UNIDADES = "tipos_unidades[]"
    DIRETORIAS_REGIONAIS = "diretorias_regionais[]"
    CLASSIFICACOES_SELECIONADAS = "classificacoes_selecionadas[]"
    TIPO_UNIDADE_UUID = "tipo_unidade__uuid[]"
    TIPOS_CONTAGEM_ALIMENTACAO = "tipos_contagem_alimentacao[]"
    PROTOCOLOS_PADRAO_SELECIONADOS = "protocolos_padrao_selecionados[]"
    PERIODOS_ESCOLARES_SELECIONADAS = "periodos_escolares_selecionadas[]"
    UNIDADES_EDUCACIONAIS_SELECIONADAS = "unidades_educacionais_selecionadas[]"
    UNIDADES_EDUCACIONAIS = "unidades_educacionais[]"
    TIPOS_UNIDADES_SELECIONADAS = "tipos_unidades_selecionadas[]"
    TIPOS_TURMAS = "tipos_turmas[]"
    TERCEIRIZADAS = "terceirizadas[]"
    STATUS_RECLAMACAO = "status_reclamacao[]"
    PERIODOS_ESCOLARES = "periodos_escolares[]"
    LOTE_UUID = "lote__uuid[]"
    EXCLUIR_TIPO_UNIDADE_UUID = "excluir_tipo_unidade__uuid[]"
    ALERGIAS_INTOLERANCIAS_SELECIONADAS = "alergias_intolerancias_selecionadas[]"
    TIPOS_ALIMENTACAO = "tipos_alimentacao[]"
    TIPO_CALENDARIO = "tipo_calendario[]"
    SOLICITACOES = "solicitacoes[]"
    MOTIVO = "motivo[]"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StatusProcessamentoArquivo(Enum):
    PENDENTE = "PENDENTE"
    SUCESSO = "SUCESSO"
    ERRO = "ERRO"
    PROCESSADO_COM_ERRO = "PROCESSADO_COM_ERRO"
    PROCESSANDO = "PROCESSANDO"
    REMOVIDO = "REMOVIDO"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class TIPOS_ALIMENTACAO(Enum):
    DESJEJUM = "Desjejum"
    COLACAO = "Colação"
    ALMOCO = "Almoço"
    REFEICAO = "Refeição"
    REFEICAO_DA_TARDE = "Refeição da Tarde"
    MERENDA_SECA = "Merenda seca"
    SOBREMESA = "Sobremesa"
    LANCHE = "Lanche"
    LANCHE_4H = "Lanche 4h"
    LANCHE_EMERGENCIAL = "Lanche Emergencial"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class TIPOS_GESTAO(Enum):
    TERC_TOTAL = "TERC TOTAL"
    MISTA = "MISTA"
    PARCEIRA = "PARCEIRA"
    DIRETA = "DIRETA"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsSearchHelpText(Enum):
    PESQUISA_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA = (
        "Pesquisa por: nome da escola, codigo eol da escola"
    )
    PESQUISA_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA_2 = (
        "Pesquisa por: nome da escola, código eol da escola"
    )
    PESQUISA_POR_NOME_DO_USUARIO_USERNAME_EMAIL_CPF_OU_RF = (
        "Pesquisa por: nome do usuário, username, email, CPF ou RF"
    )
    PESQUISA_POR_TITULO_DO_RECREIO_NAS_FERIAS = (
        "Pesquisa por: título do recreio nas férias"
    )
    PESQUISA_POR_UUID_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA = (
        "Pesquisa por: uuid, nome da escola, código eol da escola"
    )
    PESQUISAR_POR_UUID_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA = (
        "Pesquisar por: UUID, nome da escola, codigo eol da escola"
    )
    PESQUISAR_POR_UUID_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA_2 = (
        "Pesquisar por: UUID, nome da escola, código EOL da escola"
    )
    PESQUISE_POR_NOME_DA_ESCOLA_OU_CODIGO_EOL_DA_ESCOLA = (
        "Pesquise por: nome da escola ou código eol da escola"
    )
    PESQUISE_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA = (
        "Pesquise por: nome da escola, código eol da escola"
    )
    PESQUISE_POR_NOME_DA_ESCOLA_CODIGO_EOL_DA_ESCOLA_OU_PERIODO_ESCOLAR = (
        "Pesquise por: nome da escola, código eol da escola ou período escolar"
    )
    PESQUISE_POR_NOME_DO_ALUNO_CODIGO_EOL_DO_ALUNO_NOME_DA_ESCOLA_OU_CODIGO_EOL_DA_ESCOLA = "Pesquise por: nome do aluno, código eol do aluno, nome da escola ou código eol da escola"
    PESQUISE_POR_NOME_DO_ALUNO_NOME_DA_ESCOLA_OU_CODIGO_EOL_DO_ALUNO = (
        "Pesquise por: nome do aluno, nome da escola ou código eol do aluno"
    )
    PESQUISE_POR_NOME_DO_EQUIPAMENTO = "Pesquise por: nome do equipamento"
    PESQUISE_POR_NOME_DO_INSUMO = "Pesquise por: nome do insumo"
    PESQUISE_POR_NOME_DO_MOBILIARIO = "Pesquise por: nome do mobiliário"
    PESQUISE_POR_NOME_DO_PRODUTO = "Pesquise por: nome do produto"
    PESQUISE_POR_NOME_DO_PRODUTO_NUMERO_CATEGORIA_NOME_DA_EMPRESA_NOME_DO_FABRICANTE = "Pesquise por: nome do produto, número, categoria, nome da empresa, nome do fabricante"
    PESQUISE_POR_NOME_DO_REPARO_E_ADAPTACAO = "Pesquise por: nome do reparo e adaptação"
    PESQUISE_POR_NOME_DO_UTENSILIO_DE_COZINHA = (
        "Pesquise por: nome do utensílio de cozinha"
    )
    PESQUISE_POR_NOME_DO_UTENSILIO_DE_MESA = "Pesquise por: nome do utensílio de mesa"
    PESQUISE_POR_NUMERO_DA_CLAUSULA = "Pesquise por: número da cláusula"
    PESQUISE_POR_NUMERO_DO_EDITAL = "Pesquise por: número do edital"
    PESQUISE_POR_NUMERO_DO_EDITAL_TITULO = "Pesquise por: número do edital, título"
    PESQUISE_POR_NUMERO_DO_EDITAL_EMAIL_NOME_DO_USUARIO_DO_FORMULARIO = (
        "Pesquise por: número do edital; (email, nome) do usuário do formulário."
    )
    PESQUISE_POR_TITULO = "Pesquise por: título"
    PESQUISE_POR_INICIAIS_OU_NOME_DO_TIPO_DE_UNIDADE_NUMERO_DO_EDITAL_TIPO_DE_SOBREMESA = "Pesquise por: iniciais ou nome do tipo de unidade, número do edital, tipo de sobremesa"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsCaminhoModelos(Enum):
    MODEL_PERFIL = "perfil.Perfil"
    MODEL_VINCULO = "perfil.Vinculo"
    MODEL_TERCEIRIZADA = "terceirizada.Terceirizada"
    MODEL_ESCOLA = "escola.Escola"
    MODEL_DIRETORIA_REGIONAL = "escola.DiretoriaRegional"
    MODEL_LOTE = "escola.Lote"
    MODEL_USUARIO = "perfil.Usuario"
    MODEL_EDITAL = "terceirizada.Edital"
    MODEL_PERIODOESCOLAR = "escola.PeriodoEscolar"
    MODEL_CONTATO = "dados_comuns.Contato"
    MODEL_TIPOUNIDADEESCOLAR = "escola.TipoUnidadeEscolar"
    MODEL_ALIMENTO = "dieta_especial.Alimento"
    MODEL_TIPOALIMENTACAO = "cardapio.TipoAlimentacao"
    MODEL_FAIXAETARIA = "escola.FaixaEtaria"
    MODEL_VINCULOTIPOALIMENTACAOCOMPERIODOESCOLARETIPOUNIDADEESCOLAR = (
        "cardapio.VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar"
    )
    MODEL_ALUNO = "escola.Aluno"
    MODEL_ESCOLAPERIODOESCOLAR = "escola.EscolaPeriodoEscolar"
    MODEL_DIACALENDARIO = "escola.DiaCalendario"
    MODEL_CONTRATO = "terceirizada.Contrato"
    MODEL_ALUNOSMATRICULADOSPERIODOESCOLA = "escola.AlunosMatriculadosPeriodoEscola"
    MODEL_TIPOCONTAGEMALIMENTACAO = "medicao_inicial.TipoContagemAlimentacao"
    MODEL_PRODUTO = "produto.Produto"
    MODEL_ETAPASDOCRONOGRAMA = "pre_recebimento.EtapasDoCronograma"
    MODEL_QUANTIDADEPORPERIODO = "inclusao_alimentacao.QuantidadePorPeriodo"
    MODEL_UNIDADEMEDIDA = "pre_recebimento.UnidadeMedida"
    MODEL_MOTIVOSUSPENSAO = "cardapio.MotivoSuspensao"
    MODEL_MARCA = "produto.Marca"
    MODEL_FICHATECNICADOPRODUTO = "pre_recebimento.FichaTecnicaDoProduto"
    MODEL_CRONOGRAMA = "pre_recebimento.Cronograma"
    MODEL_DIALETIVOSIGPAE = "escola.DiaLetivoSIGPAE"
    MODEL_SOLICITACAOMEDICAOINICIAL = "medicao_inicial.SolicitacaoMedicaoInicial"
    MODEL_SOLICITACAOKITLANCHECEIAVULSA = "kit_lanche.SolicitacaoKitLancheCEIAvulsa"
    MODEL_KITLANCHE = "kit_lanche.KitLanche"
    MODEL_RESPONSAVEL = "medicao_inicial.Responsavel"
    MODEL_LOGALUNOSMATRICULADOSPERIODOESCOLA = (
        "escola.LogAlunosMatriculadosPeriodoEscola"
    )
    MODEL_MOTIVOINCLUSAOCONTINUA = "inclusao_alimentacao.MotivoInclusaoContinua"
    MODEL_INCLUSAOALIMENTACAOCONTINUA = (
        "inclusao_alimentacao.InclusaoAlimentacaoContinua"
    )
    MODEL_GRUPOUNIDADEESCOLAR = "escola.GrupoUnidadeEscolar"
    MODEL_PROGRAMACAOENTREGASEMANAL = "pre_recebimento.ProgramacaoEntregaSemanal"
    MODEL_HOMOLOGACAOPRODUTO = "produto.HomologacaoProduto"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsVerboseNameModels(Enum):
    ABREVIACAO = "Abreviação"
    ACAO = "ação"
    ACEITA_MULTIPLAS_RESPOSTAS = "Aceita múltiplas respostas?"
    ACESSO_MODULO_MEDICAO_DESDE = "Acesso módulo medição desde"
    ACOMPANHOU_A_VISITA = "Acompanhou a visita?"
    ADITIVOS = "Aditivos"
    ALTERADO_EM = "Alterado em"
    ALTERADO_POR = "Alterado por"
    ALTERAR_DIA = "Alterar dia"
    ALUNOS_DA_CEMEI = "Alunos da CEMEI"
    ALUNO_NO_PERIODO_PARCIAL_A_PARTIR_DE = "Aluno no período parcial a partir de"
    ANEXO = "Anexo"
    APROVADO = "Aprovado"
    ARQUIVO = "Arquivo"
    ATIVO = "Ativo?"
    BAIRRO = "Bairro"
    BAIRRO_DA_UNIDADE = "Bairro da unidade"
    CAPACIDADE_DA_EMBALAGEM = "Capacidade da Embalagem"
    CARACTERISTICAS_DOS_ALIMENTOS = "Características dos alimentos"
    CARGO = "Cargo"
    CATEGORIA = "Categoria"
    CATEGORIA_DA_OCORRENCIA = "Categoria da Ocorrência"
    CEP = "CEP"
    CEP_DA_UNIDADE = "CEP da unidade"
    CIDADE = "Cidade"
    CIDADE_DA_UNIDADE = "Cidade da unidade"
    CNPJ = "CNPJ"
    CODIGO = "Código"
    CODIGOS_CODAE_VINCULADOS = "Códigos Codae Vinculados?"
    CODIGO_CODAE = "Código CODAE"
    CODIGO_DA_UNIDADE = "Código da unidade"
    CODIGO_EOL = "Código EOL"
    CODIGO_EOL_ALUNO = "Código EOL aluno"
    CODIGO_EOL_DA_ESCOLA = "Codigo EOL da escola"
    CODIGO_EOL_ESCOLA_DESTINO = "Código EOL escola destino"
    CODIGO_EOL_ESCOLA_ORIGEM = "Código EOL escola origem"
    CODIGO_PAPA = "Código papa"
    CODIGO_SUPRIMENTO = "Código suprimento"
    COMPLEMENTO = "Complemento"
    COMPLEMENTO_DO_STATUS = "Complemento do status"
    COMPONENTES_DO_PRODUTO = "Componentes do Produto"
    COM_OCORRENCIAS = "Com ocorrências?"
    CONDICOES_DE_CONSERVACAO = "Condições de conservação"
    CONDICOES_DE_TRANSPORTE = "Condições de Transporte"
    CONTATO_NA_UNIDADE = "Contato na unidade"
    CONTEM_GLUTEN = "Contém glúten?"
    CONTEM_LACTOSE = "Contém lactose?"
    CONTRATO = "Contrato"
    CORRECAO_SOLICITADA = "Correção Solicitada"
    CRIADO_EM = "criado em"
    CRONOGRAMA = "Cronograma"
    CRONOGRAMAS = "Cronogramas"
    CRONOGRAMA_MENSAL = "Cronograma Mensal"
    CRONOGRAMA_SEMANAL = "Cronograma Semanal"
    CUSTO_UNITARIO_DO_PRODUTO = "Custo Unitário do Produto"
    DATA = "Data"
    DATA_DA_ENTREGA = "Data da entrega"
    DATA_DA_INTERRUPCAO = "Data da Interrupção"
    DATA_DA_PROPOSTA = "Data da proposta"
    DATA_DE_ENTREGA = "Data de Entrega"
    DATA_DE_INVERSAO = "Data de inversão"
    DATA_DE_RECEBIMENTO = "Data de recebimento"
    DATA_E_HORA_DO_ENCERRAMENTO = "Data e hora do encerramento"
    DATA_FABRICACAO = "Data Fabricação"
    DATA_FIM = "Data Fim"
    DATA_FINAL = "Data final"
    DATA_FINAL_DO_LOTE = "Data Final do Lote"
    DATA_INICIAL = "Data inicial"
    DATA_INICIO = "Data Início"
    DATA_MAXIMA_DE_RECEBIMENTO = "Data Máxima de Recebimento"
    DATA_PARA_INVERSAO = "Data para inversão"
    DATA_PROGRAMADA = "Data Programada"
    DATA_S_DE_FABRICACAO_OBSERVADA_S_ESTAO_DE_ACORDO = (
        "Data(s) de Fabricação Observada(s) estão de acordo?"
    )
    DATA_S_DE_VALIDADES_OBSERVADA_S_ESTAO_DE_ACORDO = (
        "Data(s) de Validades Observada(s) estão de acordo?"
    )
    DATA_VALIDADE = "Data Validade"
    DESCRICAO = "Descricao"
    DESCRICAO_2 = "Descrição"
    DESCRICAO_CICLO = "Descrição ciclo"
    DESCRICAO_DA_CLAUSULA_ITEM = "Descrição da Cláusula/Item"
    DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_FABRICACAO = (
        "Descrição da divergência nas Data(s) de Fabricação"
    )
    DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_VALIDADES = (
        "Descrição da divergência nas Data(s) de Validades"
    )
    DESCRICAO_DA_DIVERGENCIA_NOS_LOTE_S_DO_FABRICANTE = (
        "Descrição da divergência nos Lote(s) do Fabricante"
    )
    DESCRICAO_DA_EMBALAGEM = "Descrição da Embalagem"
    DESCRICAO_DO_DOCUMENTO = "Descrição do Documento"
    DESCRICAO_DO_EVENTO = "Descrição do Evento"
    DESCRICAO_DO_METODO_DE_CONTAGEM = "Descrição do método de contagem"
    DESCRICAO_DO_MOTIVO = "Descrição do Motivo"
    DESCRICAO_ETAPA = "Descrição etapa"
    DETALHAR_LACTOSE = "Detalhar Lactose"
    DE_DESCONTO = "% de Desconto"
    DE_DESCONTO_2 = "% de desconto"
    DIETA_PARA_RECREIO_NAS_FERIAS = "Dieta para Recreio nas Férias"
    DOCUMENTO_DE_RECEBIMENTO = "Documento de Recebimento"
    EDITAL_NO = "Edital No"
    EMBALAGEM_PRIMARIA = "Embalagem Primária"
    EMBALAGEM_SECUNDARIA = "Embalagem Secundária"
    EMBALAGENS_DE_ACORDO_COM_ANEXO = "Embalagens de Acordo com Anexo?"
    EMPRESA = "Empresa"
    ENCERRADO = "Encerrado?"
    ENDERECO = "Endereco"
    ENDERECO_2 = "Endereço"
    ENDERECO_DA_UNIDADE = "Endereço da unidade"
    ENVASADOR_DISTRIBUIDOR = "Envasador/Distribuidor"
    EQUIPAMENTOS = "Equipamentos"
    ESPECIE_OU_VARIEDADE_CULTIVADA = "Espécie ou Variedade Cultivada"
    ESTADO = "Estado"
    ESTADO_DA_UNIDADE = "Estado da unidade"
    ESTADO_HIGIENICO_SANITARIO_ADEQUADO = "Estado Higiênico-Sanitário adequado?"
    ESTA_CREDENCIADO = "Está credenciado?"
    ESTA_SUSPENSO = "Esta suspenso?"
    ETAPA = "Etapa"
    ETAPA_DO_CRONOGRAMA = "Etapa do Cronograma"
    E_ADMINISTRADOR_POR_PARTE_DAS_TERCEIRIZADAS = (
        "É Administrador por parte das Terceirizadas?"
    )
    E_DIA_LETIVO = "É dia Letivo?"
    E_IMR = "É IMR?"
    E_MAIL = "E-mail"
    E_NUTRICIONISTA = "É nutricionista?"
    E_ORGANICO = "É orgânico?"
    E_PARA_ALUNOS_COM_DIETA_ESPECIAL = "É para alunos com dieta especial"
    FICHA_DE_RECEBIMENTO = "Ficha de Recebimento"
    FISCAL_1 = "Fiscal 1"
    FISCAL_2 = "Fiscal 2"
    FISCAL_3 = "Fiscal 3"
    FOI_LIDO = "Foi Lido?"
    FOI_RESOLVIDO = "Foi resolvido?"
    FOI_VISTO = "Foi visto?"
    FORMULARIO_DE_OCORRENCIAS = "Formulário de Ocorrências"
    GERA_NOTIFICACAO = "Gera Notificação?"
    HABILITACAO = "Habilitação"
    HORA = "Hora"
    HORA_DA_TENTATIVA_DE_ENTREGA = "Hora da tentativa de entrega"
    HORA_DO_RECEBIMENTO = "Hora do recebimento"
    HOUVE_OCORRENCIA = "Houve Ocorrência?"
    INFORMACAO_NUTRICIONAL_FIXA = "Informação Nutricional Fixa"
    INFORMACOES_ADICIONAIS = "Informações Adicionais"
    INFORMACOES_DE_ARMAZENAMENTO = "Informações de Armazenamento"
    INGREDIENTES_ADITIVOS_ALERGENICOS = "Ingredientes/aditivos alergênicos"
    INSUMOS = "Insumos"
    ITEM_DA_CLAUSULA = "Item da Cláusula"
    JUSTIFICATIVA = "Justificativa"
    JUSTIFICATIVA_DA_ALTERACAO = "Justificativa da Alteração"
    JUSTIFICATIVA_DE_ACEITE_PELA_DILOG = "Justificativa de aceite pela dilog"
    JUSTIFICATIVA_DE_NEGACAO_PELA_DILOG = "Justificativa de negacao pela dilog"
    JUSTIFICATIVA_DE_SOLICITACAO_PELO_DISTRIBUIDOR = (
        "Justificativa de solicitação pelo distribuidor"
    )
    JUSTIFICATIVA_DE_SOLICITACAO_PELO_FORNECEDOR = (
        "Justificativa de solicitação pelo fornecedor"
    )
    LINK = "Link"
    LOGRADOURO = "Logradouro"
    LOGS_DE_MATRICULADOS_DIETAS_AUTORIZADAS_ETC_FORAM_SALVOS = (
        "Logs de matriculados, dietas autorizadas, etc foram salvos?"
    )
    LOTE_S_DO_FABRICANTE_OBSERVADO_S_ESTAO_DE_ACORDO = (
        "Lote(s) do Fabricante Observado(s) estão de acordo?"
    )
    MAIOR_NO_DE_FREQUENTES_NO_PERIODO = "Maior Nº de Frequentes no Período"
    MARCAR_COMO_CONFERIDO = "Marcar como conferido?"
    MATERIAL_DA_EMBALAGEM_PRIMARIA = "Material da Embalagem Primária"
    MENSAGEM_ERRO = "Mensagem erro"
    MES_PROGRAMADO = "Mês Programado"
    MOBILIARIOS = "Mobiliários"
    MODO_DE_PREPARO_DO_PRODUTO = "Modo de Preparo do Produto"
    MOTIVO_DA_INTERRUPCAO = "Motivo da Interrupção"
    MOTIVO_DO_INSUCESSO = "Motivo do insucesso"
    NOME = "Nome"
    NOME_COMPLETO_DO_ALUNO = "Nome Completo do Aluno"
    NOME_COMPLETO_DO_PESCRITOR_DA_RECEITA = "Nome completo do pescritor da receita"
    NOME_COMPLETO_DO_RESPONSAVEL_TECNICO = "Nome completo do Responsável Técnico"
    NOME_DA_ESCOLA_DESTINO = "Nome da Escola destino"
    NOME_DA_ESCOLA_ORIGEM = "Nome da Escola origem"
    NOME_DA_NUTRICIONISTA_RT_DA_EMPRESA = "Nome da Nutricionista RT da Empresa"
    NOME_DA_UNIDADE = "Nome da unidade"
    NOME_DO_ALIMENTO_PRODUTO = "Nome do alimento/produto"
    NOME_DO_ALUNO = "Nome do Aluno"
    NOME_DO_ARQUIVO = "Nome do arquivo"
    NOME_DO_MOTORISTA = "Nome do motorista"
    NOME_DO_PROTOCOLO = "Nome do Protocolo"
    NOME_FANTASIA = "Nome fantasia"
    NOTIFICACAO_ASSINADA = "Notificação Assinada"
    NO_DA_ATA = "No da Ata"
    NO_DA_CHAMADA_PUBLICA = "Nº da Chamada Pública"
    NO_DE_PALETES = "Nº de Paletes"
    NO_DO_CONTRATO = "No do contrato"
    NO_DO_LOTE_ARMAZENAGEM = "Nº do Lote Armazenagem"
    NO_DO_PREGAO_ELETRONICO = "Nº do Pregão Eletrônico"
    NO_DO_PROCESSO_SEI = "Nº do Processo SEI"
    NO_DO_REGISTRO_DO_ROTULO = "Nº do Registro do Rótulo"
    NO_DO_REGISTRO_EM_ORGAO_COMPETENTE = "Nº do Registro em Órgão Competente"
    NO_DO_VEICULO = "Nº do Veículo"
    NO_SIF_SISBI_OU_SISP = "Nº SIF, SISBI ou SISP"
    NUMERO = "Número"
    NUMERO_DA_CLAUSULA = "Número da Cláusula"
    NUMERO_DA_CLAUSULA_ITEM = "Número da Cláusula/Item"
    NUMERO_DA_FICHA_TECNICA = "Número da Ficha Técnica"
    NUMERO_DA_GUIA = "Número da guia"
    NUMERO_DA_NOTA = "Número da Nota"
    NUMERO_DA_NOTIFICACAO = "Número da Notificação"
    NUMERO_DA_SOLICITACAO = "Número da solicitação"
    NUMERO_DA_UNIDADE = "Número da unidade"
    NUMERO_DO_CRONOGRAMA = "Número do Cronograma"
    NUMERO_DO_CRONOGRAMA_SEMANAL = "Número do Cronograma Semanal"
    NUMERO_DO_EMPENHO = "Número do Empenho"
    NUMERO_DO_EMPENHO_2 = "Número do empenho"
    NUMERO_DO_LAUDO = "Número do Laudo"
    NUTRICIONISTA_CRN = "Nutricionista crn"
    OBJETO_RESUMIDO = "objeto resumido"
    OBSERVACAO = "Observação"
    OBSERVACOES = "Observações"
    OBSERVACOES_ALTERACAO = "Observações Alteração"
    OPCAO = "Opção"
    ORIENTACOES_GERAIS = "Orientações Gerais"
    OUTRAS_INFORMACOES = "Outras Informações"
    OUTRO_MOTIVO = "Outro Motivo"
    OUTRO_MOTIVO_2 = "Outro motivo"
    O_PRODUTO_E_LIQUIDO = "O produto é líquido?"
    PARTE = "Parte"
    PENALIDADE_DO_ITEM = "Penalidade do Item"
    PERGUNTA = "Pergunta"
    PERGUNTA_OBRIGATORIA = "Pergunta Obrigatória?"
    PERIODO_DA_VISITA = "Período da Visita"
    PESO_DA_EMBALAGEM_PRIMARIA_1 = "Peso da Embalagem Primária (1)"
    PESO_DA_EMBALAGEM_PRIMARIA_2 = "Peso da Embalagem Primária (2)"
    PESO_DA_EMBALAGEM_PRIMARIA_3 = "Peso da Embalagem Primária (3)"
    PESO_DA_EMBALAGEM_PRIMARIA_4 = "Peso da Embalagem Primária (4)"
    PLACA_DO_VEICULO = "Placa do veículo"
    PODE_CONTER_ALERGENICOS = "Pode conter alergênicos?"
    PONTUACAO_IMR = "Pontuação (IMR)"
    PONTUACAO_MAXIMA = "Pontuação Máxima"
    PONTUACAO_MINIMA = "Pontuação Mínima"
    PORCAO = "Porção"
    PORCAO_NUTRICIONAL = "Porção nutricional"
    PORQUE_FOI_SUSPENSO_INDIVIDUALMENTE = "Porque foi suspenso individualmente"
    POSICAO = "Posição"
    POSSUI_ALUNOS_PERIODO_PARCIAL = "Possui alunos periodo parcial?"
    PRAZO_DE_VALIDADE = "Prazo de Validade"
    PRAZO_DE_VALIDADE_2 = "Prazo de validade"
    PRAZO_DE_VALIDADE_DESCONGELAMENTO = "Prazo de Validade Descongelamento"
    PRAZO_MAXIMO_PARA_RECEBIMENTO = "Prazo Máximo para Recebimento"
    PREVISAO_CONTRATUAL = "Previsão Contratual"
    PROCESSO_ADMINISTRATIVO = "Processo Administrativo"
    PROGRAMA = "Programa"
    PROVENIENTE_DE_IMPORTACAO = "Proveniente de importacao?"
    QTDE_TOTAL_DO_EMPENHO = "Qtde. Total do Empenho"
    QTD_TOTAL_DE_GUIAS_NA_REQUISICAO = "Qtd total de guias na requisição"
    QTD_TOTAL_PROGRAMADA = "Qtd Total Programada"
    QUANTIDADE = "Quantidade"
    QUANTIDADE_A_RECEBER_FALTANTE = "Quantidade a receber faltante"
    QUANTIDADE_DA_ENTREGA = "Quantidade da Entrega"
    QUANTIDADE_DE_ALUNOS = "Quantidade de alunos"
    QUANTIDADE_DE_ALUNOS_ALTERADA = "Quantidade de alunos alterada"
    QUANTIDADE_DE_ALUNOS_ANTERIOR = "Quantidade de alunos anterior"
    QUANTIDADE_DE_ALUNOS_ANTES = "Quantidade de alunos antes"
    QUANTIDADE_DE_ALUNOS_ATUAL = "Quantidade de alunos atual"
    QUANTIDADE_DE_EMBALAGENS_DA_NOTA_FISCAL = "Quantidade de Embalagens da Nota Fiscal"
    QUANTIDADE_DE_EMBALAGENS_RECEBIDAS = "Quantidade de Embalagens Recebidas"
    QUANTIDADE_RECEBIDA = "Quantidade Recebida"
    QUANTIDADE_RECEBIDO = "Quantidade recebido"
    QUANTIDADE_TOTAL_RECEBIDA = "Quantidade Total Recebida"
    QUANTIDADE_VOLUME = "Quantidade/Volume"
    QUESTAO = "Questão"
    QUESTAO_DE_CONFERENCIA = "Questão de Conferência"
    QUESTOES_REFERENTES_A_EMBALAGEM_PRIMARIA = (
        "Questões referentes à Embalagem Primária"
    )
    QUESTOES_REFERENTES_A_EMBALAGEM_SECUNDARIA = (
        "Questões referentes à Embalagem Secundária"
    )
    RAZAO_SOCIAL = "Razao social"
    RECLAMACAO = "Reclamação"
    REGISTRO_DO_ORGAO_COMPETENTE = "Registro do órgão competente"
    REGISTRO_FUNCIONAL_DO_NUTRICIONISTA = "Registro funcional do nutricionista"
    REGISTRO_FUNCIONAL_DO_PESCRITOR_DA_RECEITA = (
        "Registro funcional do pescritor da receita"
    )
    RELACAO = "Relação"
    REPAROS_E_ADAPTACOES = "Reparos e Adaptações"
    REPRESENTANTE_CONTATO_EMAIL = "Representante contato (email)"
    REPRESENTANTE_CONTATO_TELEFONE = "Representante contato (telefone)"
    REPRESENTANTE_LEGAL = "Representante legal"
    RESPONSAVEL = "Responsável"
    RESPONSAVEL_CARGO = "Responsável cargo"
    RESPONSAVEL_CONTATO_EMAIL = "Responsável contato (email)"
    RESPONSAVEL_CONTATO_TELEFONE = "Responsável contato (telefone)"
    RESPOSTA = "Resposta"
    RESPOSTA_SIM_NAO = "Resposta (Sim/Não)"
    RESPOSTA_SIM_OU_NAO = "Resposta - Sim ou Não"
    RF_CRN_CRF = "RF/CRN/CRF"
    ROTULO_LEGIVEL = "Rotulo Legível?"
    SEQUENCIA_DE_ENVIO_ATRIBUIDA_PELO_PAPA = "Sequência de envio atribuída pelo papa"
    SEQUENCIA_DE_ENVIO_ATRIBUIDO_PELO_PAPA = "Sequência de envio atribuído pelo papa"
    SISTEMA_DE_VEDACAO_DA_EMBALAGEM_SECUNDARIA = (
        "Sistema de Vedação da Embalagem Secundária"
    )
    SOLICITACAO_MEDICAO_INICIAL = "Solicitação Medição Inicial"
    STATUS = "Status"
    STATUS_2 = "status"
    STATUS_DA_ANALISE = "Status da análise"
    STATUS_DA_GUIA = "Status da guia"
    STATUS_DA_REQUISICAO = "Status da requisição"
    SUPER_USUARIO_NA_INSTIUICAO = "Super usuario na instiuição?"
    SUSPENSO_EM = "Suspenso em"
    TELEFONE = "Telefone"
    TELEFONE_DA_UNIDADE = "Telefone da unidade"
    TEMPERATURA_DA_AREA_DE_RECEBIMENTO_C = "Temperatura da Área de Recebimento (°C)"
    TEMPERATURA_DE_CONGELAMENTO_DO_PRODUTO = "Temperatura de Congelamento do Produto"
    TEMPERATURA_DO_PRODUTO_C = "Temperatura do Produto (°C)"
    TEMPERATURA_INTERNA_DO_VEICULO_PARA_TRANSPORTE = (
        "Temperatura Interna do Veículo para Transporte"
    )
    TEM_ADITIVOS_ALERGENICOS = "Tem aditivos alergênicos"
    TEM_GLUTEN = "Tem Glúten?"
    TERMO_DE_RECEBIMENTO_DEFINITIVO = "Termo de Recebimento Definitivo"
    TEXTO_DO_TERMO = "Texto do Termo"
    TIPO = "Tipo"
    TIPO_DE_CALENDARIO = "Tipo de Calendário"
    TIPO_DE_CONTRATACAO = "Tipo de contratação"
    TIPO_DE_EMPENHO = "Tipo de empenho"
    TIPO_DE_ENTREGA = "Tipo de Entrega"
    TIPO_DE_GRAVIDADE = "Tipo de Gravidade"
    TIPO_DE_LANCAMENTO = "Tipo de lançamento"
    TIPO_DE_OCORRENCIA = "Tipo de Ocorrência"
    TIPO_DE_PENALIDADE = "Tipo de Penalidade"
    TIPO_DE_PRODUTO = "tipo de produto"
    TIPO_DE_RESPOSTA = "Tipo de resposta"
    TIPO_DO_PRODUTO = "Tipo do Produto"
    TITULO = "Titulo"
    TITULO_2 = "Título"
    TOLERANCIA = "Tolerância"
    TOTAL_DE_EMBALAGENS = "Total de Embalagens"
    UNIDADE_CASEIRA = "Unidade Caseira"
    UNIDADE_DE_MEDIDA = "Unidade de Medida"
    UNIDADE_DE_MEDIDA_CASEIRA = "Unidade de Medida Caseira"
    UNIDADE_NUTRICIONAL = "Unidade nutricional"
    USUARIO = "Usuário"
    UTENSILIOS_DE_COZINHA = "Utensílios de Cozinha"
    UTENSILIOS_DE_MESA = "Utensílios de Mesa"
    VALOR_DO_CAMPO = "Valor do Campo"
    VALOR_DO_CONTRATO = "Valor do Contrato"
    VISAO = "Visão"
    VOLUME = "Volume"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class TIPOS_UNIDADE_ESCOLAR(Enum):
    EMEF = "EMEF"
    CEU_EMEF = "CEU EMEF"
    EMEFM = "EMEFM"
    EMEF_P_FOM = "EMEF P FOM"
    CEU_GESTAO = "CEU GESTAO"
    EMEI = "EMEI"
    CEU_EMEI = "CEU EMEI"
    EMEI_P_FOM = "EMEI P FOM"
    CEI_DIRET = "CEI DIRET"
    CEI_CEU = "CEI CEU"
    CEU_CEI = "CEU CEI"
    CCI = "CCI"
    CCI_CIPS = "CCI/CIPS"
    CEI = "CEI"
    CEMEI = "CEMEI"
    CEU_CEMEI = "CEU CEMEI"
    EMEBS = "EMEBS"
    CIEJA = "CIEJA"
    CMCT = "CMCT"
    ESC_PART = "ESC.PART."

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


TIPO_UNIDADE_CEI_DIRET = TIPOS_UNIDADE_ESCOLAR.CEI_DIRET.value
EMAIL_TESTE = "test@test.com"
NOME_ESCOLA_EMEBS = "Escola EMEBS"
NOME_LOTE_EMEBS = "Lote EMEBS"
NOME_ESCOLA_EMEF = "Escola EMEF"
NOME_LOTE_EMEF = "LOTE EMEF"
NOME_ESCOLA_CEU_GESTAO = "Escola CEU GESTAO"
NOME_LOTE_CEU_GESTAO = "LOTE CEU GESTAO"
NOME_ESCOLA_CEI_DIRET = "Escola CEI DIRET"
NOME_LOTE_CEI_DIRET = "LOTE CEI DIRET"
NOME_ESCOLA_CEMEI = "Escola CEMEI"
NOME_LOTE_CEMEI = "LOTE CEMEI"
NOME_PROTOCOLO_PLANILHA = "nome protocolo na planilha"
CHAVE_UUID = "UUID"
CHAVE_NOME_ESCOLA = "NOME ESCOLA"
CHAVE_COD_EOL_ESCOLA = "COD EOL ESCOLA"
CHAVE_NOME_ALUNO = "NOME ALUNO"
CHAVE_COD_EOL_ALUNO = "COD EOL ALUNO"
CHAVE_LOTE = "LOTE"
CHAVE_NOME_PROTOCOLO_IMPORTADO_DIETA = "NOME PROTOCOLO IMPORTADO DIETA"
CHAVE_NOME_PROTOCOLO_DB = "NOME PROTOCOLO NO DB"


PERIODOS_INCLUSAO_MOTIVO_ESPECIFICO = ["MANHA", "TARDE", "NOITE", "INTEGRAL"]


TRADUCOES_FERIADOS = {
    "New year": "Ano novo",
    "Anniversary of the city of São Paulo": "Aniversário da cidade de São Paulo",
    "Carnaval": "Carnaval",
    "Sexta-feira da Paixão": "Sexta-feira da Paixão",
    "Easter Sunday": "Domingo de Páscoa",
    "Tiradentes' Day": "Tiradentes",
    "Labour Day": "Dia do Trabalhador",
    "Corpus Christi": "Corpus Christi",
    "Constitutional Revolution of 1932": "Revolução Constitucionalista de 1932",
    "Independence Day": "Dia da Independência do Brasil",
    "Our Lady of Aparecida": "Dia de Nossa Senhora de Aparecida",
    "All Souls' Day": "Dia de Finados",
    "Republic Day": "Dia da Proclamação da República",
    "Dia da Consciência Negra": "Dia da Consciência Negra",
    "Christmas Day": "Natal",
}

#
# LITERAIS REUTILIZÁVEIS (evitam duplicação de strings)
#

DESCRICAO_SUSPENSAO_ALIMENTACAO_CEI = "Suspensão de Alimentação de CEI"
FORMATO_DATA_BRASILEIRO = "%d/%m/%Y"
FORMATO_DATA_HORA_BRASILEIRO = "%d/%m/%Y - %H:%M"
EMAIL_ADMIN = "admin@admin.com"
TEMPLATE_FLUXO_AUTORIZAR_NEGAR_CANCELAR = "fluxo_autorizar_negar_cancelar.html"
TEMPLATE_FLUXO_CODAE_AUTORIZA_OU_NEGA = "fluxo_codae_autoriza_ou_nega.html"
MODULO_GESTAO_PRODUTO = "Gestão de Produto"
MODULO_GESTAO_ALIMENTACAO = "Gestão de Alimentação"
MODULO_DIETA_ESPECIAL = "Dieta Especial"
CRIADO_EM = "Criado em"
STATUS_ENVIADO_PARA_ANALISE = "Enviado para Análise"
EMAIL_ASSUNTO_STATUS_SOLICITACAO = "[SIGPAE] Status de solicitação - "
RELATED_NAME_RASTRO_TERCEIRIZADA = "%(app_label)s_%(class)s_rastro_terceirizada"
RELATED_NAME_RASTRO_LOTE = "%(app_label)s_%(class)s_rastro_lote"
RELATED_NAME_RASTRO_DRE = "%(app_label)s_%(class)s_rastro_dre"
RELATED_NAME_RASTRO_ESCOLA = "%(app_label)s_%(class)s_rastro_escola"
MENSAGEM_SOLICITACAO_GERACAO_ARQUIVO = (
    "Solicitação de geração de arquivo recebida com sucesso."
)
ESCREVENDO = "Escrevendo..."
