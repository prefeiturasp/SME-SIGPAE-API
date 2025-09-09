import math
import re

from django import template
from django.db.models import QuerySet
from django.template import base as template_base
from django.template.defaultfilters import title as django_title

from sme_sigpae_api.dados_comuns.utils import numero_com_agrupador_de_milhar_e_decimal
from sme_sigpae_api.produto.constants import RELATORIO_RECLAMACOES_PRODUTOS

from ...cardapio.suspensao_alimentacao.models import (
    GrupoSuspensaoAlimentacao,
    SuspensaoAlimentacao,
)
from ...dados_comuns import constants
from ...dados_comuns.fluxo_status import DietaEspecialWorkflow
from ...dados_comuns.models import LogSolicitacoesUsuario
from ...escola.models import Escola
from ...imr.models import (
    FormularioOcorrenciasBase,
    ParametrizacaoOcorrencia,
    TipoOcorrencia,
)
from ...inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoContinua,
    InclusaoAlimentacaoDaCEI,
    InclusaoDeAlimentacaoCEMEI,
)
from ...kit_lanche.models import EscolaQuantidade

register = template.Library()

# Add support for multi-line template tags
template_base.tag_re = re.compile(template_base.tag_re.pattern, re.DOTALL)


@register.filter
def get_attribute(elemento, atributo):
    return getattr(elemento, atributo, False)


@register.filter
def get_element_by_index(indexable, i):
    if i < 0:
        return None
    return indexable[i]


@register.filter
def index_exists(indexable, i):
    return i <= len(indexable)


@register.filter
def check_importada(atributo):
    if atributo:
        return not atributo
    return True


@register.filter
def fim_de_fluxo(logs):
    fim = False
    for log in logs:
        if (
            "neg" in log.status_evento_explicacao
            or "não" in log.status_evento_explicacao
            or "cancel" in log.status_evento_explicacao
        ):  # noqa
            fim = True
    return fim


@register.filter  # noqa C901
def class_css(log):
    classe_css = "pending"
    if log.status_evento_explicacao in [
        "Solicitação Realizada",
        "Escola revisou",
        "DRE validou",
        "DRE revisou",
        "CODAE autorizou",
        "Terceirizada tomou ciência",
        "Escola solicitou cancelamento",
        "CODAE autorizou cancelamento",
        "Terceirizada tomou ciência do cancelamento",
        "CODAE homologou",
        "CODAE autorizou reclamação",
    ]:
        classe_css = "active"
    elif log.status_evento_explicacao in [
        "Escola cancelou",
        "DRE cancelou",
        "Terceirizada cancelou homologação",
        "CODAE suspendeu o produto",
    ]:
        classe_css = "cancelled"
    elif log.status_evento_explicacao in [
        "DRE não validou",
        "CODAE negou",
        "Terceirizada recusou",
        "CODAE negou cancelamento",
        "CODAE não homologou",
    ]:
        classe_css = "disapproved"
    elif log.status_evento_explicacao in [
        "Questionamento pela CODAE",
        "CODAE pediu correção",
        "CODAE pediu análise sensorial",
        "Escola/Nutricionista reclamou do produto",
        "CODAE pediu análise da reclamação",
        "Terceirizada respondeu questionamento",
    ]:
        classe_css = "questioned"
    return classe_css


@register.filter
def or_logs(fluxo, logs):
    return logs if len(logs) > len(fluxo) else fluxo


@register.filter
def observacao_padrao(observacao, palavra="..."):
    return observacao or f"Sem observações por parte da {palavra}"


@register.filter
def aceita_nao_aceita_str(aceitou):
    if aceitou:
        return "Aceitou"
    return "Não aceitou"


@register.filter
def tem_questionamentos(logs):
    return logs.filter(status_evento=LogSolicitacoesUsuario.CODAE_QUESTIONOU).exists()


