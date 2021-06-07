import datetime

import environ
from workalendar.america import BrazilSaoPauloCity

calendar = BrazilSaoPauloCity()
env = environ.Env()


def obter_dias_uteis_apos_hoje(quantidade_dias: int):
    """Retorna o próximo dia útil após quantidade_dias."""
    dia = datetime.date.today()

    return calendar.add_working_days(dia, quantidade_dias)


DJANGO_EOL_API_TOKEN = env('DJANGO_EOL_API_TOKEN')
DJANGO_EOL_API_URL = env('DJANGO_EOL_API_URL')

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

SEM_FILTRO = 'sem_filtro'
DAQUI_A_SETE_DIAS = 'daqui_a_7_dias'
DAQUI_A_TRINTA_DIAS = 'daqui_a_30_dias'

PEDIDOS_CODAE = 'pedidos-codae'
PEDIDOS_TERCEIRIZADA = 'pedidos-terceirizadas'
PEDIDOS_DRE = 'pedidos-diretoria-regional'
FILTRO_PADRAO_PEDIDOS = f'(?P<filtro_aplicado>({SEM_FILTRO}|{DAQUI_A_SETE_DIAS}|{DAQUI_A_TRINTA_DIAS})+)'

RASCUNHO = 'rascunho'
CODAE_PENDENTE_HOMOLOGACAO = 'codae_pendente_homologacao'  # INICIO
CODAE_HOMOLOGADO = 'codae_homologado'
CODAE_NAO_HOMOLOGADO = 'codae_nao_homologado'
CODAE_QUESTIONADO = 'codae_questionado'
CODAE_PEDIU_ANALISE_SENSORIAL = 'codae_pediu_analise_sensorial'
TERCEIRIZADA_CANCELOU = 'terceirizada_cancelou'
CODAE_SUSPENDEU = 'codae_suspendeu'
ESCOLA_OU_NUTRICIONISTA_RECLAMOU = 'escola_ou_nutricionista_reclamou'
CODAE_PEDIU_ANALISE_RECLAMACAO = 'codae_pediu_analise_reclamacao'
CODAE_AUTORIZOU_RECLAMACAO = 'codae_autorizou_reclamacao'

FILTRO_STATUS_HOMOLOGACAO = (f'(?P<filtro_aplicado>({RASCUNHO}|{CODAE_PENDENTE_HOMOLOGACAO}|{CODAE_HOMOLOGADO}|'
                             f'{CODAE_NAO_HOMOLOGADO}|{CODAE_QUESTIONADO}|{CODAE_PEDIU_ANALISE_SENSORIAL}|'
                             f'{TERCEIRIZADA_CANCELOU}|{CODAE_SUSPENDEU}|{ESCOLA_OU_NUTRICIONISTA_RECLAMOU}|'
                             f'{CODAE_PEDIU_ANALISE_RECLAMACAO}|{CODAE_AUTORIZOU_RECLAMACAO})+)')

RELATORIO = 'relatorio'
RELATORIO_ANALISE = 'relatorio-analise-sensorial'
RELATORIO_SUSPENSOS = 'relatorio-produtos-suspensos'
RELATORIO_RECEBIMENTO = 'relatorio-analise-sensorial-recebimento'
PROTOCOLO = 'protocolo'

#
# FLUXO, usados nas actions de transição de status nas viewsets dos pedidos/informações do sistema
#
# TODO: trocar pedido por solicitação
ESCOLA_INICIO_PEDIDO = 'inicio-pedido'
ESCOLA_REVISA_PEDIDO = 'escola-revisa-pedido'
ESCOLA_CANCELA = 'escola-cancela-pedido-48h-antes'
ESCOLA_INFORMA_SUSPENSAO = 'informa-suspensao'
ESCOLA_SOLICITA_INATIVACAO = 'escola-solicita-inativacao'

ESCOLA_CANCELA_DIETA_ESPECIAL = 'escola-cancela-dieta-especial'

DRE_INICIO_PEDIDO = 'inicio-pedido'
DRE_VALIDA_PEDIDO = 'diretoria-regional-valida-pedido'
DRE_NAO_VALIDA_PEDIDO = 'diretoria-regional-nao-valida-pedido'
DRE_PEDE_REVISAO = 'diretoria-regional-pede-revisao'
DRE_REVISA_PEDIDO = 'diretoria-regional-revisa'
DRE_CANCELA = 'diretoria-regional-cancela'

