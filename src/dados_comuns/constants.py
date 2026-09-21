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

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsValidationErrors(Enum):
    CODIGO_EOL_ESCOLA_OBRIGATORIO = "`codigo_eol_escola` como query_param é obrigatório"
    PERMISSAO_NEGADA = "Você não tem permissão para executar essa ação."
    ESCOLHA_UMA_PLANILHA = "Escolha somente uma planilha."
    DIETA_ESPECIAL_PENDENTE = "Aluno já possui Solicitação de Dieta Especial pendente"

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

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


TIPO_UNIDADE_CEI_DIRET = TIPOS_UNIDADE_ESCOLAR.CEI_DIRET.value
MODEL_PERFIL = "perfil.Perfil"
MODEL_VINCULO = "perfil.Vinculo"
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

TIPO_ALIMENTACAO = "cardapio.TipoAlimentacao"
PERIODO_ESCOLAR = "escola.PeriodoEscolar"
MODEL_TERCEIRIZADA = "terceirizada.Terceirizada"
MODEL_ESCOLA = "escola.Escola"
MODEL_DIRETORIA_REGIONAL = "escola.DiretoriaRegional"
MODEL_LOTE = "escola.Lote"
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
MODEL_USUARIO = "perfil.Usuario"
STATUS_ENVIADO_PARA_ANALISE = "Enviado para Análise"
EMAIL_ASSUNTO_STATUS_SOLICITACAO = "[SIGPAE] Status de solicitação - "
RELATED_NAME_RASTRO_TERCEIRIZADA = "%(app_label)s_%(class)s_rastro_terceirizada"
RELATED_NAME_RASTRO_LOTE = "%(app_label)s_%(class)s_rastro_lote"
RELATED_NAME_RASTRO_DRE = "%(app_label)s_%(class)s_rastro_dre"
RELATED_NAME_RASTRO_ESCOLA = "%(app_label)s_%(class)s_rastro_escola"
MENSAGEM_SOLICITACAO_GERACAO_ARQUIVO = (
    "Solicitação de geração de arquivo recebida com sucesso."
)