@register.filter
def tem_cancelamento(logs):
    return logs.filter(
        status_evento__in=[
            LogSolicitacoesUsuario.ESCOLA_CANCELOU,
            LogSolicitacoesUsuario.DRE_NAO_VALIDOU,
            LogSolicitacoesUsuario.CODAE_NEGOU,
            LogSolicitacoesUsuario.DRE_CANCELOU,
        ]
    ).exists()


@register.filter
def tem_cancelamento_parcial(dias):
    return dias.filter(cancelado=True).exists()


@register.filter
def concatena_str(query_set):
    return ", ".join([p.nome for p in query_set])


@register.filter
def concatena_str_por_param(query_set, param):
    return ", ".join([getattr(p, param) for p in query_set])


@register.filter
def concatena_string(lista):
    return ", ".join([p for p in lista])


@register.filter
def concatena_label(query_set):
    label = ""
    for item in query_set:
        label += " e ".join([item.nome])
        if item != list(query_set)[-1]:
            label += ", "
    return label


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_total(dictionary):
    return dictionary.get("total")


@register.filter
def get_dado_mes(dictionary, index):
    return dictionary.get("quantidades")[index]


@register.filter
def numero_pra_mes(indice):
    return {
        0: "Janeiro",
        1: "Fevereiro",
        2: "Março",
        3: "Abril",
        4: "Maio",
        5: "Junho",
        6: "Julho",
        7: "Agosto",
        8: "Setembro",
        9: "Outubro",
        10: "Novembro",
        11: "Dezembro",
    }[indice]


@register.filter
def retira_p_texto(texto):
    texto_sem_primeira_tag = texto[3:]
    texto_sem_tag = texto_sem_primeira_tag[:-5]
    return texto_sem_tag


@register.filter
def formata_data(data):
    return data[:10]


@register.filter
def formata_hora(data):
    return data[10:]


@register.filter
def formata_telefone(telefone):
    ddd = telefone[:2]
    numero = telefone[2:]
    return "(" + ddd + ")" + " " + numero


@register.filter
def retorna_data_do_ultimo_log(logs):
    return logs[-1]["criado_em"][:10]


@register.filter
def retorna_nome_ultimo_log(logs):
    return logs[-1]["usuario"]["nome"]


@register.filter
def retorna_rf_ultimo_log(logs):
    return logs[-1]["usuario"]["registro_funcional"]


@register.filter
def retorna_cargo_ultimo_log(logs):
    return logs[-1]["usuario"]["cargo"]


@register.filter
def retorna_justificativa_ultimo_log(logs):
    justificativa = logs[-1]["justificativa"]
    texto_sem_primeira_tag = justificativa[3:]
    texto_sem_tag = texto_sem_primeira_tag[:-5]
    return texto_sem_tag


@register.filter
def retorn_se_tem_anexo(imagens):
    if len(imagens) > 0:
        return "Sim"
    return "Não"


@register.filter
def verifica_se_tem_anexos(logs):
    if len(logs[-1]["anexos"]) > 0:
        return "Sim"
    return "Não"


@register.filter
def obter_titulo_log_reclamacao(status_evento):
    titulo_log = RELATORIO_RECLAMACOES_PRODUTOS["titulo_log"]
    return titulo_log.get(status_evento, status_evento)


@register.filter
def obter_rotulo_data_log(status_evento):
    rotulo_data_log = RELATORIO_RECLAMACOES_PRODUTOS["rotulo_data_log"]
    return rotulo_data_log.get(status_evento, "Data da reclamação")


@register.filter
def obter_titulo_status_dieta(status):
    titulo_status_dieta = {
        DietaEspecialWorkflow.CODAE_A_AUTORIZAR: "Aguardando Autorização",
        DietaEspecialWorkflow.CODAE_AUTORIZADO: "Autorizada",
        DietaEspecialWorkflow.CODAE_NEGOU_PEDIDO: "Negada",
        DietaEspecialWorkflow.ESCOLA_CANCELOU: "Cancelada",
    }
    return titulo_status_dieta.get(status, "")


@register.filter
def retorna_lote(valor):
    if "LOTE" in valor:
        return valor[5:]
    return valor