CODAE_AUTORIZA_PEDIDO = 'codae-autoriza-pedido'
CODAE_AUTORIZA_INATIVACAO = 'codae-autoriza-inativacao'
CODAE_NEGA_PEDIDO = 'codae-cancela-pedido'
CODAE_NEGA_INATIVACAO = 'codae-nega-inativacao'
CODAE_PEDE_REVISAO = 'codae-pediu-revisao'
CODAE_QUESTIONA_PEDIDO = 'codae-questiona-pedido'
CODAE_HOMOLOGA = 'codae-homologa'
CODAE_NAO_HOMOLOGA = 'codae-nao-homologa'
CODAE_PEDE_ANALISE_SENSORIAL = 'codae-pede-analise-sensorial'
TERCEIRIZADA_INATIVA_HOMOLOGACAO = 'terceirizada-inativa'
ESCOLA_OU_NUTRI_RECLAMA = 'escola-ou-nutri-reclama'
SUSPENDER_PRODUTO = 'suspender'
ATIVAR_PRODUTO = 'ativar'
GERAR_PDF = 'gerar-pdf'
AGUARDANDO_ANALISE_SENSORIAL = 'aguardando-analise-sensorial'
TERCEIRIZADA_RESPONDE_ANALISE_SENSORIAL = 'terceirizada-responde-analise-sensorial'
TERCEIRIZADA_RESPONDE_RECLAMACAO = 'terceirizada-responde-reclamacao'
TERCEIRIZADA_CANCELOU_SOLICITACAO_HOMOLOGACAO = 'cancela-solicitacao-homologacao'
TERCEIRIZADA_RESPONDE = 'terceirizada-responde'
CODAE_PEDE_ANALISE_RECLAMACAO = 'codae-pede-analise-reclamacao'
CODAE_RECUSA_RECLAMACAO = 'codae-recusa-reclamacao'
CODAE_ACEITA_RECLAMACAO = 'codae-aceita-reclamacao'
CODAE_ACEITA = 'codae-aceita'
CODAE_RECUSA = 'codae-recusa'
CODAE_QUESTIONA = 'codae-questiona'
CODAE_RESPONDE = 'codae-responde'

TERCEIRIZADA_RESPONDE_QUESTIONAMENTO = 'terceirizada-responde-questionamento'
TERCEIRIZADA_TOMOU_CIENCIA = 'terceirizada-toma-ciencia'
TERCEIRIZADA_TOMOU_CIENCIA_INATIVACAO = 'terceirizada-toma-ciencia-inativacao'

#
# FILTROS
#

SOLICITACOES_DO_USUARIO = 'minhas-solicitacoes'

#
# PERFIS
#
DIRETOR = 'DIRETOR'
DIRETOR_CEI = 'DIRETOR_CEI'
COORDENADOR_ESCOLA = 'COORDENADOR_ESCOLA'
ADMINISTRADOR_ESCOLA = 'ADMINISTRADOR_ESCOLA'
ADMINISTRADOR_ESCOLA_ABASTECIMENTO = 'ADMINISTRADOR_ESCOLA_ABASTECIMENTO'
COGESTOR = 'COGESTOR'
SUPLENTE = 'SUPLENTE'
ADMINISTRADOR_DRE = 'ADMINISTRADOR_DRE'
COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA = 'COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA'
ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA = 'ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA'
COORDENADOR_DIETA_ESPECIAL = 'COORDENADOR_DIETA_ESPECIAL'
ADMINISTRADOR_DIETA_ESPECIAL = 'ADMINISTRADOR_DIETA_ESPECIAL'
COORDENADOR_GESTAO_PRODUTO = 'COORDENADOR_GESTAO_PRODUTO'
COORDENADOR_LOGISTICA = 'COORDENADOR_LOGISTICA'
ADMINISTRADOR_GESTAO_PRODUTO = 'ADMINISTRADOR_GESTAO_PRODUTO'
NUTRI_ADMIN_RESPONSAVEL = 'NUTRI_ADMIN_RESPONSAVEL'
ADMINISTRADOR_TERCEIRIZADA = 'ADMINISTRADOR_TERCEIRIZADA'
ADMINISTRADOR_DISTRIBUIDORA = 'ADMINISTRADOR_DISTRIBUIDORA'
COORDENADOR_SUPERVISAO_NUTRICAO = 'COORDENADOR_SUPERVISAO_NUTRICAO'
ADMINISTRADOR_SUPERVISAO_NUTRICAO = 'ADMINISTRADOR_SUPERVISAO_NUTRICAO'

#
# TIPOS DE USUARIO
#
TIPO_USUARIO_TERCEIRIZADA = 'terceirizada'
TIPO_USUARIO_GESTAO_PRODUTO = 'gestao_produto'
TIPO_USUARIO_ESCOLA = 'escola'

#
# DOMINIOS USADOS APENAS EM DESENVOLVIMENTO
#
DOMINIOS_DEV = [
    '@admin.com',
    '@dev.prefeitura.sp.gov.br',
    '@emailteste.sme.prefeitura.sp.gov.br',
]

# CACHE
TEMPO_CACHE_6H = 60 * 60 * 6
TEMPO_CACHE_1H = 60 * 60 * 6

DEZ_MB = 10485760


CODAE_AUTORIZOU_RECLAMACAO = 'CODAE autorizou reclamação'
CODAE_RECUSOU_RECLAMACAO = 'CODAE recusou reclamação'
CODAE_QUESTIONOU_TERCEIRIZADA = 'CODAE questionou terceirizada sobre reclamação'
CODAE_RESPONDEU_RECLAMACAO = 'CODAE respondeu ao reclamante da reclamação'
TERCEIRIZADA_RESPONDEU_RECLAMACAO = 'Terceirizada respondeu a reclamação'

TIPO_SOLICITACAO_DIETA = {'COMUM': 'COMUM',
                          'ALTERACAO_UE': 'ALTERACAO_UE',
                          'ALUNO_NAO_MATRICULADO': 'ALUNO_NAO_MATRICULADO'}
