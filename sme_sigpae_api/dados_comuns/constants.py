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
RELATORIO_ANALISE = "relatorio-analise-sensorial"
RELATORIO_SUSPENSOS = "relatorio-produtos-suspensos"
RELATORIO_RECEBIMENTO = "relatorio-analise-sensorial-recebimento"
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

TIPO_SOLICITACAO_DIETA = {
    "COMUM": "COMUM",
    "ALTERACAO_UE": "ALTERACAO_UE",
    "ALUNO_NAO_MATRICULADO": "ALUNO_NAO_MATRICULADO",
}

TIPOS_TURMAS_EMEBS = ["INFANTIL", "FUNDAMENTAL"]

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
    "Infantil MANHA": 1,
    "TARDE": 2,
    "Infantil TARDE": 2,
    "INTEGRAL": 3,
    "Infantil INTEGRAL": 3,
    "NOITE": 4,
    "Infantil NOITE": 4,
    "INTERMEDIARIO": 5,
    "VESPERTINO": 6,
    "Programas e Projetos": 7,
    "Solicitações de Alimentação": 8,
    "ETEC": 9,
}

ORDEM_PERIODOS_GRUPOS_CEI = {
    "INTEGRAL": 1,
    "PARCIAL": 2,
    "MANHA": 3,
    "TARDE": 4,
}

ORDEM_PERIODOS_GRUPOS_CEMEI = {
    "INTEGRAL": 1,
    "PARCIAL": 2,
    "Infantil INTEGRAL": 3,
    "Infantil MANHA": 4,
    "Infantil TARDE": 5,
    "Programas e Projetos": 6,
    "Solicitações de Alimentação": 7,
}

ORDEM_CAMPOS = [
    "numero_de_alunos",
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

MAX_COLUNAS = 15

ORDEM_UNIDADES_GRUPO_EMEF = {
    "EMEF": 1,
    "EMEFM": 2,
    "CIEJA": 3,
    "CEU GESTAO": 4,
    "CEU EMEF": 5,
}

ORDEM_HEADERS = {
    "Solicitações de Alimentação": 1,
    "MANHA": 2,
    "TARDE": 3,
    "INTEGRAL": 4,
    "NOITE": 5,
    "INTERMEDIARIO": 6,
    "VESPERTINO": 7,
    "Programas e Projetos": 8,
    "ETEC": 9,
    "DIETA ESPECIAL - TIPO A": 10,
    "DIETA ESPECIAL - TIPO A - ENTERAL / RESTRIÇÃO DE AMINOÁCIDOS": 11,
    "DIETA ESPECIAL - TIPO B": 12,
}


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