@register.simple_tag
def embalagens_filter(embalagens, tipo):
    for emb in embalagens:
        if emb.tipo_embalagem == tipo:
            return emb
    else:
        return False


# LOGS CRONOGRAMA


@register.simple_tag
def get_assinatura_cronograma(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ENVIADO_AO_FORNECEDOR
    ).last()


@register.simple_tag
def get_assinatura_fornecedor(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELO_FORNECEDOR
    ).last()


@register.simple_tag
def get_assinatura_dilog_abastecimento(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELO_DILOG_ABASTECIMENTO
    ).last()


@register.simple_tag
def get_assinatura_codae(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.CRONOGRAMA_ASSINADO_PELA_CODAE
    ).last()


# LOGS FICHA TECNICA


@register.simple_tag
def get_assinatura_fornecedor_ficha(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_ENVIADA_PARA_ANALISE
    ).last()


@register.simple_tag
def get_assinatura_codae_ficha(logs):
    return logs.filter(
        status_evento=LogSolicitacoesUsuario.FICHA_TECNICA_APROVADA
    ).last()


@register.filter
def existe_inclusao_cancelada(solicitacao):
    status_ = (
        solicitacao["status"] if isinstance(solicitacao, dict) else solicitacao.status
    )
    inclusoes_ = (
        solicitacao["datas_intervalo"]
        if isinstance(solicitacao, dict)
        else solicitacao.inclusoes
    )
    return (
        status_ == "ESCOLA_CANCELOU"
        or inclusoes_.filter(cancelado_justificativa__isnull=False)
        .exclude(cancelado_justificativa="")
        .exists()
    )


@register.filter
def eh_inclusao(solicitacao):
    return (
        isinstance(solicitacao, GrupoInclusaoAlimentacaoNormal)
        or isinstance(solicitacao, InclusaoAlimentacaoContinua)
        or isinstance(solicitacao, InclusaoAlimentacaoDaCEI)
        or isinstance(solicitacao, InclusaoDeAlimentacaoCEMEI)
    )


@register.filter
def formatar_cpf(cpf):
    try:
        inicio = cpf[:2]
        fim = cpf[-2:]
        return inicio + "*.***.***-" + fim
    except Exception:
        return cpf


@register.filter
def inclusao_multiplos_cancelamentos(solicitacao):
    multiplos_cancelamentos = (
        len(
            set(
                list(
                    solicitacao.inclusoes.filter(
                        cancelado_justificativa__isnull=False
                    ).values_list("cancelado_justificativa", flat=True)
                )
            )
        )
        > 1
    )
    return multiplos_cancelamentos


@register.filter
def inclusoes_canceladas(solicitacao):
    if solicitacao.status == "ESCOLA_CANCELOU":
        return solicitacao.inclusoes.all()
    return solicitacao.inclusoes.filter(cancelado_justificativa__isnull=False).exclude(
        cancelado_justificativa=""
    )


@register.filter
def formatar_data_solicitacoes_alimentacao(data):
    try:
        return data.strftime("%d/%m/%Y")
    except Exception:
        return data


@register.simple_tag
def get_valor_somatorio_campo_periodo(tabela_somatorio, campo, periodo):
    for item in tabela_somatorio:
        if item["campo"] == campo and item["periodo"] == periodo:
            return item["valor"]
    return "-"


@register.simple_tag
def total_periodo_ou_campo_medicao(tabela_somatorio, periodo_ou_campo):
    total = 0
    for item in tabela_somatorio:
        if item["periodo"] == periodo_ou_campo or item["campo"] == periodo_ou_campo:
            total += item["valor"]
    return total


@register.filter
def get_total_medicao(tabela_somatorio):
    total = 0
    for item in tabela_somatorio:
        total += item["valor"]
    return total


@register.filter
def get_matriculados(uuid, alunos_matriculados):
    periodo = alunos_matriculados["periodo_escolar"]
    try:
        alunos_no_periodo = alunos_matriculados["alunos_por_faixa_etaria"][periodo]
        if alunos_no_periodo and alunos_no_periodo[uuid]:
            return alunos_matriculados["alunos_por_faixa_etaria"][periodo][uuid]
        else:
            return 0
    except KeyError:
        return 0


