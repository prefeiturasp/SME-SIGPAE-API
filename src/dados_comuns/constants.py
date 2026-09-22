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
    FORMATO_ISO_MEIA_NOITE = "%Y-%m-%dT00:00:00"

    @classmethod
    def choices(cls):
        return [(key.value, key.name) for key in cls]


class StringsValidationErrors(Enum):
    CODIGO_EOL_ESCOLA_OBRIGATORIO = "`codigo_eol_escola` como query_param é obrigatório"
    PERMISSAO_NEGADA = "Você não tem permissão para executar essa ação."
    ESCOLHA_UMA_PLANILHA = "Escolha somente uma planilha."
    DIETA_ESPECIAL_PENDENTE = "Aluno já possui Solicitação de Dieta Especial pendente"
    CAMPO_OBRIGATORIO = "Este campo é obrigatório!"

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
    DE_DESCONTO = "% de Desconto"
    DE_DESCONTO_2 = "% de desconto"
    ABREVIACAO = "Abreviação"
    ACEITA_MULTIPLAS_RESPOSTAS = "Aceita múltiplas respostas?"
    ACESSO_MODULO_MEDICAO_DESDE = "Acesso módulo medição desde"
    ACOMPANHOU_A_VISITA = "Acompanhou a visita?"
    ADITIVOS = "Aditivos"
    ALIMENTACAO_DE_LANCAMENTO_ESPECIAL = "Alimentação de Lançamento Especial"
    ALIMENTACOES_DE_LANCAMENTOS_ESPECIAIS = "Alimentações de Lançamentos Especiais"
    ALIMENTO = "Alimento"
    ALIMENTOS = "Alimentos"
    ALTERADO_EM = "Alterado em"
    ALTERADO_POR = "Alterado por"
    ALTERAR_DIA = "Alterar dia"
    ALTERACAO_DE_CARDAPIO = "Alteração de cardápio"
    ALTERACAO_DE_CARDAPIO_CEI = "Alteração de cardápio CEI"
    ALTERACAO_DE_CARDAPIO_CEMEI = "Alteração de cardápio CEMEI"
    ALTERACOES_DE_CARDAPIO = "Alterações de cardápio"
    ALTERACOES_DE_CARDAPIO_CEI = "Alterações de cardápio CEI"
    ALTERACOES_DE_CARDAPIO_CEMEI = "Alterações de cardápio CEMEI"
    ALUNO = "Aluno"
    ALUNO_NO_PERIODO_PARCIAL = "Aluno no período parcial"
    ALUNO_NO_PERIODO_PARCIAL_A_PARTIR_DE = "Aluno no período parcial a partir de"
    ALUNOS = "Alunos"
    ALUNOS_MATRICULADOS_POR_PERIODO_E_ESCOLA = (
        "Alunos Matriculados por Período e Escola"
    )
    ALUNOS_MATRICULADOS_POR_PERIODOS_E_ESCOLAS = (
        "Alunos Matriculados por Períodos e Escolas"
    )
    ALUNOS_DA_CEMEI = "Alunos da CEMEI"
    ALUNOS_NO_PERIODO_PARCIAL = "Alunos no período parcial"
    ANEXO = "Anexo"
    ANEXO_FORMULARIO_BASE = "Anexo Formulário Base"
    ANEXOS_FORMULARIO_BASE = "Anexos Formulário Base"
    ANALISE_DA_FICHA_TECNICA = "Análise da Ficha Técnica"
    ANALISES_DAS_FICHAS_TECNICAS = "Análises das Fichas Técnicas"
    APROVADO = "Aprovado"
    ARQUIVO = "Arquivo"
    ARQUIVO_FICHA_DE_RECEBIMENTO = "Arquivo Ficha de Recebimento"
    ARQUIVO_DO_TIPO_DE_DOCUMENTO = "Arquivo do Tipo de Documento"
    ARQUIVO_PARA_IMPORTACAO_DE_ALIMENTOS_E_ALIMENTOS_SUBSTITUTOS = (
        "Arquivo para importação de Alimentos e Alimentos substitutos"
    )
    ARQUIVO_PARA_IMPORTACAO_DE_SOLICITACOES_DE_DIETA_ESPECIAL = (
        "Arquivo para importação de solicitações de Dieta Especial"
    )
    ARQUIVO_PARA_IMPORTACAO_DE_USUARIO_PERFIL_CODAE = (
        "Arquivo para importação de usuário perfil Codae"
    )
    ARQUIVO_PARA_IMPORTACAO_DE_USUARIO_PERFIL_DRE = (
        "Arquivo para importação de usuário perfil Dre"
    )
    ARQUIVO_PARA_IMPORTACAO_DE_USUARIO_PERFIL_ESCOLA = (
        "Arquivo para importação de usuário perfil Escola"
    )
    ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_OCORRENCIA = (
        "Arquivo para importação/atualização de tipos de ocorrência"
    )
    ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_PENALIDADE = (
        "Arquivo para importação/atualização de tipos de penalidade"
    )
    ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_UES_PARCEIRAS_NO_CORESSO = (
        "Arquivo para importação/atualização de usuários UEs parceiras no CoreSSO"
    )
    ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_EXTERNOS_NO_CORESSO = (
        "Arquivo para importação/atualização de usuários externos no CoreSSO"
    )
    ARQUIVO_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_SERVIDORES_NO_CORESSO = (
        "Arquivo para importação/atualização de usuários servidores no CoreSSO"
    )
    ARQUIVOS_FICHAS_DE_RECEBIMENTOS = "Arquivos Fichas de Recebimentos"
    ARQUIVOS_DOS_TIPOS_DE_DOCUMENTOS = "Arquivos dos Tipos de Documentos"
    ARQUIVOS_PARA_IMPORTACAO_DE_ALIMENTOS_E_ALIMENTOS_SUBSTITUTOS = (
        "Arquivos para importação de Alimentos e Alimentos substitutos"
    )
    ARQUIVOS_PARA_IMPORTACAO_DE_SOLICITACOES_DE_DIETA_ESPECIAL = (
        "Arquivos para importação de solicitações de Dieta Especial"
    )
    ARQUIVOS_PARA_IMPORTACAO_DE_USUARIOS_PERFIL_CODAE = (
        "Arquivos para importação de usuários perfil Codae"
    )
    ARQUIVOS_PARA_IMPORTACAO_DE_USUARIOS_PERFIL_DRE = (
        "Arquivos para importação de usuários perfil Dre"
    )
    ARQUIVOS_PARA_IMPORTACAO_DE_USUARIOS_PERFIL_ESCOLA = (
        "Arquivos para importação de usuários perfil Escola"
    )
    ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_OCORRENCIA = (
        "Arquivos para importação/atualização de tipos de ocorrência"
    )
    ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_TIPOS_DE_PENALIDADE = (
        "Arquivos para importação/atualização de tipos de penalidade"
    )
    ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_UES_PARCEIRAS_NO_CORESSO = (
        "Arquivos para importação/atualização de usuários UEs parceiras no CoreSSO"
    )
    ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_EXTERNOS_NO_CORESSO = (
        "Arquivos para importação/atualização de usuários externos no CoreSSO"
    )
    ARQUIVOS_PARA_IMPORTACAO_ATUALIZACAO_DE_USUARIOS_SERVIDORES_NO_CORESSO = (
        "Arquivos para importação/atualização de usuários servidores no CoreSSO"
    )
    ATIVO = "Ativo?"
    BAIRRO = "Bairro"
    BAIRRO_DA_UNIDADE = "Bairro da unidade"
    CEP = "CEP"
    CEP_DA_UNIDADE = "CEP da unidade"
    CNPJ = "CNPJ"
    CODAE = "CODAE"
    CAPACIDADE_DA_EMBALAGEM = "Capacidade da Embalagem"
    CARACTERISTICAS_DOS_ALIMENTOS = "Características dos alimentos"
    CARGO = "Cargo"
    CARGOS = "Cargos"
    CATEGORIA = "Categoria"
    CATEGORIA_DA_OCORRENCIA = "Categoria da Ocorrência"
    CATEGORIA_DAS_OCORRENCIAS = "Categoria das Ocorrências"
    CATEGORIA_DE_ALIMENTACAO = "Categoria de Alimentação"
    CATEGORIA_DE_MEDICAO = "Categoria de medição"
    CATEGORIAS_DAS_OCORRENCIAS = "Categorias das Ocorrências"
    CATEGORIAS_DE_ALIMENTACAO = "Categorias de Alimentação"
    CATEGORIAS_DE_MEDICOES = "Categorias de medições"
    CENTRAL_DE_DOWNLOAD = "Central de Download"
    CENTRAL_DE_DOWNLOADS = "Central de Downloads"
    CIDADE = "Cidade"
    CIDADE_DA_UNIDADE = "Cidade da unidade"
    CLAUSULA_DE_DESCONTO = "Cláusula de Desconto"
    CLAUSULAS_DE_DESCONTOS = "Cláusulas de Descontos"
    CODIGO_EOL_DA_ESCOLA = "Codigo EOL da escola"
    COM_OCORRENCIAS = "Com ocorrências?"
    COMPLEMENTO = "Complemento"
    COMPLEMENTO_DO_STATUS = "Complemento do status"
    COMPONENTES_DO_PRODUTO = "Componentes do Produto"
    CONDICOES_DE_TRANSPORTE = "Condições de Transporte"
    CONDICOES_DE_CONSERVACAO = "Condições de conservação"
    CONFERENCIA_INDIVIDUAL_POR_ALIMENTO = "Conferência Individual por Alimento"
    CONFERENCIA_DA_GUIA_DE_REMESSA = "Conferência da Guia de Remessa"
    CONFERENCIA_DAS_GUIAS_DE_REMESSAS = "Conferência das Guias de Remessas"
    CONFERENCIAS_INDIVIDUAIS_POR_ALIMENTOS = "Conferências Individuais por Alimentos"
    CONTATO_NA_UNIDADE = "Contato na unidade"
    CONTRATO = "Contrato"
    CONTRATOS = "Contratos"
    CONTEM_GLUTEN = "Contém glúten?"
    CONTEM_LACTOSE = "Contém lactose?"
    CORRECAO_SOLICITADA = "Correção Solicitada"
    CRONOGRAMA = "Cronograma"
    CRONOGRAMA_MENSAL = "Cronograma Mensal"
    CRONOGRAMA_SEMANAL = "Cronograma Semanal"
    CRONOGRAMA_DO_TERMO_DE_RECEBIMENTO_DEFINITIVO = (
        "Cronograma do Termo de Recebimento Definitivo"
    )
    CRONOGRAMAS = "Cronogramas"
    CRONOGRAMAS_SEMANAIS = "Cronogramas Semanais"
    CRONOGRAMAS_DO_TERMO_DE_RECEBIMENTO_DEFINITIVO = (
        "Cronogramas do Termo de Recebimento Definitivo"
    )
    CUSTO_UNITARIO_DO_PRODUTO = "Custo Unitário do Produto"
    CODIGO = "Código"
    CODIGO_CODAE = "Código CODAE"
    CODIGO_EOL = "Código EOL"
    CODIGO_EOL_ALUNO = "Código EOL aluno"
    CODIGO_EOL_ESCOLA_DESTINO = "Código EOL escola destino"
    CODIGO_EOL_ESCOLA_ORIGEM = "Código EOL escola origem"
    CODIGO_DA_UNIDADE = "Código da unidade"
    CODIGO_PAPA = "Código papa"
    CODIGO_SUPRIMENTO = "Código suprimento"
    CODIGOS_CODAE_VINCULADOS = "Códigos Codae Vinculados?"
    DADO_LIQUIDACAO = "Dado Liquidação"
    DADOS_LIQUIDACOES = "Dados Liquidações"
    DATA = "Data"
    DATA_FABRICACAO = "Data Fabricação"
    DATA_FIM = "Data Fim"
    DATA_FINAL_DO_LOTE = "Data Final do Lote"
    DATA_INICIO = "Data Início"
    DATA_MAXIMA_DE_RECEBIMENTO = "Data Máxima de Recebimento"
    DATA_PROGRAMADA = "Data Programada"
    DATA_VALIDADE = "Data Validade"
    DATA_DA_INTERRUPCAO = "Data da Interrupção"
    DATA_DA_ENTREGA = "Data da entrega"
    DATA_DA_PROPOSTA = "Data da proposta"
    DATA_DE_ENTREGA = "Data de Entrega"
    DATA_DE_FABRICACAO_E_PRAZO = "Data de Fabricação e Prazo"
    DATA_DE_INVERSAO = "Data de inversão"
    DATA_DE_RECEBIMENTO = "Data de recebimento"
    DATA_DO_INTERVALO_DE_ALTERACAO_DE_CARDAPIO = (
        "Data do intervalo de Alteração de cardápio"
    )
    DATA_DO_INTERVALO_DE_ALTERACAO_DE_CARDAPIO_CEMEI = (
        "Data do intervalo de Alteração de cardápio CEMEI"
    )
    DATA_E_HORA_DO_ENCERRAMENTO = "Data e hora do encerramento"
    DATA_E_HORA_DO_VINCULO = "Data e hora do vínculo"
    DATA_FINAL = "Data final"
    DATA_INICIAL = "Data inicial"
    DATA_PARA_INVERSAO = "Data para inversão"
    DATA_S_DE_FABRICACAO_OBSERVADA_S_ESTAO_DE_ACORDO = (
        "Data(s) de Fabricação Observada(s) estão de acordo?"
    )
    DATA_S_DE_VALIDADES_OBSERVADA_S_ESTAO_DE_ACORDO = (
        "Data(s) de Validades Observada(s) estão de acordo?"
    )
    DATAS_DE_FABRICACAO_E_PRAZOS = "Datas de Fabricação e Prazos"
    DATAS_DO_INTERVALO_DE_ALTERACAO_DE_CARDAPIO = (
        "Datas do intervalo de Alteração de cardápio"
    )
    DATAS_DO_INTERVALO_DE_ALTERACAO_DE_CARDAPIO_CEMEI = (
        "Datas do intervalo de Alteração de cardápio CEMEI"
    )
    DATAS_E_HORAS_DO_VINCULO = "Datas e horas do vínculo"
    DESCONTO_FINANCEIRO = "Desconto Financeiro"
    DESCONTOS_FINANCEIROS = "Descontos Financeiros"
    DESCRICAO = "Descricao"
    DESCRICAO_2 = "Descrição"
    DESCRICAO_CICLO = "Descrição ciclo"
    DESCRICAO_DA_CLAUSULA_ITEM = "Descrição da Cláusula/Item"
    DESCRICAO_DA_EMBALAGEM = "Descrição da Embalagem"
    DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_FABRICACAO = (
        "Descrição da divergência nas Data(s) de Fabricação"
    )
    DESCRICAO_DA_DIVERGENCIA_NAS_DATA_S_DE_VALIDADES = (
        "Descrição da divergência nas Data(s) de Validades"
    )
    DESCRICAO_DA_DIVERGENCIA_NOS_LOTE_S_DO_FABRICANTE = (
        "Descrição da divergência nos Lote(s) do Fabricante"
    )
    DESCRICAO_DO_DOCUMENTO = "Descrição do Documento"
    DESCRICAO_DO_EVENTO = "Descrição do Evento"
    DESCRICAO_DO_MOTIVO = "Descrição do Motivo"
    DESCRICAO_DO_METODO_DE_CONTAGEM = "Descrição do método de contagem"
    DESCRICAO_ETAPA = "Descrição etapa"
    DETALHAR_LACTOSE = "Detalhar Lactose"
    DIA = "Dia"
    DIA_DA_MEDICAO_PARA_CORRIGIR = "Dia da Medição para corrigir"
    DIA_DE_SOBREMESA_DOCE = "Dia de sobremesa doce"
    DIA_DE_SUSPENSAO_DE_ATIVIDADES = "Dia de suspensão de atividades"
    DIA_E_MOTIVO_INCLUSAO_DE_ALIMENTACAO_CEI = (
        "Dia e motivo inclusão de alimentação CEI"
    )
    DIA_LETIVO_NO_SIGPAE = "Dia letivo no SIGPAE"
    DIAA_E_MOTIVO_INCLUSAO_DE_ALIMENTACAO_CEMEI = (
        "Diaa e motivo inclusão de alimentação CEMEI"
    )
    DIAS = "Dias"
    DIAS_DA_MEDICAO_PARA_CORRIGIR = "Dias da Medição para corrigir"
    DIAS_DE_SOBREMESA_DOCE = "Dias de sobremesa doce"
    DIAS_DE_SUSPENSAO_DE_ATIVIDADES = "Dias de suspensão de atividades"
    DIAS_E_MOTIVOS_INCLUSAO_DE_ALIMENTACAO_CEI = (
        "Dias e motivos inclusão de alimentação CEI"
    )
    DIAS_E_MOTIVOS_INCLUSCAO_DE_ALIMENTACAO_CEMEI = (
        "Dias e motivos inclusçao de alimentação CEMEI"
    )
    DIAS_LETIVOS_NO_SIGPAE = "Dias letivos no SIGPAE"
    DIETA_PARA_RECREIO_NAS_FERIAS = "Dieta para Recreio nas Férias"
    DIRETORIA_REGIONAL = "Diretoria regional"
    DIRETORIAS_REGIONAIS = "Diretorias regionais"
    DOCUMENTO_FICHA_DE_RECEBIMENTO = "Documento Ficha de Recebimento"
    DOCUMENTO_DE_RECEBIMENTO = "Documento de Recebimento"
    DOCUMENTOS_FICHAS_DE_RECEBIMENTO = "Documentos Fichas de Recebimento"
    DOCUMENTOS_DE_RECEBIMENTO = "Documentos de Recebimento"
    E_MAIL = "E-mail"
    E_MAIL_DE_TERCEIRIZADA_POR_MODULOS = "E-mail de Terceirizada por Módulos"
    E_MAILS_DE_TERCEIRIZADAS_POR_MODULOS = "E-mails de Terceirizadas por Módulos"
    EDITAIS = "Editais"
    EDITAL = "Edital"
    EDITAL_NO = "Edital No"
    EMBALAGEM = "Embalagem"
    EMBALAGEM_PRIMARIA = "Embalagem Primária"
    EMBALAGEM_SECUNDARIA = "Embalagem Secundária"
    EMBALAGENS = "Embalagens"
    EMBALAGENS_DE_ACORDO_COM_ANEXO = "Embalagens de Acordo com Anexo?"
    EMPENHO = "Empenho"
    EMPENHOS = "Empenhos"
    EMPRESA = "Empresa"
    ENCERRADO = "Encerrado?"
    ENDERECO = "Endereco"
    ENDERECO_2 = "Endereço"
    ENDERECO_DA_UNIDADE = "Endereço da unidade"
    ENVASADOR_DISTRIBUIDOR = "Envasador/Distribuidor"
    EQUIPAMENTO = "Equipamento"
    EQUIPAMENTO_POR_EDITAL = "Equipamento Por Edital"
    EQUIPAMENTOS = "Equipamentos"
    EQUIPAMENTOS_POR_EDITAL = "Equipamentos Por Edital"
    ESCOLA = "Escola"
    ESCOLA_COM_PERIODO_ESCOLAR = "Escola com período escolar"
    ESCOLA_COM_PERIODOS_ESCOLARES = "Escola com períodos escolares"
    ESCOLA_QUANTIDADE = "Escola quantidade"
    ESCOLAS = "Escolas"
    ESCOLAS_QUANTIDADES = "Escolas quantidades"
    ESPECIFICACOES_DO_PRODUTO = "Especificações do Produto"
    ESPECIFICICACAO_DO_PRODUTO = "Especificicação do Produto"
    ESPECIE_OU_VARIEDADE_CULTIVADA = "Espécie ou Variedade Cultivada"
    ESTA_SUSPENSO = "Esta suspenso?"
    ESTADO = "Estado"
    ESTADO_HIGIENICO_SANITARIO_ADEQUADO = "Estado Higiênico-Sanitário adequado?"
    ESTADO_DA_UNIDADE = "Estado da unidade"
    ESTA_CREDENCIADO = "Está credenciado?"
    ETAPA = "Etapa"
    ETAPA_DO_CRONOGRAMA = "Etapa do Cronograma"
    ETAPAS_DOS_CRONOGRAMAS = "Etapas dos Cronogramas"
    FABRICANTE_DA_FICHA_TECNICA = "Fabricante da Ficha Técnica"
    FABRICANTES_DAS_FICHAS_TECNICAS = "Fabricantes das Fichas Técnicas"
    FAIXA_ETARIA_DE_SOLICITACAO_DE_KIT_LANCHE_CEI_AVULSA = (
        "Faixa Etária de solicitação de kit lanche CEI avulsa"
    )
    FAIXA_ETARIA_DE_SUBSTITUICAO_DE_ALIMENTACAO_CEI = (
        "Faixa Etária de substituição de alimentação CEI"
    )
    FAIXA_ETARIA_DE_SUBSTITUICAO_DE_ALIMENTACAO_CEMEI_CEI = (
        "Faixa Etária de substituição de alimentação CEMEI CEI"
    )
    FAIXA_DE_PONTUACAO_IMR = "Faixa de Pontuação - IMR"
    FAIXA_E_QUANTIDADE_DE_ALUNOS_DA_CEI_DA_SOLICITACAO_KIT_LANCHE_CEMEI = (
        "Faixa e quantidade de alunos da CEI da solicitação kit lanche CEMEI"
    )
    FAIXAS_ETARIAS_DE_SOLICITACAO_DE_KIT_LANCHE_CEI_AVULSA = (
        "Faixas Etárias de solicitação de kit lanche CEI avulsa"
    )
    FAIXAS_ETARIAS_DE_SUBSTITUICAO_DE_ALIMENTACAO_CEI = (
        "Faixas Etárias de substituição de alimentação CEI"
    )
    FAIXAS_ETARIAS_DE_SUBSTITUICAO_DE_ALIMENTACAO_CEMEI_CEI = (
        "Faixas Etárias de substituição de alimentação CEMEI CEI"
    )
    FAIXAS_DE_PONTUACAO_IMR = "Faixas de Pontuação - IMR"
    FAIXAS_E_QUANTIDADE_DE_ALUNOS_DA_CEI_DAS_SOLICITACOES_KIT_LANCHE_CEMEI = (
        "Faixas e quantidade de alunos da CEI das solicitações kit lanche CEMEI"
    )
    FICHA_TECNICA_DO_PRODUTO = "Ficha Técnica do Produto"
    FICHA_DE_RECEBIMENTO = "Ficha de Recebimento"
    FICHAS_TECNICAS_DOS_PRODUTOS = "Fichas Técnicas dos Produtos"
    FICHAS_DE_RECEBIMENTOS = "Fichas de Recebimentos"
    FISCAL_1 = "Fiscal 1"
    FISCAL_2 = "Fiscal 2"
    FISCAL_3 = "Fiscal 3"
    FOI_LIDO = "Foi Lido?"
    FOI_RESOLVIDO = "Foi resolvido?"
    FOI_VISTO = "Foi visto?"
    FORMULARIO_BASE_OCORRENCIAS = "Formulário Base - Ocorrências"
    FORMULARIO_DA_SUPERVISAO_OCORRENCIAS = "Formulário da Supervisão - Ocorrências"
    FORMULARIO_DE_OCORRENCIAS = "Formulário de Ocorrências"
    FORMULARIO_DO_DIRETOR_OCORRENCIAS = "Formulário do Diretor - Ocorrências"
    FORMULARIOS_BASE_OCORRENCIAS = "Formulários Base - Ocorrências"
    FORMULARIOS_DA_SUPERVISAO_OCORRENCIAS = "Formulários da Supervisão - Ocorrências"
    FORMULARIOS_DO_DIRETOR_OCORRENCIAS = "Formulários do Diretor - Ocorrências"
    GERA_NOTIFICACAO = "Gera Notificação?"
    GRUPO_DE_INCLUSAO_DE_ALIMENTACAO_NORMAL = "Grupo de inclusão de alimentação normal"
    GRUPO_DE_MEDICAO = "Grupo de medição"
    GRUPO_DE_SUSPENSAO_DE_ALIMENTACAO = "Grupo de suspensão de alimentação"
    GRUPO_DE_UNIDADE_ESCOLAR = "Grupo de unidade escolar"
    GRUPOS_DE_INCLUSAO_DE_ALIMENTACAO_NORMAL = (
        "Grupos de inclusão de alimentação normal"
    )
    GRUPOS_DE_MEDICAO = "Grupos de medição"
    GRUPOS_DE_UNIDADE_ESCOLAR = "Grupos de unidade escolar"
    GUIA_DE_REMESSA = "Guia de Remessa"
    GUIAS_DE_REMESSAS = "Guias de Remessas"
    HABILITACAO = "Habilitação"
    HISTORICO_DA_ESCOLA = "Histórico da Escola"
    HISTORICO_DE_MATRICULA_DO_ALUNO = "Histórico de Matrícula do Aluno"
    HISTORICO_DE_ACESSO_A_MEDICAO_INICIAL_DA_UE = (
        "Histórico de acesso à medição inicial da UE"
    )
    HISTORICOS_DA_ESCOLA = "Históricos da escola"
    HISTORICOS_DE_MATRICULAS_DOS_ALUNOS = "Históricos de Matrículas dos Alunos"
    HISTORICOS_DE_ACESSO_A_MEDICAO_INICIAL_DA_UE = (
        "Históricos de acesso à medição inicial da UE"
    )
    HOMOLOGACAO_DE_PRODUTO = "Homologação de Produto"
    HOMOLOGACOES_DE_PRODUTO = "Homologações de Produto"
    HORA = "Hora"
    HORA_DA_TENTATIVA_DE_ENTREGA = "Hora da tentativa de entrega"
    HORA_DO_RECEBIMENTO = "Hora do recebimento"
    HOUVE_OCORRENCIA = "Houve Ocorrência?"
    IDADE_ESCOLAR = "Idade escolar"
    IDADES_ESCOLARES = "Idades escolares"
    IMAGEM_DO_PRODUTO = "Imagem do Produto"
    IMAGEM_DO_TIPO_DE_EMBALAGEM = "Imagem do Tipo de Embalagem"
    IMAGENS_DO_PRODUTO = "Imagens do Produto"
    IMAGENS_DOS_TIPOS_DE_EMBALAGENS = "Imagens dos Tipos de Embalagens"
    INCLUSAO_DE_ALIMENTACAO_CEMEI = "Inclusão de alimentação CEMEI"
    INCLUSAO_DE_ALIMENTACAO_CONTINUA = "Inclusão de alimentação contínua"
    INCLUSAO_DE_ALIMENTACAO_DA_CEI = "Inclusão de alimentação da CEI"
    INCLUSAO_DE_ALIMENTACAO_NORMAL = "Inclusão de alimentação normal"
    INCLUSOES_DE_ALIMENTACAO_CEMEI = "Inclusões de alimentação CEMEI"
    INCLUSOES_DE_ALIMENTACAO_CONTINUA = "Inclusões de alimentação contínua"
    INCLUSOES_DE_ALIMENTACAO_DA_CEI = "Inclusões de alimentação da CEI"
    INCLUSOES_DE_ALIMENTACAO_NORMAL = "Inclusões de alimentação normal"
    INFORMACAO_NUTRICIONAL = "Informação Nutricional"
    INFORMACAO_NUTRICIONAL_FIXA = "Informação Nutricional Fixa"
    INFORMACAO_NUTRICIONAL_DA_FICHA_TECNICA = "Informação Nutricional da Ficha Técnica"
    INFORMACAO_NUTRICIONAL_DO_PRODUTO = "Informação Nutricional do Produto"
    INFORMACOES_ADICIONAIS = "Informações Adicionais"
    INFORMACOES_NUTRICIONAIS = "Informações Nutricionais"
    INFORMACOES_NUTRICIONAIS_DA_FICHA_TECNICA = (
        "Informações Nutricionais da Ficha Técnica"
    )
    INFORMACOES_NUTRICIONAIS_DO_PRODUTO = "Informações Nutricionais do Produto"
    INFORMACOES_DE_ARMAZENAMENTO = "Informações de Armazenamento"
    INGREDIENTES_ADITIVOS_ALERGENICOS = "Ingredientes/aditivos alergênicos"
    INSUCESSO_DE_ENTREGA_DA_GUIA = "Insucesso de Entrega da Guia"
    INSUCESSOS_DE_ENTREGAS_DAS_GUIAS = "Insucessos de Entregas das Guias"
    INSUMO = "Insumo"
    INSUMO_POR_EDITAL = "Insumo Por Edital"
    INSUMOS = "Insumos"
    INSUMOS_POR_EDITAL = "Insumos Por Edital"
    INTERRUPCAO_PROGRAMADA_DE_ENTREGA = "Interrupção Programada de Entrega"
    INTERRUPCOES_PROGRAMADAS_DE_ENTREGAS = "Interrupções Programadas de Entregas"
    INVERSAO_DE_CARDAPIO = "Inversão de cardápio"
    INVERSOES_DE_CARDAPIO = "Inversões de cardápio"
    ITEM_DA_CLAUSULA = "Item da Cláusula"
    ITEM_DO_KIT_LANCHE = "Item do kit lanche"
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
    KIT_LANCHE = "Kit lanche"
    KIT_LANCHES = "Kit lanches"
    LABORATORIO = "Laboratório"
    LABORATORIOS = "Laboratórios"
    LANCHE_EMERGENCIAL_DIARIO = "Lanche Emergencial Diário"
    LANCHES_EMERGENCIAIS_DIARIOS = "Lanches Emergenciais Diários"
    LAYOUT_DE_EMBALAGEM = "Layout de Embalagem"
    LAYOUTS_DE_EMBALAGEM = "Layouts de Embalagem"
    LINK = "Link"
    LOG_ALTERACAO_QUANTIDADE_DE_ALUNOS = "Log Alteração quantidade de alunos"
    LOG_ALTERACAO_QUANTIDADE_DE_ALUNOS_REGULAR_E_PROGRAMA = (
        "Log Alteração quantidade de alunos regular e programa"
    )
    LOG_ROTINA_DIARIA_QUANTIDADE_DE_ALUNOS = "Log Rotina Diária quantidade de alunos"
    LOG_ALUNO_POR_DIA = "Log aluno por dia"
    LOG_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR = (
        "Log da quantidade de dietas autorizadas por unidade escolar"
    )
    LOG_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_RECREIO_NAS_FERIAS = "Log da quantidade de dietas autorizadas por unidade escolar - Recreio nas Férias"
    LOG_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_CEI = (
        "Log da quantidade de dietas autorizadas por unidade escolar CEI"
    )
    LOG_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_CEI_RECREIO_NAS_FERIAS = "Log da quantidade de dietas autorizadas por unidade escolar CEI - Recreio nas Férias"
    LOG_DE_PRODUTO_PROVENIENTE_DO_EDITAL = "Log de Produto proveniente do Edital"
    LOG_DE_PRODUTOS_PROVENIENTES_DO_EDITAL = "Log de Produtos provenientes do Edital"
    LOG_DE_SOLICITACAO_DE_CANCELAMENTO_DO_PAPA = (
        "Log de Solicitação de Cancelamento do PAPA"
    )
    LOG_QUANTIDADE_DE_ALUNOS_POR_FAIXA_ETARIA_DIA_E_PERIODO = (
        "Log quantidade de alunos por faixa etária, dia e período"
    )
    LOGRADOURO = "Logradouro"
    LOGS_ROTINA_DIARIA_QUANTIDADE_DE_ALUNOS = "Logs Rotina Diária quantidade de alunos"
    LOGS_ALUNOS_POR_DIA = "Logs alunos por dia"
    LOGS_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR = (
        "Logs da quantidade de dietas autorizadas por unidade escolar"
    )
    LOGS_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_RECREIO_NAS_FERIAS = "Logs da quantidade de dietas autorizadas por unidade escolar - Recreio nas Férias"
    LOGS_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_CEI = (
        "Logs da quantidade de dietas autorizadas por unidade escolar CEI"
    )
    LOGS_DA_QUANTIDADE_DE_DIETAS_AUTORIZADAS_POR_UNIDADE_ESCOLAR_CEI_RECREIO_NAS_FERIAS = "Logs da quantidade de dietas autorizadas por unidade escolar CEI - Recreio nas Férias"
    LOGS_DE_ALTERACAO_QUANTIDADE_DE_ALUNOS = "Logs de Alteração quantidade de alunos"
    LOGS_DE_ALTERACAO_QUANTIDADE_DE_ALUNOS_REGULARES_E_DE_PROGRAMAS = (
        "Logs de Alteração quantidade de alunos regulares e de programas"
    )
    LOGS_DE_SOLICITACOES_DE_CANCELAMENTO_DO_PAPA = (
        "Logs de Solicitações de Cancelamento do PAPA"
    )
    LOGS_DE_MATRICULADOS_DIETAS_AUTORIZADAS_ETC_FORAM_SALVOS = (
        "Logs de matriculados, dietas autorizadas, etc foram salvos?"
    )
    LOGS_QUANTIDADES_DE_ALUNOS_POR_FAIXAS_ETARIAS_DIAS_E_PERIODOS = (
        "Logs quantidades de alunos por faixas etárias, dias e períodos"
    )
    LOTE = "Lote"
    LOTE_S_DO_FABRICANTE_OBSERVADO_S_ESTAO_DE_ACORDO = (
        "Lote(s) do Fabricante Observado(s) estão de acordo?"
    )
    LOTES = "Lotes"
    MAIOR_NO_DE_FREQUENTES_NO_PERIODO = "Maior Nº de Frequentes no Período"
    MARCAR_COMO_CONFERIDO = "Marcar como conferido?"
    MATERIAL_DA_EMBALAGEM_PRIMARIA = "Material da Embalagem Primária"
    MEDICAO = "Medição"
    MEDICOES = "Medições"
    MENSAGEM_ERRO = "Mensagem erro"
    MOBILIARIO = "Mobiliário"
    MOBILIARIO_POR_EDITAL = "Mobiliário Por Edital"
    MOBILIARIOS = "Mobiliários"
    MOBILIARIOS_POR_EDITAL = "Mobiliários Por Edital"
    MODALIDADE = "Modalidade"
    MODALIDADES = "Modalidades"
    MODO_DE_PREPARO_DO_PRODUTO = "Modo de Preparo do Produto"
    MOTIVO_ALTERACAO_U_E = "Motivo Alteração U.E"
    MOTIVO_DA_INTERRUPCAO = "Motivo da Interrupção"
    MOTIVO_DE_ALTERACAO_DE_CARDAPIO = "Motivo de alteração de cardápio"
    MOTIVO_DE_INCLUSAO_CONTINUA = "Motivo de inclusao contínua"
    MOTIVO_DE_INCLUSAO_NORMAL = "Motivo de inclusao normal"
    MOTIVO_DE_NAO_VALIDACAO_DA_DRE = "Motivo de não validação da DRE"
    MOTIVO_DE_SUSPENSAO_DE_ALIMENTACAO = "Motivo de suspensão de alimentação"
    MOTIVO_DO_INSUCESSO = "Motivo do insucesso"
    MOTIVOS_DE_ALTERACAO_DE_CARDAPIO = "Motivos de alteração de cardápio"
    MOTIVOS_DE_INCLUSAO_CONTINUA = "Motivos de inclusao contínua"
    MOTIVOS_DE_INCLUSAO_NORMAIS = "Motivos de inclusao normais"
    MOTIVOS_DE_NAO_VALIDACAO_DA_DRE = "Motivos de não validação da DRE"
    MES_PROGRAMADO = "Mês Programado"
    MODULO = "Módulo"
    MODULOS = "Módulos"
    NO_DA_ATA = "No da Ata"
    NO_DO_CONTRATO = "No do contrato"
    NOME = "Nome"
    NOME_COMPLETO_DO_ALUNO = "Nome Completo do Aluno"
    NOME_COMPLETO_DO_RESPONSAVEL_TECNICO = "Nome completo do Responsável Técnico"
    NOME_COMPLETO_DO_PESCRITOR_DA_RECEITA = "Nome completo do pescritor da receita"
    NOME_DA_ESCOLA_DESTINO = "Nome da Escola destino"
    NOME_DA_ESCOLA_ORIGEM = "Nome da Escola origem"
    NOME_DA_NUTRICIONISTA_RT_DA_EMPRESA = "Nome da Nutricionista RT da Empresa"
    NOME_DA_UNIDADE = "Nome da unidade"
    NOME_DO_ALUNO = "Nome do Aluno"
    NOME_DO_PROTOCOLO = "Nome do Protocolo"
    NOME_DO_ALIMENTO_PRODUTO = "Nome do alimento/produto"
    NOME_DO_ARQUIVO = "Nome do arquivo"
    NOME_DO_MOTORISTA = "Nome do motorista"
    NOME_FANTASIA = "Nome fantasia"
    NOTIFICACAO = "Notificação"
    NOTIFICACAO_ASSINADA = "Notificação Assinada"
    NOTIFICACAO_ASSINADA_FORMULARIO_BASE = "Notificação Assinada Formulário Base"
    NOTIFICACAO_DE_GUIAS_COM_OCORRENCIAS = "Notificação de Guias com Ocorrencias"
    NOTIFICACOES = "Notificações"
    NOTIFICACOES_ASSINADAS_FORMULARIO_BASE = "Notificações Assinadas Formulário Base"
    NOTIFICACOES_DE_GUIAS_COM_OCORRENCIAS = "Notificações de Guias com Ocorrencias"
    NUTRICIONISTA = "Nutricionista"
    NUTRICIONISTA_CRN = "Nutricionista crn"
    NUTRICIONISTAS = "Nutricionistas"
    NO_SIF_SISBI_OU_SISP = "Nº SIF, SISBI ou SISP"
    NO_DA_CHAMADA_PUBLICA = "Nº da Chamada Pública"
    NO_DE_PALETES = "Nº de Paletes"
    NO_DO_LOTE_ARMAZENAGEM = "Nº do Lote Armazenagem"
    NO_DO_PREGAO_ELETRONICO = "Nº do Pregão Eletrônico"
    NO_DO_PROCESSO_SEI = "Nº do Processo SEI"
    NO_DO_REGISTRO_DO_ROTULO = "Nº do Registro do Rótulo"
    NO_DO_REGISTRO_EM_ORGAO_COMPETENTE = "Nº do Registro em Órgão Competente"
    NO_DO_VEICULO = "Nº do Veículo"
    NUMERO = "Número"
    NUMERO_DA_CLAUSULA = "Número da Cláusula"
    NUMERO_DA_CLAUSULA_ITEM = "Número da Cláusula/Item"
    NUMERO_DA_FICHA_TECNICA = "Número da Ficha Técnica"
    NUMERO_DA_NOTA = "Número da Nota"
    NUMERO_DA_NOTIFICACAO = "Número da Notificação"
    NUMERO_DA_GUIA = "Número da guia"
    NUMERO_DA_SOLICITACAO = "Número da solicitação"
    NUMERO_DA_UNIDADE = "Número da unidade"
    NUMERO_DO_CRONOGRAMA = "Número do Cronograma"
    NUMERO_DO_CRONOGRAMA_SEMANAL = "Número do Cronograma Semanal"
    NUMERO_DO_EMPENHO = "Número do Empenho"
    NUMERO_DO_LAUDO = "Número do Laudo"
    NUMERO_DO_EMPENHO_2 = "Número do empenho"
    O_PRODUTO_E_LIQUIDO = "O produto é líquido?"
    OBRIGACAO_DA_PENALIDADE = "Obrigação da Penalidade"
    OBRIGACOES_DAS_PENALIDADES = "Obrigações das Penalidades"
    OBSERVACAO = "Observação"
    OBSERVACOES = "Observações"
    OBSERVACOES_ALTERACAO = "Observações Alteração"
    OCORRENCIA_NAO_SE_APLICA = "Ocorrência Não se aplica"
    OCORRENCIA_DA_FICHA_DE_RECEBIMENTO = "Ocorrência da Ficha de Recebimento"
    OCORRENCIAS_NAO_SE_APLICA = "Ocorrências Não se aplica"
    OCORRENCIAS_DAS_FICHAS_DE_RECEBIMENTO = "Ocorrências das Fichas de Recebimento"
    OPCAO = "Opção"
    ORIENTACOES_GERAIS = "Orientações Gerais"
    OUTRAS_INFORMACOES = "Outras Informações"
    OUTRO_MOTIVO = "Outro Motivo"
    OUTRO_MOTIVO_2 = "Outro motivo"
    PARAMETRIZACAO_FINANCEIRA = "Parametrização Financeira"
    PARAMETRIZACAO_FINANCEIRA_TABELA = "Parametrização Financeira Tabela"
    PARAMETRIZACAO_FINANCEIRA_TABELA_VALOR = "Parametrização Financeira Tabela Valor"
    PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA = "Parametrização de Tipo de Ocorrência"
    PARAMETRIZACOES_FINANCEIRAS = "Parametrizações Financeiras"
    PARAMETRIZACOES_FINANCEIRAS_TABELAS = "Parametrizações Financeiras Tabelas"
    PARAMETRIZACOES_FINANCEIRAS_TABELAS_VALORES = (
        "Parametrizações Financeiras Tabelas Valores"
    )
    PARAMETRIZACOES_DE_TIPO_DE_OCORRENCIA = "Parametrizações de Tipo de Ocorrência"
    PARTE = "Parte"
    PENALIDADE_DO_ITEM = "Penalidade do Item"
    PERFIL = "Perfil"
    PERFIS = "Perfis"
    PERFIS_VINCULADOS = "Perfis Vinculados"
    PERGUNTA = "Pergunta"
    PERGUNTA_OBRIGATORIA = "Pergunta Obrigatória?"
    PERMISSAO_DE_LANCAMENTO_ESPECIAL = "Permissão de Lançamento Especial"
    PERMISSOES_DE_LANCAMENTOS_ESPECIAIS = "Permissões de Lançamentos Especiais"
    PERIODO_DA_VISITA = "Período da Visita"
    PERIODO_DE_VISITA = "Período de Visita"
    PERIODO_ESCOLAR = "Período escolar"
    PERIODOS_DE_VISITA = "Períodos de Visita"
    PERIODOS_ESCOLARES = "Períodos escolares"
    PESO_DA_EMBALAGEM_PRIMARIA_1 = "Peso da Embalagem Primária (1)"
    PESO_DA_EMBALAGEM_PRIMARIA_2 = "Peso da Embalagem Primária (2)"
    PESO_DA_EMBALAGEM_PRIMARIA_3 = "Peso da Embalagem Primária (3)"
    PESO_DA_EMBALAGEM_PRIMARIA_4 = "Peso da Embalagem Primária (4)"
    PLACA_DO_VEICULO = "Placa do veículo"
    PLANILHA_ATUALIZACAO_TIPO_GESTAO_ESCOLA = "Planilha Atualização Tipo Gestão Escola"
    PLANILHA_DE_PARA_CODIGO_EOL_X_CODIGO_CODAE = (
        "Planilha De-Para: Código EOL x Código Codae"
    )
    PLANILHA_DIETA_ATIVA = "Planilha Dieta Ativa"
    PLANILHA_DIRETOR_COGESTOR = "Planilha Diretor Cogestor"
    PLANILHAS_DE_PARA_CODIGO_EOL_X_CODIGO_CODAE = (
        "Planilhas De-Para: Código EOL x Código Codae"
    )
    PLANILHAS_DIETAS_ATIVAS = "Planilhas Dietas Ativas"
    PLANILHAS_DIRETORES_COGESTORES = "Planilhas Diretores Cogestores"
    PODE_CONTER_ALERGENICOS = "Pode conter alergênicos?"
    PONTUACAO_IMR = "Pontuação (IMR)"
    PONTUACAO_MAXIMA = "Pontuação Máxima"
    PONTUACAO_MINIMA = "Pontuação Mínima"
    PORQUE_FOI_SUSPENSO_INDIVIDUALMENTE = "Porque foi suspenso individualmente"
    PORCAO = "Porção"
    PORCAO_NUTRICIONAL = "Porção nutricional"
    POSICAO = "Posição"
    POSSUI_ALUNOS_PERIODO_PARCIAL = "Possui alunos periodo parcial?"
    PRAZO_MAXIMO_PARA_RECEBIMENTO = "Prazo Máximo para Recebimento"
    PRAZO_DE_VALIDADE = "Prazo de Validade"
    PRAZO_DE_VALIDADE_DESCONGELAMENTO = "Prazo de Validade Descongelamento"
    PRAZO_DE_VALIDADE_2 = "Prazo de validade"
    PREVISAO_CONTRATUAL = "Previsão Contratual"
    PREVISOES_CONTRATUAIS = "Previsões Contratuais"
    PROCESSO_ADMINISTRATIVO = "Processo Administrativo"
    PRODUTO = "Produto"
    PRODUTO_PROVENIENTE_DO_EDITAL = "Produto proveniente do Edital"
    PRODUTOS = "Produtos"
    PRODUTOS_PROVENIENTES_DO_EDITAL = "Produtos provenientes do Edital"
    PROGRAMA = "Programa"
    PROGRAMACAO_DE_ENTREGA_SEMANAL = "Programação de Entrega Semanal"
    PROGRAMACAO_DO_RECEBIMENTO_DO_CROMOGRAMA = (
        "Programação do Recebimento do Cromograma"
    )
    PROGRAMACOES_DE_ENTREGA_SEMANAL = "Programações de Entrega Semanal"
    PROGRAMACOES_DOS_RECEBIMENTOS_DOS_CROMOGRAMAS = (
        "Programações dos Recebimentos dos Cromogramas"
    )
    PROTOCOLO_DE_DIETA_ESPECIAL = "Protocolo de Dieta Especial"
    PROTOCOLO_PADRAO_DE_DIETA_ESPECIAL = "Protocolo padrão de dieta especial"
    PROTOCOLOS_DE_DIETA_ESPECIAL = "Protocolos de Dieta Especial"
    PROTOCOLOS_PADROES_DE_DIETA_ESPECIAL = "Protocolos padrões de dieta especial"
    PROVENIENTE_DE_IMPORTACAO = "Proveniente de importacao?"
    QTD_TOTAL_PROGRAMADA = "Qtd Total Programada"
    QTD_TOTAL_DE_GUIAS_NA_REQUISICAO = "Qtd total de guias na requisição"
    QTDE_TOTAL_DO_EMPENHO = "Qtde. Total do Empenho"
    QUANTIDADE = "Quantidade"
    QUANTIDADE_RECEBIDA = "Quantidade Recebida"
    QUANTIDADE_TOTAL_RECEBIDA = "Quantidade Total Recebida"
    QUANTIDADE_A_RECEBER_FALTANTE = "Quantidade a receber faltante"
    QUANTIDADE_DA_ENTREGA = "Quantidade da Entrega"
    QUANTIDADE_DE_EMBALAGENS_RECEBIDAS = "Quantidade de Embalagens Recebidas"
    QUANTIDADE_DE_EMBALAGENS_DA_NOTA_FISCAL = "Quantidade de Embalagens da Nota Fiscal"
    QUANTIDADE_DE_ALUNOS = "Quantidade de alunos"
    QUANTIDADE_DE_ALUNOS_EMEI_POR_INCLUSAO_DE_ALIMENTACAO_CEMEI = (
        "Quantidade de alunos EMEI por inclusao de alimentação CEMEI"
    )
    QUANTIDADE_DE_ALUNOS_ALTERADA = "Quantidade de alunos alterada"
    QUANTIDADE_DE_ALUNOS_ANTERIOR = "Quantidade de alunos anterior"
    QUANTIDADE_DE_ALUNOS_ANTES = "Quantidade de alunos antes"
    QUANTIDADE_DE_ALUNOS_ATUAL = "Quantidade de alunos atual"
    QUANTIDADE_DE_ALUNOS_POR_FAIXA_ETARIA_DA_INCLUSAO_DE_ALIMENTACAO = (
        "Quantidade de alunos por faixa etária da inclusao de alimentação"
    )
    QUANTIDADE_DE_ALUNOS_POR_FAIXA_ETARIA_DA_INCLUSAO_DE_ALIMENTACAO_CEMEI = (
        "Quantidade de alunos por faixa etária da inclusao de alimentação CEMEI"
    )
    QUANTIDADE_POR_PERIODO = "Quantidade por periodo"
    QUANTIDADE_POR_PERIODO_DE_SUSPENSAO_DE_ALIMENTACAO = (
        "Quantidade por período de suspensão de alimentação"
    )
    QUANTIDADE_RECEBIDO = "Quantidade recebido"
    QUANTIDADE_VOLUME = "Quantidade/Volume"
    QUANTIDADES_POR_PERIODO = "Quantidades por periodo"
    QUESTAO = "Questão"
    QUESTAO_DE_CONFERENCIA = "Questão de Conferência"
    QUESTAO_PARA_CONFERENCIA = "Questão para Conferência"
    QUESTAO_POR_FICHA_DE_RECEBIMENTO = "Questão por Ficha de Recebimento"
    QUESTOES_PARA_CONFERENCIA = "Questões para Conferência"
    QUESTOES_POR_FICHAS_DE_RECEBIMENTO = "Questões por Fichas de Recebimento"
    QUESTOES_POR_PRODUTO = "Questões por Produto"
    QUESTOES_POR_PRODUTOS = "Questões por Produtos"
    QUESTOES_REFERENTES_A_EMBALAGEM_PRIMARIA = (
        "Questões referentes à Embalagem Primária"
    )
    QUESTOES_REFERENTES_A_EMBALAGEM_SECUNDARIA = (
        "Questões referentes à Embalagem Secundária"
    )
    RF_CRN_CRF = "RF/CRN/CRF"
    RAZAO_SOCIAL = "Razao social"
    RECLAMACAO = "Reclamação"
    RECREIO_NAS_FERIAS_UNIDADE_PARTICIPANTE = (
        "Recreio nas Férias - Unidade Participante"
    )
    RECREIOS_NAS_FERIAS = "Recreios nas Férias"
    RECREIOS_NAS_FERIAS_UNIDADES_PARTICIPANTES = (
        "Recreios nas Férias - Unidades Participantes"
    )
    REGISTRO_DO_ORGAO_COMPETENTE = "Registro do órgão competente"
    REGISTRO_FUNCIONAL_DO_NUTRICIONISTA = "Registro funcional do nutricionista"
    REGISTRO_FUNCIONAL_DO_PESCRITOR_DA_RECEITA = (
        "Registro funcional do pescritor da receita"
    )
    RELATORIO_FINANCEIRO = "Relatório Financeiro"
    RELATORIOS_FINANCEIROS = "Relatórios Financeiros"
    RELACAO = "Relação"
    REPARO_E_ADAPTACAO = "Reparo e Adaptação"
    REPARO_E_ADAPTACAO_POR_EDITAL = "Reparo e Adaptação Por Edital"
    REPAROS_E_ADAPTACOES = "Reparos e Adaptações"
    REPAROS_E_ADAPTACOES_POR_EDITAL = "Reparos e Adaptações Por Edital"
    REPONSAVEIS = "Reponsáveis"
    REPOSICAO_CRONOGRAMA_DA_FICHA_DE_RECEBIMENTO = (
        "Reposição Cronograma da Ficha de Recebimento"
    )
    REPOSICOES_CRONOGRAMAS_DAS_FICHAS_DE_RECEBIMENTO = (
        "Reposições Cronogramas das Fichas de Recebimento"
    )
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
    RESPOSTA_CAMPO_NUMERICO = "Resposta Campo Numérico"
    RESPOSTA_CAMPO_TEXTO_LONGO = "Resposta Campo Texto Longo"
    RESPOSTA_CAMPO_TEXTO_SIMPLES = "Resposta Campo Texto Simples"
    RESPOSTA_DATAS = "Resposta Datas"
    RESPOSTA_EQUIPAMENTO = "Resposta Equipamento"
    RESPOSTA_FAIXA_ETARIA = "Resposta Faixa Etária"
    RESPOSTA_INSUMO = "Resposta Insumo"
    RESPOSTA_MOBILIARIO = "Resposta Mobiliário"
    RESPOSTA_PERIODO = "Resposta Período"
    RESPOSTA_REPARO_E_ADAPTACAO = "Resposta Reparo e Adaptação"
    RESPOSTA_SIM_NAO_2 = "Resposta Sim/Não"
    RESPOSTA_SIM_NAO_NAO_SE_APLICA = "Resposta Sim/Não/Não se aplica"
    RESPOSTA_TIPO_ALIMENTACAO = "Resposta Tipo Alimentação"
    RESPOSTA_UTENSILIO_DE_COZINHA = "Resposta Utensílio de Cozinha"
    RESPOSTA_UTENSILIO_DE_MESA = "Resposta Utensílio de Mesa"
    RESPOSTAS_CAMPO_NUMERICO = "Respostas Campo Numérico"
    RESPOSTAS_CAMPO_TEXTO_LONGO = "Respostas Campo Texto Longo"
    RESPOSTAS_CAMPO_TEXTO_SIMPLES = "Respostas Campo Texto Simples"
    RESPOSTAS_DATAS = "Respostas Datas"
    RESPOSTAS_EQUIPAMENTO = "Respostas Equipamento"
    RESPOSTAS_FAIXA_ETARIA = "Respostas Faixa Etária"
    RESPOSTAS_INSUMO = "Respostas Insumo"
    RESPOSTAS_MOBILIARIO = "Respostas Mobiliário"
    RESPOSTAS_PERIODO = "Respostas Período"
    RESPOSTAS_REPARO_E_ADAPTACAO = "Respostas Reparo e Adaptação"
    RESPOSTAS_SIM_NAO = "Respostas Sim/Não"
    RESPOSTAS_SIM_NAO_NAO_SE_APLICA = "Respostas Sim/Não/Não se aplica"
    RESPOSTAS_TIPO_ALIMENTACAO = "Respostas Tipo Alimentação"
    RESPOSTAS_UTENSILIO_DE_COZINHA = "Respostas Utensílio de Cozinha"
    RESPOSTAS_UTENSILIO_DE_MESA = "Respostas Utensílio de Mesa"
    ROTULO_LEGIVEL = "Rotulo Legível?"
    SEQUENCIA_DE_ENVIO_ATRIBUIDA_PELO_PAPA = "Sequência de envio atribuída pelo papa"
    SEQUENCIA_DE_ENVIO_ATRIBUIDO_PELO_PAPA = "Sequência de envio atribuído pelo papa"
    SISTEMA_DE_VEDACAO_DA_EMBALAGEM_SECUNDARIA = (
        "Sistema de Vedação da Embalagem Secundária"
    )
    SOLICITACAO_KIT_LANCHE_CEI_DA_EMEI = "Solicitação Kit Lanche CEI da EMEI"
    SOLICITACAO_KIT_LANCHE_CEMEI = "Solicitação Kit Lanche CEMEI"
    SOLICITACAO_MEDICAO_INICIAL = "Solicitação Medição Inicial"
    SOLICITACAO_REMESSA = "Solicitação Remessa"
    SOLICITACAO_DE_ALTERACAO_DE_CRONOGRAMA = "Solicitação de Alteração de Cronograma"
    SOLICITACAO_DE_ALTERACAO_DE_REQUISICAO = "Solicitação de Alteração de Requisição"
    SOLICITACAO_DE_DIETA_ESPECIAL = "Solicitação de dieta especial"
    SOLICITACAO_DE_KIT_LANCHE_CEI_AVULSA = "Solicitação de kit lanche CEI avulsa"
    SOLICITACAO_DE_KIT_LANCHE_AVULSA = "Solicitação de kit lanche avulsa"
    SOLICITACAO_DE_MEDICAO_INICIAL = "Solicitação de medição inicial"
    SOLICITACAO_KIT_LANCHE_BASE = "Solicitação kit lanche base"
    SOLICITACAO_KIT_LANCHE_UNIFICADA = "Solicitação kit lanche unificada"
    SOLICITACOES_KIT_LANCHE_CEI_DA_EMEI = "Solicitações Kit Lanche CEI da EMEI"
    SOLICITACOES_KIT_LANCHE_CEMEI = "Solicitações Kit Lanche CEMEI"
    SOLICITACOES_REMESSAS = "Solicitações Remessas"
    SOLICITACOES_DE_KIT_LANCHE_UNIFICADAS = "Solicitações de  kit lanche unificadas"
    SOLICITACOES_DE_ALTERACAO_DE_CRONOGRAMA = "Solicitações de Alteração de Cronograma"
    SOLICITACOES_DE_ALTERACAO_DE_REQUISICAO = "Solicitações de Alteração de Requisição"
    SOLICITACOES_DE_DIETA_ESPECIAL = "Solicitações de dieta especial"
    SOLICITACOES_DE_KIT_LANCHE_CEI_AVULSA = "Solicitações de kit lanche CEI avulsa"
    SOLICITACOES_DE_KIT_LANCHE_AVULSA = "Solicitações de kit lanche avulsa"
    SOLICITACOES_DE_MEDICAO_INICIAL = "Solicitações de medição inicial"
    SOLICITACOES_KIT_LANCHE_BASE = "Solicitações kit lanche base"
    STATUS = "Status"
    STATUS_DA_ANALISE = "Status da análise"
    STATUS_DA_GUIA = "Status da guia"
    STATUS_DA_REQUISICAO = "Status da requisição"
    SUBPREFEITURA = "Subprefeitura"
    SUBPREFEITURAS = "Subprefeituras"
    SUBSTITUICAO_DE_ALIMENTO_PARA_PROTOCOLO_PADRAO_DE_DIETA = (
        "Substituição de alimento para protocolo padrão de dieta"
    )
    SUBSTITUICOES_DE_ALIMENTACAO_CEI_NO_PERIODO = (
        "Substituições de alimentação CEI no período"
    )
    SUBSTITUICOES_DE_ALIMENTACAO_CEMEI_CEI_NO_PERIODO = (
        "Substituições de alimentação CEMEI CEI no período"
    )
    SUBSTITUICOES_DE_ALIMENTACAO_CEMEI_EMEI_NO_PERIODO = (
        "Substituições de alimentação CEMEI EMEI no período"
    )
    SUBSTITUICOES_DE_ALIMENTACAO_NO_PERIODO = "Substituições de alimentação no período"
    SUBSTITUICOES_DE_ALIMENTOS_PARA_PROTOCOLOS_PADROES_DE_DIETAS = (
        "Substituições de alimentos para protocolos padrões de dietas"
    )
    SUPER_USUARIO_NA_INSTIUICAO = "Super usuario na instiuição?"
    SUSPENSO_EM = "Suspenso em"
    SUSPENSAO_DE_ALIMENTACAO = "Suspensão de alimentação"
    SUSPENSOES_DE_ALIMENTACAO_DE_CEI = "Suspensões de Alimentação de CEI"
    SUSPENSOES_DE_ALIMENTACAO = "Suspensões de alimentação"
    TELEFONE = "Telefone"
    TELEFONE_DA_UNIDADE = "Telefone da unidade"
    TEM_GLUTEN = "Tem Glúten?"
    TEM_ADITIVOS_ALERGENICOS = "Tem aditivos alergênicos"
    TEMPERATURA_INTERNA_DO_VEICULO_PARA_TRANSPORTE = (
        "Temperatura Interna do Veículo para Transporte"
    )
    TEMPERATURA_DA_AREA_DE_RECEBIMENTO_C = "Temperatura da Área de Recebimento (°C)"
    TEMPERATURA_DE_CONGELAMENTO_DO_PRODUTO = "Temperatura de Congelamento do Produto"
    TEMPERATURA_DO_PRODUTO_C = "Temperatura do Produto (°C)"
    TERCEIRIZADA = "Terceirizada"
    TERCEIRIZADAS = "Terceirizadas"
    TERMO_DE_RECEBIMENTO_DEFINITIVO = "Termo de Recebimento Definitivo"
    TERMOS_DE_RECEBIMENTO_DEFINITIVO = "Termos de Recebimento Definitivo"
    TEXTO_DO_TERMO = "Texto do Termo"
    TIPO = "Tipo"
    TIPO_DE_ALIMENTACAO_DA_UNIDADE = "Tipo de Alimentação da Unidade"
    TIPO_DE_CALENDARIO = "Tipo de Calendário"
    TIPO_DE_DOCUMENTO_DE_RECEBIMENTO = "Tipo de Documento de Recebimento"
    TIPO_DE_EMBALAGEM_QUALIDADE = "Tipo de Embalagem (Qualidade)"
    TIPO_DE_EMBALAGEM_FECHADA = "Tipo de Embalagem Fechada"
    TIPO_DE_EMBALAGEM_DE_LAYOUT = "Tipo de Embalagem de Layout"
    TIPO_DE_ENTREGA = "Tipo de Entrega"
    TIPO_DE_GRAVIDADE = "Tipo de Gravidade"
    TIPO_DE_OCORRENCIA = "Tipo de Ocorrência"
    TIPO_DE_PENALIDADE = "Tipo de Penalidade"
    TIPO_DE_PERGUNTA_PARA_PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA = (
        "Tipo de Pergunta para Parametrização de Tipo de Ocorrência"
    )
    TIPO_DE_RESPOSTA_MODELO = "Tipo de Resposta (Modelo)"
    TIPO_DE_SOBREMESA_DOCE = "Tipo de Sobremesa Doce"
    TIPO_DE_ALIMENTACAO = "Tipo de alimentação"
    TIPO_DE_CONTAGEM_DAS_ALIMENTACOES = "Tipo de contagem das alimentações"
    TIPO_DE_CONTRATACAO = "Tipo de contratação"
    TIPO_DE_EMPENHO = "Tipo de empenho"
    TIPO_DE_GESTAO = "Tipo de gestão"
    TIPO_DE_LANCAMENTO = "Tipo de lançamento"
    TIPO_DE_RESPOSTA = "Tipo de resposta"
    TIPO_DE_UNIDADE_ESCOLAR = "Tipo de unidade escolar"
    TIPO_DO_PRODUTO = "Tipo do Produto"
    TIPOS_DE_ALIMENTACAO_DAS_UNIDADES = "Tipos de Alimentação das Unidades"
    TIPOS_DE_DOCUMENTOS_DE_RECEBIMENTO = "Tipos de Documentos de Recebimento"
    TIPOS_DE_EMBALAGENS_QUALIDADE = "Tipos de Embalagens (Qualidade)"
    TIPOS_DE_EMBALAGENS_FECHADAS = "Tipos de Embalagens Fechadas"
    TIPOS_DE_EMBALAGENS_DE_LAYOUT = "Tipos de Embalagens de Layout"
    TIPOS_DE_GRAVIDADES = "Tipos de Gravidades"
    TIPOS_DE_OCORRENCIA = "Tipos de Ocorrência"
    TIPOS_DE_PENALIDADES = "Tipos de Penalidades"
    TIPOS_DE_PERGUNTA_PARA_PARAMETRIZACAO_DE_TIPO_DE_OCORRENCIA = (
        "Tipos de Pergunta para Parametrização de Tipo de Ocorrência"
    )
    TIPOS_DE_RESPOSTA_MODELO = "Tipos de Resposta (Modelo)"
    TIPOS_DE_SOBREMESA_DOCE = "Tipos de Sobremesa Doce"
    TIPOS_DE_ALIMENTACAO = "Tipos de alimentação"
    TIPOS_DE_CONTAGEM_DAS_ALIMENTACOES = "Tipos de contagem das alimentações"
    TIPOS_DE_GESTAO = "Tipos de gestão"
    TIPOS_DE_UNIDADE_ESCOLAR = "Tipos de unidade escolar"
    TITULO = "Titulo"
    TOLERANCIA = "Tolerância"
    TOTAL_DE_EMBALAGENS = "Total de Embalagens"
    TITULO_2 = "Título"
    UNIDADE_CASEIRA = "Unidade Caseira"
    UNIDADE_DE_MEDIDA = "Unidade de Medida"
    UNIDADE_DE_MEDIDA_CASEIRA = "Unidade de Medida Caseira"
    UNIDADE_NUTRICIONAL = "Unidade nutricional"
    UNIDADES_DE_MEDIDA = "Unidades de Medida"
    USUARIO = "Usuário"
    USUARIOS = "Usuários"
    UTENSILIO_DE_COZINHA = "Utensílio de Cozinha"
    UTENSILIO_DE_COZINHA_POR_EDITAL = "Utensílio de Cozinha Por Edital"
    UTENSILIO_DE_MESA = "Utensílio de Mesa"
    UTENSILIO_DE_MESA_POR_EDITAL = "Utensílio de Mesa Por Edital"
    UTENSILIOS_DE_COZINHA = "Utensílios de Cozinha"
    UTENSILIOS_DE_COZINHA_POR_EDITAL = "Utensílios de Cozinha Por Edital"
    UTENSILIOS_DE_MESA = "Utensílios de Mesa"
    UTENSILIOS_DE_MESA_POR_EDITAL = "Utensílios de Mesa Por Edital"
    VALOR_DA_MEDICAO = "Valor da Medição"
    VALOR_DO_CAMPO = "Valor do Campo"
    VALOR_DO_CONTRATO = "Valor do Contrato"
    VALORES_DAS_MEDICOES = "Valores das Medições"
    VERSAO_DO_SISTEMA = "Versão do Sistema"
    VERSOES_DO_SISTEMA = "Versões do Sistema"
    VEICULO_FICHA_DE_RECEBIMENTO = "Veículo Ficha de Recebimento"
    VEICULOS_FICHAS_DE_RECEBIMENTOS = "Veículos Fichas de Recebimentos"
    VIGENCIA_DE_CONTRATO = "Vigência de contrato"
    VIGENCIAS_DE_CONTRATO = "Vigências de contrato"
    VINCULO_ENTRE_PRODUTO_E_EDITAL = "Vinculo entre produto e edital"
    VINCULOS_ENTRE_PRODUTOS_E_EDITAIS = "Vinculos entre produtos e editais"
    VISAO = "Visão"
    VOLUME = "Volume"
    VINCULO = "Vínculo"
    VINCULO_TIPO_ALIMENTACAO = "Vínculo tipo alimentação"
    VINCULOS = "Vínculos"
    VINCULOS_TIPO_ALIMENTACAO = "Vínculos tipo alimentação"
    ACAO = "ação"
    CRIADO_EM = "criado em"
    LOG_DIETAS_ATIVAS_CANCELADAS_AUTOMATICAMENTE = (
        "log dietas ativas canceladas automaticamente"
    )
    OBJETO_RESUMIDO = "objeto resumido"
    STATUS_2 = "status"
    TIPO_DE_PRODUTO = "tipo de produto"
    E_ADMINISTRADOR_POR_PARTE_DAS_TERCEIRIZADAS = (
        "É Administrador por parte das Terceirizadas?"
    )
    E_IMR = "É IMR?"
    E_DIA_LETIVO = "É dia Letivo?"
    E_NUTRICIONISTA = "É nutricionista?"
    E_ORGANICO = "É orgânico?"
    E_PARA_ALUNOS_COM_DIETA_ESPECIAL = "É para alunos com dieta especial"

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