@register.filter
def get_nao_eh_dia_letivo(dias_letivos, i):
    return not dias_letivos[i]


@register.simple_tag
def aluno_nessa_faixa_etaria(dia, aluno, dias):
    return bool([d for d in dias if d["dia"] == dia and aluno in d["alunos_por_dia"]])


@register.simple_tag
def eh_dia_nao_letivo(dia, escola_nome, mes_ano):
    from workalendar.america import BrazilSaoPauloCity

    from sme_sigpae_api.escola.models import DiaSuspensaoAtividades

    escola = Escola.objects.get(nome=escola_nome)
    mes, ano = mes_ano.split("_")
    eh_dia_letivo = escola.calendario.get(
        data__month=mes, data__year=ano, data__day=dia
    ).dia_letivo
    calendario = BrazilSaoPauloCity()
    feriados = [h[0] for h in calendario.holidays()]
    eh_feriado = [
        feriado for feriado in feriados if feriado.month == mes and feriado.day == dia
    ]
    eh_dia_suspensao = DiaSuspensaoAtividades.objects.filter(
        tipo_unidade=escola.tipo_unidade, data__month=mes, data__year=ano, data__day=dia
    )
    return (not eh_dia_letivo) or eh_feriado or eh_dia_suspensao


@register.simple_tag
def tem_dieta_especial(aluno, alunos_com_dietas_autorizadas):
    return bool(
        [
            aluno_dieta
            for aluno_dieta in alunos_com_dietas_autorizadas
            if aluno.split(" - ")[0] in aluno_dieta["aluno"]
        ]
    )


@register.filter
def get_quantidade_total_colunas(dias_do_mes):
    return len(dias_do_mes) + 2


@register.filter
def get_string_aluno_dieta(aluno, alunos_com_dietas_autorizadas):
    aluno_dieta = [
        aluno_dieta
        for aluno_dieta in alunos_com_dietas_autorizadas
        if aluno.split(" - ")[0] in aluno_dieta["aluno"]
    ][0]
    return f"Aluno com Dieta Especial Autorizada em {aluno_dieta['data_autorizacao']} - {aluno_dieta['tipo_dieta']}"


@register.filter
def get_nao_eh_dia_letivo_cei(dias_letivos, i):
    try:
        return not dias_letivos[i]
    except Exception:
        return False


@register.filter
def get_nome_campo(campo):
    campos = {
        "numero_de_alunos": "Número de Alunos",
        "matriculados": "Matriculados",
        "aprovadas": "Aprovadas",
        "frequencia": "Frequência",
        "solicitado": "Solicitado",
        "consumido": "Consumido",
        "desjejum": "Desjejum",
        "lanche": "Lanche",
        "lanche_4h": "Lanche 4h",
        "refeicao": "Refeição 1ª Oferta",
        "repeticao_refeicao": "Repetição de Refeição",
        "lanche_emergencial": "Lanche Emergencial",
        "kit_lanche": "Kit Lanche",
        "total_refeicoes_pagamento": "Total de Refeições para Pagamento",
        "sobremesa": "Sobremesa 1ª Oferta",
        "repeticao_sobremesa": "Repetição de Sobremesa",
        "total_sobremesas_pagamento": "Total de Sobremesas para Pagamento",
        "2_lanche_4h": "2º Lanche 4h",
        "2_lanche_5h": "2º Lanche 5h",
        "lanche_extra": "Lanche Extra",
        "2_refeicao_1_oferta": "2ª Refeição 1ª Oferta",
        "repeticao_2_refeicao": "Repetição 2ª Refeição",
        "2_sobremesa_1_oferta": "2ª Sobremesa 1ª Oferta",
        "repeticao_2_sobremesa": "Repetição 2ª Sobremesa",
    }
    return campos.get(campo, campo)


def get_dias(observacoes_tuple):
    dias = []
    for obs in observacoes_tuple:
        if obs[0] not in dias:
            dias.append(obs[0])
    return dias


@register.filter
def formatar_observacoes(observacoes, tipo_unidade=None):
    MAX_LINHAS_POR_PAGINA = 22

    def format_observacao(obs):
        obs_list = list(obs)
        obs_list[4] = (
            f"{obs_list[4]} - {obs_list[1]}"
            if obs_list[4] and obs_list[1]
            else obs_list[4] or obs_list[1]
        )
        obs_list[3] = re.sub(r"<.*?>", "", obs_list[3])
        return tuple(obs_list)

    observacoes_tuple = [format_observacao(observacao) for observacao in observacoes]

    order_key = None
    if tipo_unidade == "CEI":
        order_key = constants.ORDEM_PERIODOS_GRUPOS_CEI
    elif tipo_unidade == "CEMEI":
        order_key = constants.ORDEM_PERIODOS_GRUPOS_CEMEI
    else:
        order_key = constants.ORDEM_PERIODOS_GRUPOS

    dias = get_dias(observacoes_tuple)

    def order_by_periodo(obs):
        return order_key[obs[4]]

    observacoes_ordenadas_corretamente = []
    for dia in dias:
        obs_for_dia = [obs for obs in observacoes_tuple if obs[0] == dia]
        observacoes_ordenadas_corretamente.extend(
            sorted(obs_for_dia, key=order_by_periodo)
        )

    num_observacoes = len(observacoes_ordenadas_corretamente)
    paginated_observacoes = [
        observacoes_ordenadas_corretamente[i : i + MAX_LINHAS_POR_PAGINA]
        for i in range(0, num_observacoes, MAX_LINHAS_POR_PAGINA)
    ]

    return paginated_observacoes


@register.filter
def str_qtd_paginas_tabela(escolas_quantidades):
    qtd_paginas = math.ceil(len(escolas_quantidades) / 10)
    return "".join([str(i) for i in range(0, qtd_paginas)])


@register.filter
def smart_slice(escolas_quantidades, idx):
    idx = int(idx)
    list_uuids = [esc["uuid"] for esc in escolas_quantidades]
    qs = EscolaQuantidade.objects.filter(uuid__in=list_uuids)
    return qs[10 * idx : 10 * (idx + 1)]


@register.filter
def get_total_pages(tabela):
    total_pages = math.ceil(len(tabela) / 30)
    return range(total_pages)


@register.filter
def slice_table(tabela, index):
    return tabela[index * 30 : (index * 30) + 30]


@register.filter
def build_rows_faixas_etarias(tabela):
    html_output = []
    index_inicial = 0
    for _, campos_list in tabela["categorias_dos_periodos"].items():
        for campos in campos_list:
            numero_campos = campos["numero_campos"] + 1
            faixas_limite = tabela["faixas_etarias"][
                index_inicial : index_inicial + numero_campos
            ]
            for faixa in faixas_limite:
                if faixa == "total":
                    html_output.append('<th class="faixa-etaria">Total do Dia</th>')
                else:
                    if campos["categoria"] == "ALIMENTAÇÃO":
                        html_output.append("<th>Matriculados</th><th>Frequência</th>")
                    else:
                        html_output.append("<th>Aprovadas</th><th>Frequência</th>")
            index_inicial += numero_campos
    return "".join(html_output)


@register.filter
def build_headers_faixas_etarias(tabela):
    html_output = []
    faixas_etarias = tabela["faixas_etarias"]
    colunas = faixas_etarias.copy()
    campos = tabela["nomes_campos"]

    if campos and faixas_etarias:
        colunas.extend([""] * len(campos))

    for faixa in colunas:
        if faixa == "total" or faixa == "":
            html_output.append('<th  class="faixa-etaria" colspan="1"></th>')
        else:
            html_output.append(f'<th class="faixa-etaria" colspan="2">{faixa}</th>')
    return "".join(html_output)


@register.filter
def check_tipo_usuario(tipo_usuario):
    return tipo_usuario in [
        constants.TIPO_USUARIO_ESCOLA,
        constants.TIPO_USUARIO_DIRETORIA_REGIONAL,
        constants.TIPO_USUARIO_TERCEIRIZADA,
        constants.TIPO_USUARIO_NUTRISUPERVISOR,
        constants.TIPO_USUARIO_NUTRIMANIFESTACAO,
        constants.TIPO_USUARIO_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        constants.TIPO_USUARIO_CODAE_GABINETE,
    ]


@register.filter
def multiply(valor, multiplicador):
    return round(int(valor) * multiplicador)


@register.filter
def relatorio_adesao_total_servido(alimentacoes):
    return sum([totais["total_servido"] for totais in alimentacoes.values()])


@register.filter
def relatorio_adesao_total_frequencia(alimentacoes):
    return sum([totais["total_frequencia"] for totais in alimentacoes.values()])


@register.filter
def relatorio_adesao_total_adesao(alimentacoes):
    total_servido = relatorio_adesao_total_servido(alimentacoes)
    total_frequencia = relatorio_adesao_total_frequencia(alimentacoes)
    return round(total_servido / total_frequencia, 4)


@register.filter
def numero_para_milhar(valor):
    return "{0:,}".format(valor).replace(",", ".")


@register.filter
def numero_para_porcentagem(valor):
    return f"{round(valor * 100, 4)}%"


@register.filter
def get_colspan(periodo):
    periodo_colsapn = {
        "TIPOS DE ALIMENTAÇÃO": 2,
        "DIETAS TIPO A / ENTERAL / REST. DE AMINOÁCIDOS": 2,
        "DIETAS TIPO B": 2,
        "MANHA": 1,
        "TARDE": 1,
        "INTEGRAL": 1,
        "PROGRAMAS E PROJETOS": 1,
        "SOLICITAÇÕES DE ALIMENTAÇÃO": 2,
        "TOTAL": 1,
        "NOITE": 1,
        "ETEC": 1,
        "Infantil INTEGRAL": 1,
        "Infantil MANHA": 1,
        "Infantil TARDE": 1,
    }

    return periodo_colsapn.get(periodo.upper())


@register.filter
def get_nome_header(nome):
    nomes = {
        "MANHA": "MANHÃ",
        "NOITE": "NOITE/EJA",
        "TIPO A": "DIETAS TIPO A / ENTERAL / REST. DE AMINOÁCIDOS",
        "TIPO B": "DIETAS TIPO B",
        "Infantil INTEGRAL": "INTEGRAL",
        "Infantil MANHA": "MANHÃ",
        "Infantil TARDE": "TARDE",
    }

    return nomes.get(nome, nome.upper())


@register.filter
def get_nome_categoria(nome):
    nomes = {
        "DIETA ESPECIAL - TIPO A": "DIETA TIPO A",
        "DIETA ESPECIAL - TIPO B": "DIETA TIPO B",
    }

    return nomes.get(nome, nome.upper())


@register.filter
def agrupador_milhar_com_decimal(value: int | float) -> str:
    return numero_com_agrupador_de_milhar_e_decimal(value)


@register.filter
def get_resposta_tipo_ocorrencia(
    tipo_ocorrencia: TipoOcorrencia, formulario_base: FormularioOcorrenciasBase
):
    return tipo_ocorrencia.get_resposta(formulario_base)


@register.filter
def get_quantidade_grupos_tipo_ocorrencia(
    tipo_ocorrencia: TipoOcorrencia, formulario_base: FormularioOcorrenciasBase
):
    return tipo_ocorrencia.quantidade_grupos(formulario_base)


@register.filter
def get_descricao_ocorrencia_nao_se_aplica(
    tipo_ocorrencia: TipoOcorrencia, formulario_base: FormularioOcorrenciasBase
):
    descricao = tipo_ocorrencia.ocorrencias_nao_se_aplica.get(
        formulario_base=formulario_base
    ).descricao
    return descricao


@register.simple_tag
def get_rowspan(
    tipo_ocorrencia: TipoOcorrencia,
    formulario_base: FormularioOcorrenciasBase,
    tipos_ocorrencia: QuerySet[TipoOcorrencia],
):
    tipos_ocorrencia_mesma_posicao = tipos_ocorrencia.filter(
        categoria=tipo_ocorrencia.categoria, posicao=tipo_ocorrencia.posicao
    )
    if tipos_ocorrencia_mesma_posicao.count() > 1:
        rowspan = tipos_ocorrencia_mesma_posicao.count()
        for tipo_ocorrencia_ in tipos_ocorrencia_mesma_posicao:
            if "Não" in tipo_ocorrencia_.get_resposta(formulario_base):
                rowspan += 1
        return rowspan
    else:
        if "Não" in tipo_ocorrencia.get_resposta(formulario_base):
            return 2
        return 1


@register.simple_tag
def get_resposta_str(
    parametrizacao: ParametrizacaoOcorrencia,
    formulario_base: FormularioOcorrenciasBase,
    grupo: int,
) -> str:
    return parametrizacao.get_resposta_str(formulario_base, grupo)


@register.simple_tag
def calcular_index(index_loop: int, tipos_ocorrencia: QuerySet[TipoOcorrencia]) -> int:
    indice = 1
    for index, tipo_ocorrencia in enumerate(tipos_ocorrencia[:index_loop]):
        if index > 0 and (
            tipo_ocorrencia.categoria != tipos_ocorrencia[index - 1].categoria
            or tipo_ocorrencia.posicao != tipos_ocorrencia[index - 1].posicao
        ):
            indice += 1
    return indice


@register.filter
def existe_suspensoes_cancelada(solicitacao: GrupoSuspensaoAlimentacao) -> bool:
    """
    Verifica se uma solicitação possui suspensões de alimentação canceladas.
    """
    status_ = (
        solicitacao["status"] if isinstance(solicitacao, dict) else solicitacao.status
    )

    return (
        status_ == "ESCOLA_CANCELOU"
        or solicitacao.suspensoes_alimentacao.filter(
            cancelado_justificativa__isnull=False
        )
        .exclude(cancelado_justificativa="")
        .exists()
    )


@register.filter
def suspensoes_canceladas(
    solicitacao: GrupoSuspensaoAlimentacao,
) -> SuspensaoAlimentacao:
    """
    Retorna todas as suspensões de alimentação canceladas para uma solicitação.
    """
    if solicitacao.status == "ESCOLA_CANCELOU":
        return solicitacao.suspensoes_alimentacao.all()
    return solicitacao.suspensoes_alimentacao.filter(
        cancelado_justificativa__isnull=False
    ).exclude(cancelado_justificativa="")


@register.filter
def sum_faixas(faixa_etaria):
    return sum(faixa["autorizadas"] for faixa in faixa_etaria)


@register.filter
def soma_dietas_periodo_cemei(periodo_obj):
    if not isinstance(periodo_obj, dict):
        return 0

    total = periodo_obj.get("autorizadas_infantil", 0)

    por_idade = periodo_obj.get("por_idade", [])
    for faixa in por_idade:
        total += faixa.get("autorizadas", 0)

    return total


@register.filter
def soma_autorizadas_emebs(periodo):
    infantil = periodo.get("autorizadas_infantil", 0)
    fundamental = periodo.get("autorizadas_fundamental", 0)
    return infantil + fundamental


@register.filter
def title_personalizado(value):
    titled_value = django_title(str(value))

    if titled_value == "Manha":
        return "Manhã"
    return titled_value


@register.simple_tag(takes_context=True)
def next_section(context):
    """
    Incrementa o contador de seções e retorna o valor atualizado.
    """
    if "section_number" not in context:
        context["section_number"] = 1
    else:
        context["section_number"] += 1
    return context["section_number"]

@register.filter
def replace(value, arg):
    """
    Filtro de replace
    Use da seguinte forma: `{{ "aaa"|replace:"a|b" }}`
    a = valor original
    b = valor que será substituído
    """
    if len(arg.split('|')) != 2:
        return value

    what, to = arg.split('|')
    return value.replace(what, to)
