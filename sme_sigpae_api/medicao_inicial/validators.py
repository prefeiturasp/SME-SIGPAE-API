import calendar
import datetime
import unicodedata

from django.db.models import Q
from workalendar.america import BrazilSaoPauloCity

from sme_sigpae_api.dados_comuns.utils import get_ultimo_dia_mes

from ..cardapio.base.models import (
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from ..dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
from ..escola.models import (
    DiaCalendario,
    FaixaEtaria,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
)
from ..inclusao_alimentacao.models import (
    GrupoInclusaoAlimentacaoNormal,
    InclusaoAlimentacaoNormal,
    InclusaoDeAlimentacaoCEMEI,
)
from ..paineis_consolidados.models import SolicitacoesEscola
from .api.constants import ALIMENTACOES_LANCAMENTOS_ESPECIAIS
from .models import CategoriaMedicao, PermissaoLancamentoEspecial, ValorMedicao
from .utils import (
    agrupa_permissoes_especiais_por_dia,
    get_linhas_da_tabela,
    get_lista_dias_inclusoes_ceu_gestao,
    get_periodos_escolares_comuns_com_inclusoes_normais,
    incluir_lanche,
)

calendario = BrazilSaoPauloCity()


def get_lista_dias_letivos(solicitacao, escola):
    dias_letivos = DiaCalendario.objects.filter(
        data__month=int(solicitacao.mes),
        data__year=int(solicitacao.ano),
        escola=escola,
        dia_letivo=True,
    )
    dias_letivos = list(set(dias_letivos.values_list("data__day", flat=True)))
    return [
        str(dia) if not len(str(dia)) == 1 else ("0" + str(dia)) for dia in dias_letivos
    ]


def erros_unicos(lista_erros):
    return list(map(dict, set(tuple(sorted(erro.items())) for erro in lista_erros)))


def buscar_valores_lancamento_alimentacoes(
    linhas_da_tabela,
    solicitacao,
    periodo_escolar,
    dias_letivos,
    categoria_medicao,
    lista_erros,
):
    periodo_com_erro = False
    for nome_campo in linhas_da_tabela:
        valores_da_medicao = (
            ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo=nome_campo,
                medicao__periodo_escolar=periodo_escolar,
                dia__in=dias_letivos,
                categoria_medicao=categoria_medicao,
            )
            .exclude(valor=None)
            .values_list("dia", flat=True)
        )
        permissoes_especiais = get_permissoes_especiais_da_solicitacao(
            solicitacao, solicitacao.escola, periodo_escolar
        )
        permissoes_especiais_agrupadas_por_dia = agrupa_permissoes_especiais_por_dia(
            permissoes_especiais, solicitacao.mes, solicitacao.ano
        )
        valores_da_medicao = list(set(valores_da_medicao))
        if len(valores_da_medicao) != len(dias_letivos):
            diferenca = list(set(dias_letivos) - set(valores_da_medicao))
            for dia_sem_preenchimento in diferenca:
                if nome_campo in ALIMENTACOES_LANCAMENTOS_ESPECIAIS and (
                    (
                        not permissoes_especiais_agrupadas_por_dia.get(
                            dia_sem_preenchimento
                        )
                    )
                ):
                    continue
                valor_observacao = ValorMedicao.objects.filter(
                    medicao__solicitacao_medicao_inicial=solicitacao,
                    nome_campo="observacao",
                    medicao__periodo_escolar=periodo_escolar,
                    dia=dia_sem_preenchimento,
                    categoria_medicao=categoria_medicao,
                ).exclude(valor=None)
                periodo_com_erro = checa_valor_observacao(
                    valor_observacao, periodo_com_erro
                )
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": periodo_escolar.nome,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def buscar_valores_lancamento_alimentacoes_emei_cemei(
    lista_erros,
    dias_letivos,
    categoria_medicao,
    medicao,
    alimentacoes_vinculadas,
    permissoes_especiais,
    mes,
    ano,
):
    periodo_com_erro = False
    dias_letivos = [str(x).rjust(2, "0") for x in dias_letivos]
    permissoes_especiais_agrupadas_por_dia = agrupa_permissoes_especiais_por_dia(
        permissoes_especiais, mes, ano
    )
    for dia in dias_letivos:
        permissao_do_dia = permissoes_especiais_agrupadas_por_dia.get(dia)
        alimentacoes_permitidas_no_dia = (
            permissao_do_dia["alimentacoes"] if permissao_do_dia else []
        )
        alimentacoes = alimentacoes_vinculadas + alimentacoes_permitidas_no_dia
        linhas_da_tabela = get_linhas_da_tabela(alimentacoes)
        for nome_campo in linhas_da_tabela:
            valor_da_medicao = ValorMedicao.objects.filter(
                medicao=medicao,
                nome_campo=nome_campo,
                dia=dia,
                categoria_medicao=categoria_medicao,
            ).exclude(valor=None)
            if not valor_da_medicao.exists():
                valor_observacao = ValorMedicao.objects.filter(
                    medicao=medicao,
                    nome_campo="observacao",
                    dia=dia,
                    categoria_medicao=categoria_medicao,
                ).exclude(valor=None)
                if not valor_observacao.exists():
                    periodo_com_erro = True
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": medicao.nome_periodo_grupo,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def validate_lancamento_alimentacoes_medicao(solicitacao, lista_erros):
    escola = solicitacao.escola
    tipo_unidade = escola.tipo_unidade
    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos = get_lista_dias_letivos(solicitacao, escola)
    for periodo_escolar in escola.periodos_escolares(solicitacao.ano):
        alimentacoes_permitidas = get_alimentacoes_permitidas(
            solicitacao, escola, periodo_escolar
        )
        vinculo = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
                tipo_unidade_escolar=tipo_unidade, periodo_escolar=periodo_escolar
            )
        )
        alimentacoes_vinculadas = vinculo.tipos_alimentacao.exclude(
            nome="Lanche Emergencial"
        )
        alimentacoes_vinculadas = list(
            set(alimentacoes_vinculadas.values_list("nome", flat=True))
        )
        alimentacoes = alimentacoes_vinculadas + alimentacoes_permitidas
        linhas_da_tabela = get_linhas_da_tabela(alimentacoes)
        lista_erros = buscar_valores_lancamento_alimentacoes(
            linhas_da_tabela,
            solicitacao,
            periodo_escolar,
            dias_letivos,
            categoria_medicao,
            lista_erros,
        )
    return erros_unicos(lista_erros)


def validate_lancamento_alimentacoes_medicao_emei_cemei(
    solicitacao, lista_erros, escola, categoria_medicao, dias_letivos, medicao
):
    for periodo_escolar in escola.periodos_escolares(solicitacao.ano):
        if periodo_escolar.nome.upper() in medicao.nome_periodo_grupo.upper():
            permissoes_especiais = get_permissoes_especiais_da_solicitacao(
                solicitacao, escola, periodo_escolar
            )
            vinculo = (
                VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
                    tipo_unidade_escolar__iniciais="EMEI",
                    periodo_escolar=periodo_escolar,
                )
            )
            alimentacoes_vinculadas = vinculo.tipos_alimentacao.exclude(
                nome="Lanche Emergencial"
            )
            alimentacoes_vinculadas = list(
                set(alimentacoes_vinculadas.values_list("nome", flat=True))
            )
            lista_erros = buscar_valores_lancamento_alimentacoes_emei_cemei(
                lista_erros,
                dias_letivos,
                categoria_medicao,
                medicao,
                alimentacoes_vinculadas,
                permissoes_especiais,
                solicitacao.mes,
                solicitacao.ano,
            )
    return erros_unicos(lista_erros)


def lista_erros_com_periodo(lista_erros, medicao, tipo_erro):
    return next(
        (
            erro
            for erro in lista_erros
            if (
                erro["periodo_escolar"] == medicao.periodo_escolar.nome
                if medicao.periodo_escolar
                else medicao.grupo.nome
            )
            and tipo_erro in erro["erro"]
        ),
        None,
    )


def get_quantidade_dietas_autorizadas(medicao, ano, mes, dia, faixa_etaria):
    escola = medicao.solicitacao_medicao_inicial.escola
    periodo = medicao.periodo_escolar
    quantidade_dietas_autorizadas = sum(
        LogQuantidadeDietasAutorizadasCEI.objects.filter(
            escola=escola,
            data__month=mes,
            data__year=ano,
            data__day=dia,
            periodo_escolar=periodo,
            faixa_etaria=faixa_etaria,
        ).values_list("quantidade", flat=True)
    )
    return quantidade_dietas_autorizadas


def validate_lancamento_alimentacoes_medicao_cei_faixas_etarias(
    faixas_etarias,
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    periodo_com_erro,
    valores_medicao_,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    FAIXA_ETARIA_ID_INDEX = 2
    QUANTIDADE_INDEX = 3

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 3

    for faixa_etaria in faixas_etarias:
        if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
            continue
        log = next(
            (
                log_
                for log_ in logs_
                if (
                    log_[DATA_INDEX] == datetime.date(int(ano), int(mes), int(dia))
                    and log_[PERIODO_ESCOLAR_ID_INDEX] == medicao.periodo_escolar.id
                    and log_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                )
            ),
            None,
        )
        quantidade = log[QUANTIDADE_INDEX] if log else 0
        quantidade_dietas_autorizadas = get_quantidade_dietas_autorizadas(
            medicao, ano, mes, dia, faixa_etaria
        )
        if quantidade == 0 or (quantidade - quantidade_dietas_autorizadas <= 0):
            continue
        valor_medicao = next(
            (
                valor_medicao_
                for valor_medicao_ in valores_medicao_
                if (
                    valor_medicao_[NOME_CAMPO_INDEX] == "frequencia"
                    and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                    and valor_medicao_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                    and valor_medicao_[DIA_ID] == f"{dia:02d}"
                )
            ),
            None,
        )
        if not valor_medicao:
            periodo_com_erro = True
    return periodo_com_erro


def validate_lancamento_alimentacoes_medicao_cei_cemei_faixas_etarias(
    faixas_etarias,
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    periodo_com_erro,
    valores_medicao_,
    inclusoes_,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    FAIXA_ETARIA_ID_INDEX = 2
    QUANTIDADE_INDEX = 3

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 3

    for faixa_etaria in faixas_etarias:
        if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
            continue
        log = next(
            (
                log_
                for log_ in logs_
                if (
                    log_[DATA_INDEX] == datetime.date(int(ano), int(mes), int(dia))
                    and log_[PERIODO_ESCOLAR_ID_INDEX] == medicao.periodo_escolar.id
                    and log_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                )
            ),
            None,
        )
        quantidade = log[QUANTIDADE_INDEX] if log else 0
        if quantidade == 0:
            continue
        valor_medicao = next(
            (
                valor_medicao_
                for valor_medicao_ in valores_medicao_
                if (
                    valor_medicao_[NOME_CAMPO_INDEX] == "frequencia"
                    and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                    and valor_medicao_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                    and valor_medicao_[DIA_ID] == f"{dia:02d}"
                )
            ),
            None,
        )
        tem_inclusao_para_a_faixa_etaria = inclusoes_.filter(
            quantidade_alunos_cei_da_inclusao_cemei__faixa_etaria=faixa_etaria
        ).exists()
        if tem_inclusao_para_a_faixa_etaria and not valor_medicao:
            periodo_com_erro = True
    return periodo_com_erro


def build_nomes_campos_dietas_emef(escola, categoria, medicao):
    tipos_alimentacao = list(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar=medicao.periodo_escolar,
        )
        .values_list("tipos_alimentacao__nome", flat=True)
        .distinct()
    )

    nomes_campos = ["frequencia"]
    if "Lanche" in tipos_alimentacao:
        nomes_campos.append("lanche")
    if "Lanche 4h" in tipos_alimentacao:
        nomes_campos.append("lanche_4h")
    if "Refeição" in tipos_alimentacao and "ENTERAL" in categoria.nome:
        nomes_campos.append("refeicao")
    return nomes_campos


def build_nomes_campos_inclusoes_dietas_emef(escola, categoria, inclusoes, medicao):
    tipos_alimentacao = list(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar__in=escola.periodos_escolares(
                medicao.solicitacao_medicao_inicial.ano
            ),
        )
        .values_list("tipos_alimentacao__nome", flat=True)
        .distinct()
    )

    nomes_campos = ["frequencia"]
    if (
        "Lanche" in tipos_alimentacao
        and inclusoes.filter(
            quantidades_por_periodo__periodo_escolar=medicao.periodo_escolar,
            quantidades_por_periodo__tipos_alimentacao__nome="Lanche",
        ).exists()
    ):
        nomes_campos.append("lanche")
    if (
        "Lanche 4h" in tipos_alimentacao
        and inclusoes.filter(
            quantidades_por_periodo__periodo_escolar=medicao.periodo_escolar,
            quantidades_por_periodo__tipos_alimentacao__nome="Lanche 4h",
        ).exists()
    ):
        nomes_campos.append("lanche_4h")
    if (
        "Refeição" in tipos_alimentacao
        and "ENTERAL" in categoria.nome
        and inclusoes.filter(
            quantidades_por_periodo__periodo_escolar=medicao.periodo_escolar,
            quantidades_por_periodo__tipos_alimentacao__nome="Refeição",
        ).exists()
    ):
        nomes_campos.append("refeicao")
    return nomes_campos


def build_nomes_campos_dietas_emei_cemei(medicao, categoria):
    tipos_alimentacao = (
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            tipo_unidade_escolar__iniciais="EMEI",
            periodo_escolar__nome__in=medicao.nome_periodo_grupo.upper().split(),
        ).values_list("tipos_alimentacao__nome", flat=True)
    )
    nomes_campos = ["frequencia"]
    if "Lanche" in tipos_alimentacao:
        nomes_campos.append("lanche")
    if "Lanche 4h" in tipos_alimentacao:
        nomes_campos.append("lanche_4h")
    if "Refeição" in tipos_alimentacao and "ENTERAL" in categoria.nome:
        nomes_campos.append("refeicao")
    return nomes_campos


def get_nomes_campos_emef_emebs_dietas(inclusoes, escola, categoria, medicao):
    if inclusoes:
        return build_nomes_campos_inclusoes_dietas_emef(
            escola, categoria, inclusoes, medicao
        )
    else:
        return build_nomes_campos_dietas_emef(escola, categoria, medicao)


def validate_lancamento_alimentacoes_inclusoes_emebs_dietas(
    nomes_campos,
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    classificacoes,
    valores_medicao_,
    escola,
    periodo_com_erro,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    QUANTIDADE_INDEX = 2
    CLASSIFICACAO_ID_INDEX = 3
    INFANTIL_OU_FUNDAMENTAL_INDEX = 4

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 2
    INFANTIL_OU_FUNDAMENTAL_VALOR_INDEX = 3

    tipos_alunos = (
        LogQuantidadeDietasAutorizadas.objects.filter(
            escola=escola,
            data__year=ano,
            data__month=mes,
            periodo_escolar=medicao.periodo_escolar,
        )
        .exclude(Q(quantidade=0) | Q(infantil_ou_fundamental="N/A"))
        .values_list("infantil_ou_fundamental", flat=True)
    )
    tipos_alunos = list(set(tipos_alunos))
    for tipo_aluno in tipos_alunos:
        for nome_campo in nomes_campos:
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            quantidade = 0
            for classificacao in classificacoes:
                log = next(
                    (
                        log_
                        for log_ in logs_
                        if (
                            log_[DATA_INDEX]
                            == datetime.date(int(ano), int(mes), int(dia))
                            and (
                                log_[PERIODO_ESCOLAR_ID_INDEX]
                                == medicao.periodo_escolar.id
                                if medicao.periodo_escolar
                                else None
                            )
                            and log_[CLASSIFICACAO_ID_INDEX] == classificacao.id
                            and log_[INFANTIL_OU_FUNDAMENTAL_INDEX] == tipo_aluno
                        )
                    ),
                    None,
                )
                quantidade += log[QUANTIDADE_INDEX] if log else 0
            if quantidade == 0:
                continue
            valor_medicao = next(
                (
                    valor_medicao_
                    for valor_medicao_ in valores_medicao_
                    if (
                        valor_medicao_[NOME_CAMPO_INDEX] == nome_campo
                        and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                        and valor_medicao_[DIA_ID] == f"{dia:02d}"
                        and valor_medicao_[INFANTIL_OU_FUNDAMENTAL_VALOR_INDEX]
                        == tipo_aluno
                    )
                ),
                None,
            )
            periodo_com_erro = checa_valor_medicao(valor_medicao, periodo_com_erro)
    return periodo_com_erro


def validate_lancamento_alimentacoes_medicao_emef_emebs_dietas(
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    classificacoes,
    periodo_com_erro,
    valores_medicao_,
    escola,
    inclusoes=None,
    eh_emebs=False,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    QUANTIDADE_INDEX = 2
    CLASSIFICACAO_ID_INDEX = 3

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 2

    nomes_campos = get_nomes_campos_emef_emebs_dietas(
        inclusoes, escola, categoria, medicao
    )
    if eh_emebs:
        periodo_com_erro = validate_lancamento_alimentacoes_inclusoes_emebs_dietas(
            nomes_campos,
            lista_erros,
            medicao,
            logs_,
            ano,
            mes,
            dia,
            categoria,
            classificacoes,
            valores_medicao_,
            escola,
            periodo_com_erro,
        )
    else:
        for nome_campo in nomes_campos:
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            quantidade = 0
            for classificacao in classificacoes:
                log = next(
                    (
                        log_
                        for log_ in logs_
                        if (
                            log_[DATA_INDEX]
                            == datetime.date(int(ano), int(mes), int(dia))
                            and (
                                log_[PERIODO_ESCOLAR_ID_INDEX]
                                == medicao.periodo_escolar.id
                                if medicao.periodo_escolar
                                else None
                            )
                            and log_[CLASSIFICACAO_ID_INDEX] == classificacao.id
                        )
                    ),
                    None,
                )
                quantidade += log[QUANTIDADE_INDEX] if log else 0
            if quantidade == 0:
                continue
            valor_medicao = next(
                (
                    valor_medicao_
                    for valor_medicao_ in valores_medicao_
                    if (
                        valor_medicao_[NOME_CAMPO_INDEX] == nome_campo
                        and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                        and valor_medicao_[DIA_ID] == f"{dia:02d}"
                    )
                ),
                None,
            )
            periodo_com_erro = checa_valor_medicao(valor_medicao, periodo_com_erro)
    return periodo_com_erro


def get_periodo_escolar_id(medicao):
    periodo_escolar_id = None
    if "Infantil" in medicao.grupo.nome:
        nome_periodo_escolar = medicao.grupo.nome.split(" ")[1]
        periodo_escolar_id = PeriodoEscolar.objects.get(nome=nome_periodo_escolar).id
    return periodo_escolar_id


def validate_lancamento_alimentacoes_medicao_emei_cemei_dietas(
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    classificacoes,
    periodo_com_erro,
    valores_medicao_,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    QUANTIDADE_INDEX = 2
    CLASSIFICACAO_ID_INDEX = 3
    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 2
    nomes_campos = build_nomes_campos_dietas_emei_cemei(medicao, categoria)

    for nome_campo in nomes_campos:
        if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
            continue
        quantidade = 0
        for classificacao in classificacoes:
            log = next(
                (
                    log_
                    for log_ in logs_
                    if (
                        log_[DATA_INDEX] == datetime.date(int(ano), int(mes), int(dia))
                        and log_[PERIODO_ESCOLAR_ID_INDEX]
                        == get_periodo_escolar_id(medicao)
                        and log_[CLASSIFICACAO_ID_INDEX] == classificacao.id
                    )
                ),
                None,
            )
            quantidade += log[QUANTIDADE_INDEX] if log else 0
        if quantidade == 0:
            continue
        valor_medicao = next(
            (
                valor_medicao_
                for valor_medicao_ in valores_medicao_
                if (
                    valor_medicao_[NOME_CAMPO_INDEX] == nome_campo
                    and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                    and valor_medicao_[DIA_ID] == f"{dia:02d}"
                )
            ),
            None,
        )
        if not valor_medicao:
            periodo_com_erro = True
    return periodo_com_erro


def validate_lancamento_alimentacoes_medicao_cei_dietas_faixas_etarias(
    faixas_etarias,
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    classificacoes,
    periodo_com_erro,
    valores_medicao_,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    FAIXA_ETARIA_ID_INDEX = 2
    QUANTIDADE_INDEX = 3
    CLASSIFICACAO_ID_INDEX = 4

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 3

    for faixa_etaria in faixas_etarias:
        if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
            continue
        quantidade = 0
        for classificacao in classificacoes:
            log = next(
                (
                    log_
                    for log_ in logs_
                    if (
                        log_[DATA_INDEX] == datetime.date(int(ano), int(mes), int(dia))
                        and log_[PERIODO_ESCOLAR_ID_INDEX] == medicao.periodo_escolar.id
                        and log_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                        and log_[CLASSIFICACAO_ID_INDEX] == classificacao.id
                    )
                ),
                None,
            )
            quantidade += log[QUANTIDADE_INDEX] if log else 0
        if quantidade == 0:
            continue
        valor_medicao = next(
            (
                valor_medicao_
                for valor_medicao_ in valores_medicao_
                if (
                    valor_medicao_[NOME_CAMPO_INDEX] == "frequencia"
                    and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                    and valor_medicao_[FAIXA_ETARIA_ID_INDEX] == faixa_etaria.id
                    and valor_medicao_[DIA_ID] == f"{dia:02d}"
                )
            ),
            None,
        )
        if not valor_medicao:
            periodo_com_erro = True
    return periodo_com_erro


def valida_medicoes_inexistentes_cei(solicitacao, lista_erros):
    for periodo_escolar in solicitacao.escola.periodos_escolares(ano=solicitacao.ano):
        if not solicitacao.medicoes.filter(periodo_escolar=periodo_escolar).exists():
            lista_erros.append(
                {
                    "periodo_escolar": periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas alimentações.",
                }
            )
    if (
        solicitacao.ue_possui_alunos_periodo_parcial
        and not solicitacao.medicoes.filter(periodo_escolar__nome="PARCIAL").exists()
    ):
        lista_erros.append(
            {
                "periodo_escolar": "PARCIAL",
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def validate_lancamento_alimentacoes_medicao_cei(solicitacao, lista_erros):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
    logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    dias_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=True
        ).values_list("data__day", flat=True)
    )

    logs_ = list(
        set(
            logs.values_list(
                "data", "periodo_escolar_id", "faixa_etaria_id", "quantidade"
            ).distinct()
        )
    )

    for dia in dias_letivos:
        for medicao in solicitacao.medicoes.all():
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "faixa_etaria_id",
                        "dia",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
                continue
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_cei_faixas_etarias(
                    faixas_etarias,
                    lista_erros,
                    medicao,
                    logs_,
                    ano,
                    mes,
                    dia,
                    categoria,
                    periodo_com_erro,
                    valores_medicao_,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.periodo_escolar.nome,
                        "erro": "Restam dias a serem lançados nas alimentações.",
                    }
                )
    return lista_erros


def validate_lancamento_alimentacoes_medicao_cei_cemei(
    lista_erros, dias_letivos, medicao, faixas_etarias, logs, ano, mes, categoria
):
    for dia in dias_letivos:
        valores_medicao_ = list(
            set(
                medicao.valores_medicao.values_list(
                    "nome_campo",
                    "categoria_medicao_id",
                    "faixa_etaria_id",
                    "dia",
                )
            )
        )
        periodo_com_erro = False
        if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
            continue
        periodo_com_erro = validate_lancamento_alimentacoes_medicao_cei_faixas_etarias(
            faixas_etarias,
            lista_erros,
            medicao,
            logs,
            ano,
            mes,
            dia,
            categoria,
            periodo_com_erro,
            valores_medicao_,
        )
        if periodo_com_erro:
            lista_erros.append(
                {
                    "periodo_escolar": medicao.periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas alimentações.",
                }
            )
    return lista_erros


def buscar_valores_lancamento_inclusoes_emebs(
    inclusao, solicitacao, categoria_medicao, lista_erros, periodo_com_erro
):
    tipos_alunos = (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=solicitacao.escola,
            criado_em__year=solicitacao.ano,
            criado_em__month=solicitacao.mes,
            periodo_escolar__nome=inclusao["periodo_escolar"],
        )
        .exclude(Q(quantidade_alunos=0) | Q(infantil_ou_fundamental="N/A"))
        .values_list("infantil_ou_fundamental", flat=True)
    )
    tipos_alunos = list(set(tipos_alunos))
    for tipo_aluno in tipos_alunos:
        for nome_campo in inclusao["linhas_da_tabela"]:
            valores_da_medicao = ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo=nome_campo,
                medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
                dia=inclusao["dia"],
                categoria_medicao=categoria_medicao,
                infantil_ou_fundamental=tipo_aluno,
            ).exclude(valor=None)
            if not valores_da_medicao:
                valor_observacao = ValorMedicao.objects.filter(
                    medicao__solicitacao_medicao_inicial=solicitacao,
                    nome_campo="observacao",
                    medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
                    dia=inclusao["dia"],
                    categoria_medicao=categoria_medicao,
                    infantil_ou_fundamental=tipo_aluno,
                ).exclude(valor=None)
                if not valor_observacao:
                    periodo_com_erro = True
    return periodo_com_erro


def buscar_valores_lancamento_inclusoes(
    inclusao, solicitacao, categoria_medicao, lista_erros, eh_emebs=False
):
    periodo_com_erro = False
    if eh_emebs:
        periodo_com_erro = buscar_valores_lancamento_inclusoes_emebs(
            inclusao, solicitacao, categoria_medicao, lista_erros, periodo_com_erro
        )
    else:
        for nome_campo in inclusao["linhas_da_tabela"]:
            valores_da_medicao = ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo=nome_campo,
                medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
                dia=inclusao["dia"],
                categoria_medicao=categoria_medicao,
            ).exclude(valor=None)
            if not valores_da_medicao:
                valor_observacao = ValorMedicao.objects.filter(
                    medicao__solicitacao_medicao_inicial=solicitacao,
                    nome_campo="observacao",
                    medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
                    dia=inclusao["dia"],
                    categoria_medicao=categoria_medicao,
                ).exclude(valor=None)
                if not valor_observacao:
                    periodo_com_erro = True
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": inclusao["periodo_escolar"],
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def buscar_valores_lancamento_inclusoes_emei_cemei(
    inclusao, categoria_medicao, lista_erros
):
    periodo_com_erro = False
    for nome_campo in inclusao["linhas_da_tabela"]:
        valores_da_medicao = ValorMedicao.objects.filter(
            medicao=inclusao["medicao"],
            nome_campo=nome_campo,
            dia=inclusao["dia"],
            categoria_medicao=categoria_medicao,
        ).exclude(valor=None)
        if not valores_da_medicao.exists():
            valor_observacao = ValorMedicao.objects.filter(
                medicao=inclusao["medicao"],
                nome_campo="observacao",
                dia=inclusao["dia"],
                categoria_medicao=categoria_medicao,
            ).exclude(valor=None)
            if not valor_observacao.exists():
                periodo_com_erro = True
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": inclusao["medicao"].nome_periodo_grupo,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def buscar_valores_lancamento_dietas_inclusoes(
    inclusao, solicitacao, categoria_medicao, lista_erros, nomes_campos
):
    periodo_com_erro = False
    valor_dietas_autorizadas = ValorMedicao.objects.filter(
        medicao__solicitacao_medicao_inicial=solicitacao,
        nome_campo="dietas_autorizadas",
        medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
        dia=inclusao["dia"],
        categoria_medicao=categoria_medicao,
    ).exclude(valor=0)
    for nome_campo in nomes_campos:
        valores_da_medicao = ValorMedicao.objects.filter(
            medicao__solicitacao_medicao_inicial=solicitacao,
            nome_campo=nome_campo,
            medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
            dia=inclusao["dia"],
            categoria_medicao=categoria_medicao,
        ).exclude(valor=None)
        if not valores_da_medicao and valor_dietas_autorizadas:
            valor_observacao = ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo="observacao",
                medicao__periodo_escolar__nome=inclusao["periodo_escolar"],
                dia=inclusao["dia"],
                categoria_medicao=categoria_medicao,
            ).exclude(valor=None)
            if not valor_observacao:
                periodo_com_erro = True
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": inclusao["periodo_escolar"],
                "erro": "Restam dias a serem lançados nas dietas.",
            }
        )
    return lista_erros


def get_alimentacoes_permitidas(solicitacao, escola, periodo_escolar):
    permissoes_especiais = get_permissoes_especiais_da_solicitacao(
        solicitacao, escola, periodo_escolar
    )
    alimentacoes_permitidas = list(
        set(
            [
                nome
                for nome, ativo in permissoes_especiais.values_list(
                    "alimentacoes_lancamento_especial__nome",
                    "alimentacoes_lancamento_especial__ativo",
                )
                if ativo
            ]
        )
    )
    return alimentacoes_permitidas


def get_permissoes_especiais_da_solicitacao(solicitacao, escola, periodo_escolar):
    permissoes_especiais = PermissaoLancamentoEspecial.objects.filter(
        Q(
            data_inicial__month__lte=int(solicitacao.mes),
            data_inicial__year=int(solicitacao.ano),
            data_final=None,
        )
        | Q(
            data_inicial__month__lte=int(solicitacao.mes),
            data_inicial__year=int(solicitacao.ano),
            data_final__year__gte=int(solicitacao.ano),
        ),
        escola=escola,
        periodo_escolar=periodo_escolar,
    )

    return permissoes_especiais


def get_alimentacoes_permitidas_emei_cemei(permissoes_especiais):
    alimentacoes_permitidas = list(
        set(
            [
                nome
                for nome, ativo in permissoes_especiais.values_list(
                    "alimentacoes_lancamento_especial__nome",
                    "alimentacoes_lancamento_especial__ativo",
                )
                if ativo
            ]
        )
    )

    return alimentacoes_permitidas


def validate_lancamento_inclusoes(solicitacao, lista_erros, eh_emebs=False):
    escola = solicitacao.escola
    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    list_inclusoes = []
    inclusoes_uuids = list(
        set(
            GrupoInclusaoAlimentacaoNormal.objects.filter(
                escola=escola,
                status=GrupoInclusaoAlimentacaoNormal.workflow_class.CODAE_AUTORIZADO,
            ).values_list("inclusoes_normais__uuid", flat=True)
        )
    )
    inclusoes = InclusaoAlimentacaoNormal.objects.filter(
        uuid__in=inclusoes_uuids,
        data__month=int(solicitacao.mes),
        data__year=int(solicitacao.ano),
        cancelado=False,
    ).order_by("data")
    for inclusao in inclusoes:
        grupo = inclusao.grupo_inclusao
        for periodo in grupo.quantidades_periodo.all():
            alimentacoes_permitidas = get_alimentacoes_permitidas(
                solicitacao, escola, periodo.periodo_escolar
            )
            tipos_alimentacao = periodo.tipos_alimentacao.exclude(
                nome="Lanche Emergencial"
            )
            tipos_alimentacao = list(
                set(tipos_alimentacao.values_list("nome", flat=True))
            )
            alimentacoes = tipos_alimentacao + alimentacoes_permitidas
            eh_numero_alunos = periodo.periodo_escolar not in escola.periodos_escolares(
                ano=solicitacao.ano
            )
            linhas_da_tabela = get_linhas_da_tabela(alimentacoes, eh_numero_alunos)
            dia_da_inclusao = str(inclusao.data.day)
            if len(dia_da_inclusao) == 1:
                dia_da_inclusao = "0" + str(inclusao.data.day)
            list_inclusoes.append(
                {
                    "periodo_escolar": periodo.periodo_escolar.nome,
                    "dia": dia_da_inclusao,
                    "linhas_da_tabela": linhas_da_tabela,
                }
            )
    for inclusao in list_inclusoes:
        lista_erros = buscar_valores_lancamento_inclusoes(
            inclusao, solicitacao, categoria_medicao, lista_erros, eh_emebs
        )
    return erros_unicos(lista_erros)


def validate_lancamento_inclusoes_emei_cemei(
    solicitacao, lista_erros, inclusoes, escola, categoria, medicao
):
    list_inclusoes = []

    for inclusao in inclusoes:
        for qt in inclusao.quantidade_alunos_emei_da_inclusao_cemei.all():
            periodo = qt.periodo_escolar
            if periodo.nome.upper() in medicao.nome_periodo_grupo.upper():
                alimentacoes_permitidas = get_alimentacoes_permitidas(
                    solicitacao, escola, periodo
                )
                vinculo = VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
                    tipo_unidade_escolar__iniciais="EMEI", periodo_escolar=periodo
                )
                alimentacoes_vinculadas = vinculo.tipos_alimentacao.exclude(
                    nome="Lanche Emergencial"
                )
                alimentacoes_vinculadas = list(
                    set(alimentacoes_vinculadas.values_list("nome", flat=True))
                )
                alimentacoes = alimentacoes_vinculadas + alimentacoes_permitidas
                eh_numero_alunos = periodo not in escola.periodos_escolares(
                    ano=solicitacao.ano
                )
                linhas_da_tabela = get_linhas_da_tabela(alimentacoes, eh_numero_alunos)

                dia_da_inclusao = str(
                    inclusao.dias_motivos_da_inclusao_cemei.first().data.day
                ).rjust(2, "0")
                list_inclusoes.append(
                    {
                        "medicao": medicao,
                        "dia": dia_da_inclusao,
                        "linhas_da_tabela": linhas_da_tabela,
                    }
                )
    for inclusao in list_inclusoes:
        lista_erros = buscar_valores_lancamento_inclusoes_emei_cemei(
            inclusao, categoria, lista_erros
        )
    return erros_unicos(lista_erros)


def validate_lancamento_inclusoes_cei_cemei(
    lista_erros,
    ano,
    mes,
    inclusoes,
    faixas_etarias,
    categoria,
    dias_nao_letivos,
    logs,
    medicao,
):
    if not inclusoes.exists():
        return lista_erros

    lista_erros = get_lista_erros_inclusoes_cei_cemei(
        dias_nao_letivos,
        lista_erros,
        inclusoes,
        mes,
        ano,
        faixas_etarias,
        categoria,
        logs,
        medicao,
    )

    return lista_erros


def get_inclusoes_filtradas_cei(inclusoes, dia, mes, ano, medicao):
    inclusoes_ = inclusoes.filter(
        dias_motivos_da_inclusao_cei__data=datetime.date(int(ano), int(mes), int(dia)),
        dias_motivos_da_inclusao_cei__cancelado=False,
    )
    if medicao.periodo_escolar.nome == "PARCIAL":
        inclusoes_ = inclusoes_.filter(
            quantidade_alunos_da_inclusao__periodo_externo__nome="INTEGRAL"
        ).exclude(quantidade_alunos_da_inclusao__periodo__nome="INTEGRAL")
    else:
        inclusoes_ = inclusoes_.filter(
            quantidade_alunos_da_inclusao__periodo=medicao.periodo_escolar,
            quantidade_alunos_da_inclusao__periodo_externo=medicao.periodo_escolar,
        )
    return inclusoes_


def get_inclusoes_filtradas_emei_cemei(inclusoes, dia, mes, ano, medicao):
    inclusoes_ = inclusoes.filter(
        dias_motivos_da_inclusao_cemei__data=datetime.date(
            int(ano), int(mes), int(dia)
        ),
        dias_motivos_da_inclusao_cemei__cancelado=False,
    )

    nome_periodo = medicao.nome_periodo_grupo.upper().split()

    return inclusoes_.filter(
        Q(
            quantidade_alunos_emei_da_inclusao_cemei__periodo_escolar__nome__in=nome_periodo
        )
        | Q(
            quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar__nome__in=nome_periodo
        )
    )


def get_inclusoes_filtradas_cei_cemei(inclusoes, dia, mes, ano, medicao):
    inclusoes_ = inclusoes.filter(
        dias_motivos_da_inclusao_cemei__data=datetime.date(
            int(ano), int(mes), int(dia)
        ),
        dias_motivos_da_inclusao_cemei__cancelado=False,
    )
    if medicao.periodo_escolar.nome == "PARCIAL":
        inclusoes_ = inclusoes_.exclude(
            Q(quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar__nome="INTEGRAL")
        )
    else:
        inclusoes_ = inclusoes_.filter(
            Q(
                quantidade_alunos_cei_da_inclusao_cemei__periodo_escolar=medicao.periodo_escolar
            )
        )
    return inclusoes_.distinct()


def get_inclusoes_filtradas_emef_emebs(inclusoes, dia, mes, ano, medicao):
    inclusoes_ = inclusoes.filter(
        inclusoes_normais__data=datetime.date(int(ano), int(mes), int(dia)),
        inclusoes_normais__cancelado=False,
        quantidades_por_periodo__periodo_escolar=medicao.periodo_escolar,
    )
    return inclusoes_


def get_lista_erros_inclusoes_cei(
    dias_nao_letivos,
    solicitacao,
    lista_erros,
    inclusoes,
    mes,
    ano,
    categoria,
    logs,
):
    logs_ = list(
        set(
            logs.values_list(
                "data", "periodo_escolar_id", "faixa_etaria_id", "quantidade"
            ).distinct()
        )
    )
    for dia in dias_nao_letivos:
        for medicao in solicitacao.medicoes.all():
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "faixa_etaria_id",
                        "dia",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
                continue
            inclusoes_ = get_inclusoes_filtradas_cei(inclusoes, dia, mes, ano, medicao)
            if not inclusoes_.exists():
                continue
            faixas_etarias = FaixaEtaria.objects.filter(
                id__in=inclusoes_.values_list(
                    "quantidade_alunos_da_inclusao__faixa_etaria__id", flat=True
                )
            )
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_cei_faixas_etarias(
                    faixas_etarias,
                    lista_erros,
                    medicao,
                    logs_,
                    ano,
                    mes,
                    dia,
                    categoria,
                    periodo_com_erro,
                    valores_medicao_,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.periodo_escolar.nome,
                        "erro": "Restam dias a serem lançados nas alimentações.",
                    }
                )
    return lista_erros


def get_lista_erros_inclusoes_cei_cemei(
    dias_nao_letivos,
    lista_erros,
    inclusoes,
    mes,
    ano,
    faixas_etarias,
    categoria,
    logs,
    medicao,
):
    logs_ = list(
        set(
            logs.values_list(
                "data", "periodo_escolar_id", "faixa_etaria_id", "quantidade"
            ).distinct()
        )
    )
    for dia in dias_nao_letivos:
        valores_medicao_ = list(
            set(
                medicao.valores_medicao.values_list(
                    "nome_campo",
                    "categoria_medicao_id",
                    "faixa_etaria_id",
                    "dia",
                )
            )
        )
        periodo_com_erro = False
        if lista_erros_com_periodo(lista_erros, medicao, "alimentações"):
            continue
        inclusoes_ = get_inclusoes_filtradas_cei_cemei(
            inclusoes, dia, mes, ano, medicao
        )
        if not inclusoes_.exists():
            continue
        periodo_com_erro = (
            validate_lancamento_alimentacoes_medicao_cei_cemei_faixas_etarias(
                faixas_etarias,
                lista_erros,
                medicao,
                logs_,
                ano,
                mes,
                dia,
                categoria,
                periodo_com_erro,
                valores_medicao_,
                inclusoes_,
            )
        )
        if periodo_com_erro:
            lista_erros.append(
                {
                    "periodo_escolar": medicao.periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas alimentações.",
                }
            )
    return lista_erros


def get_lista_erros_inclusoes_dietas_emef_emebs(
    dias_nao_letivos,
    solicitacao,
    lista_erros,
    inclusoes,
    mes,
    ano,
    categoria,
    logs,
    eh_emebs=False,
):
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "quantidade",
                "classificacao_id",
                "infantil_ou_fundamental",
            ).distinct()
        )
    )
    classificacoes = get_classificacoes_dietas(categoria)
    for dia in dias_nao_letivos:
        for medicao in solicitacao.medicoes.filter(periodo_escolar__isnull=False):
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "dia",
                        "infantil_ou_fundamental",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            inclusoes_ = get_inclusoes_filtradas_emef_emebs(
                inclusoes, dia, mes, ano, medicao
            )
            if not inclusoes_.exists():
                continue
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_emef_emebs_dietas(
                    lista_erros,
                    medicao,
                    logs_,
                    ano,
                    mes,
                    dia,
                    categoria,
                    classificacoes,
                    periodo_com_erro,
                    valores_medicao_,
                    solicitacao.escola,
                    inclusoes_,
                    eh_emebs,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.periodo_escolar.nome,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
    return lista_erros


def get_lista_erros_inclusoes_dietas_emei_cemei(
    dias_nao_letivos,
    lista_erros,
    inclusoes,
    mes,
    ano,
    categoria,
    logs,
    medicao,
):
    classificacoes = get_classificacoes_dietas(categoria)
    for dia in dias_nao_letivos:
        valores_medicao_ = list(
            set(
                medicao.valores_medicao.values_list(
                    "nome_campo",
                    "categoria_medicao_id",
                    "dia",
                )
            )
        )
        periodo_com_erro = False
        if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
            continue
        inclusoes_ = get_inclusoes_filtradas_emei_cemei(
            inclusoes, dia, mes, ano, medicao
        )
        if not inclusoes_.exists():
            continue
        periodo_com_erro = validate_lancamento_alimentacoes_medicao_emei_cemei_dietas(
            lista_erros,
            medicao,
            logs,
            ano,
            mes,
            dia,
            categoria,
            classificacoes,
            periodo_com_erro,
            valores_medicao_,
        )
        if periodo_com_erro:
            lista_erros.append(
                {
                    "periodo_escolar": medicao.nome_periodo_grupo,
                    "erro": "Restam dias a serem lançados nas dietas.",
                }
            )
    return lista_erros


def get_lista_erros_inclusoes_dietas_cei(
    dias_nao_letivos,
    solicitacao,
    lista_erros,
    inclusoes,
    mes,
    ano,
    faixas_etarias,
    categoria,
    classificacao,
    logs,
):
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "faixa_etaria_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )
    for dia in dias_nao_letivos:
        for medicao in solicitacao.medicoes.all():
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "faixa_etaria_id",
                        "dia",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            inclusoes_ = get_inclusoes_filtradas_cei(inclusoes, dia, mes, ano, medicao)
            if not inclusoes_.exists():
                continue
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_cei_dietas_faixas_etarias(
                    faixas_etarias,
                    lista_erros,
                    medicao,
                    logs_,
                    ano,
                    mes,
                    dia,
                    categoria,
                    classificacao,
                    periodo_com_erro,
                    valores_medicao_,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.periodo_escolar.nome,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
    return lista_erros


def get_lista_erros_inclusoes_dietas_cei_cemei(
    dias_nao_letivos,
    lista_erros,
    inclusoes,
    mes,
    ano,
    faixas_etarias,
    categoria,
    classificacao,
    logs,
    medicao,
):
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "faixa_etaria_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )
    for dia in dias_nao_letivos:
        valores_medicao_ = list(
            set(
                medicao.valores_medicao.values_list(
                    "nome_campo",
                    "categoria_medicao_id",
                    "faixa_etaria_id",
                    "dia",
                )
            )
        )
        periodo_com_erro = False
        if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
            continue
        inclusoes_ = get_inclusoes_filtradas_cei_cemei(
            inclusoes, dia, mes, ano, medicao
        )
        if not inclusoes_.exists():
            continue
        periodo_com_erro = (
            validate_lancamento_alimentacoes_medicao_cei_dietas_faixas_etarias(
                faixas_etarias,
                lista_erros,
                medicao,
                logs_,
                ano,
                mes,
                dia,
                categoria,
                classificacao,
                periodo_com_erro,
                valores_medicao_,
            )
        )
        if periodo_com_erro:
            lista_erros.append(
                {
                    "periodo_escolar": medicao.periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas dietas.",
                }
            )
    return lista_erros


def validate_lancamento_inclusoes_cei(solicitacao, lista_erros):
    escola = solicitacao.escola
    mes = solicitacao.mes
    ano = solicitacao.ano

    inclusoes = (
        escola.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_escola.filter(
            dias_motivos_da_inclusao_cei__data__month=mes,
            dias_motivos_da_inclusao_cei__data__year=ano,
            dias_motivos_da_inclusao_cei__cancelado=False,
            status="CODAE_AUTORIZADO",
        )
    )
    if not inclusoes.exists():
        return lista_erros

    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    logs = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    dias_nao_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=False
        ).values_list("data__day", flat=True)
    )

    lista_erros = get_lista_erros_inclusoes_cei(
        dias_nao_letivos,
        solicitacao,
        lista_erros,
        inclusoes,
        mes,
        ano,
        categoria,
        logs,
    )

    return lista_erros


def validate_lancamento_inclusoes_dietas_emef_emebs(
    solicitacao, lista_erros, eh_emebs=False
):
    escola = solicitacao.escola
    mes = solicitacao.mes
    ano = solicitacao.ano

    inclusoes = escola.grupos_inclusoes_normais.filter(
        inclusoes_normais__data__month=mes,
        inclusoes_normais__data__year=ano,
        inclusoes_normais__cancelado=False,
        status="CODAE_AUTORIZADO",
    )
    if not inclusoes.exists():
        return lista_erros

    logs = escola.logs_dietas_autorizadas.filter(data__month=mes, data__year=ano)
    dias_nao_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=False
        ).values_list("data__day", flat=True)
    )
    categorias = CategoriaMedicao.objects.exclude(nome__icontains="ALIMENTAÇÃO")
    for categoria in categorias:
        lista_erros = get_lista_erros_inclusoes_dietas_emef_emebs(
            dias_nao_letivos,
            solicitacao,
            lista_erros,
            inclusoes,
            mes,
            ano,
            categoria,
            logs,
            eh_emebs,
        )
    return lista_erros


def validate_lancamento_inclusoes_dietas_emei_cemei(
    lista_erros,
    inclusoes,
    categorias,
    dias_nao_letivos,
    mes,
    ano,
    logs,
    medicao,
):
    if not inclusoes.exists():
        return lista_erros

    for categoria in categorias:
        lista_erros = get_lista_erros_inclusoes_dietas_emei_cemei(
            dias_nao_letivos,
            lista_erros,
            inclusoes,
            mes,
            ano,
            categoria,
            logs,
            medicao,
        )
    return lista_erros


def validate_lancamento_inclusoes_dietas_cei(solicitacao, lista_erros):
    escola = solicitacao.escola
    mes = solicitacao.mes
    ano = solicitacao.ano

    inclusoes = (
        escola.inclusao_alimentacao_inclusaoalimentacaodacei_rastro_escola.filter(
            dias_motivos_da_inclusao_cei__data__month=mes,
            dias_motivos_da_inclusao_cei__data__year=ano,
            dias_motivos_da_inclusao_cei__cancelado=False,
            status="CODAE_AUTORIZADO",
        )
    )
    if not inclusoes.exists():
        return lista_erros

    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
    logs = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    dias_nao_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=False
        ).values_list("data__day", flat=True)
    )
    categorias = CategoriaMedicao.objects.exclude(
        nome__icontains="ALIMENTAÇÃO"
    ).exclude(nome__icontains="ENTERAL")
    for categoria in categorias:
        classificacao = get_classificacoes_dietas_cei(categoria)
        lista_erros = get_lista_erros_inclusoes_dietas_cei(
            dias_nao_letivos,
            solicitacao,
            lista_erros,
            inclusoes,
            mes,
            ano,
            faixas_etarias,
            categoria,
            classificacao,
            logs,
        )
    return lista_erros


def validate_lancamento_inclusoes_dietas_cei_cemei(
    lista_erros,
    mes,
    ano,
    inclusoes,
    categorias,
    dias_nao_letivos,
    faixas_etarias,
    logs,
    medicao,
):
    if not inclusoes.exists():
        return lista_erros

    for categoria in categorias:
        classificacao = get_classificacoes_dietas_cei(categoria)
        lista_erros = get_lista_erros_inclusoes_dietas_cei_cemei(
            dias_nao_letivos,
            lista_erros,
            inclusoes,
            mes,
            ano,
            faixas_etarias,
            categoria,
            classificacao,
            logs,
            medicao,
        )
    return lista_erros


def get_classificacoes_dietas_cei(categoria):
    classificacoes = ClassificacaoDieta.objects.filter(
        nome__icontains=categoria.nome.split(" - ")[1]
    )
    return classificacoes


def get_classificacoes_dietas(categoria):
    if "AMINOÁCIDOS" in categoria.nome:
        classificacoes = ClassificacaoDieta.objects.filter(
            nome__icontains="Tipo A"
        ).exclude(nome="Tipo A")
    else:
        classificacoes = (
            ClassificacaoDieta.objects.filter(
                nome__icontains=categoria.nome.split(" - ")[1]
            )
            .exclude(nome__icontains="amino")
            .exclude(nome__icontains="enteral")
        )
    return classificacoes


def validate_lancamento_dietas_emef(solicitacao, lista_erros):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    categorias = CategoriaMedicao.objects.exclude(nome__icontains="ALIMENTAÇÃO")
    logs = escola.logs_dietas_autorizadas.filter(data__month=mes, data__year=ano)
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )
    dias_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=True
        ).values_list("data__day", flat=True)
    )
    for categoria in categorias:
        classificacoes = get_classificacoes_dietas(categoria)
        for dia in dias_letivos:
            for medicao in solicitacao.medicoes.all():
                valores_medicao_ = list(
                    set(
                        medicao.valores_medicao.values_list(
                            "nome_campo",
                            "categoria_medicao_id",
                            "dia",
                        )
                    )
                )
                periodo_com_erro = False
                if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                    continue
                periodo_com_erro = (
                    validate_lancamento_alimentacoes_medicao_emef_emebs_dietas(
                        lista_erros,
                        medicao,
                        logs_,
                        ano,
                        mes,
                        dia,
                        categoria,
                        classificacoes,
                        periodo_com_erro,
                        valores_medicao_,
                        escola,
                    )
                )
                if periodo_com_erro:
                    lista_erros.append(
                        {
                            "periodo_escolar": medicao.periodo_escolar.nome,
                            "erro": "Restam dias a serem lançados nas dietas.",
                        }
                    )
    return lista_erros


def validate_lancamento_dietas_emei_cemei(
    lista_erros, mes, ano, categorias, dias_letivos, logs, medicao
):
    for categoria in categorias:
        classificacoes = get_classificacoes_dietas(categoria)
        for dia in dias_letivos:
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "dia",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_emei_cemei_dietas(
                    lista_erros,
                    medicao,
                    logs,
                    ano,
                    mes,
                    dia,
                    categoria,
                    classificacoes,
                    periodo_com_erro,
                    valores_medicao_,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.nome_periodo_grupo,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
    return lista_erros


def validate_lancamento_dietas_cei(solicitacao, lista_erros):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    categorias = CategoriaMedicao.objects.exclude(
        nome__icontains="ALIMENTAÇÃO"
    ).exclude(nome__icontains="ENTERAL")
    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
    logs = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "faixa_etaria_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )
    dias_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=True
        ).values_list("data__day", flat=True)
    )
    for categoria in categorias:
        classificacoes = get_classificacoes_dietas_cei(categoria)
        for dia in dias_letivos:
            for medicao in solicitacao.medicoes.all():
                valores_medicao_ = list(
                    set(
                        medicao.valores_medicao.values_list(
                            "nome_campo",
                            "categoria_medicao_id",
                            "faixa_etaria_id",
                            "dia",
                        )
                    )
                )
                periodo_com_erro = False
                if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                    continue
                periodo_com_erro = (
                    validate_lancamento_alimentacoes_medicao_cei_dietas_faixas_etarias(
                        faixas_etarias,
                        lista_erros,
                        medicao,
                        logs_,
                        ano,
                        mes,
                        dia,
                        categoria,
                        classificacoes,
                        periodo_com_erro,
                        valores_medicao_,
                    )
                )
                if periodo_com_erro:
                    lista_erros.append(
                        {
                            "periodo_escolar": medicao.periodo_escolar.nome,
                            "erro": "Restam dias a serem lançados nas dietas.",
                        }
                    )
    return lista_erros


def validate_lancamento_dietas_cei_cemei(
    lista_erros, mes, ano, categorias, faixas_etarias, logs, dias_letivos, medicao
):
    for categoria in categorias:
        classificacoes = get_classificacoes_dietas_cei(categoria)
        for dia in dias_letivos:
            valores_medicao_ = list(
                set(
                    medicao.valores_medicao.values_list(
                        "nome_campo",
                        "categoria_medicao_id",
                        "faixa_etaria_id",
                        "dia",
                    )
                )
            )
            periodo_com_erro = False
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            periodo_com_erro = (
                validate_lancamento_alimentacoes_medicao_cei_dietas_faixas_etarias(
                    faixas_etarias,
                    lista_erros,
                    medicao,
                    logs,
                    ano,
                    mes,
                    dia,
                    categoria,
                    classificacoes,
                    periodo_com_erro,
                    valores_medicao_,
                )
            )
            if periodo_com_erro:
                lista_erros.append(
                    {
                        "periodo_escolar": medicao.periodo_escolar.nome,
                        "erro": "Restam dias a serem lançados nas dietas.",
                    }
                )
    return lista_erros


def remover_duplicados(query_set):
    aux = []
    sem_uuid_repetido = []
    for resultado in query_set:
        if resultado.uuid not in aux:
            aux.append(resultado.uuid)
            sem_uuid_repetido.append(resultado)
    return sem_uuid_repetido


def formatar_query_set_alteracao(query_set, mes, ano):
    datas = []
    for alteracao_alimentacao in query_set:
        alteracao = alteracao_alimentacao.get_raw_model.objects.get(
            uuid=alteracao_alimentacao.uuid
        )
        datas_intervalos = alteracao.datas_intervalo.filter(
            data__month=mes, data__year=ano, cancelado=False
        )
        for obj in datas_intervalos:
            if not len(str(obj.data.day)) == 1:
                datas.append(str(obj.data.day))
            else:
                datas.append(("0" + str(obj.data.day)))
    return list(set(datas))


def get_lista_dias_solicitacoes(params, escola):
    query_set = SolicitacoesEscola.get_autorizados(escola_uuid=escola.uuid)
    query_set = SolicitacoesEscola.busca_filtro(query_set, params)
    query_set = query_set.filter(
        data_evento__month=params["mes"], data_evento__year=params["ano"]
    )
    query_set = query_set.filter(data_evento__lt=datetime.date.today())
    """
    TODO: remover essa regra posteriormente quando definir calendário de Recreio Férias
    """
    if "tipo_solicitacao" in params and params["tipo_solicitacao"] == "Kit Lanche":
        query_set = query_set.exclude(
            data_evento__gte="2025-07-07", data_evento__lte="2025-07-18"
        )
    if params.get("eh_lanche_emergencial", False):
        query_set = query_set.filter(motivo__icontains="Emergencial")
        query_set = remover_duplicados(query_set)
        return formatar_query_set_alteracao(query_set, params["mes"], params["ano"])
    else:
        query_set = remover_duplicados(query_set)
        datas_kits = []
        for obj in query_set:
            if not len(str(obj.data_evento.day)) == 1:
                datas_kits.append(str(obj.data_evento.day))
            else:
                datas_kits.append(("0" + str(obj.data_evento.day)))
        return datas_kits


def validate_lancamento_kit_lanche(solicitacao, lista_erros):
    escola = solicitacao.escola
    mes = solicitacao.mes
    ano = solicitacao.ano
    tipo_solicitacao = "Kit Lanche"
    params = {
        "mes": mes,
        "ano": ano,
        "escola_uuid": escola.uuid,
        "tipo_solicitacao": tipo_solicitacao,
    }
    dias_kit_lanche = get_lista_dias_solicitacoes(params, escola)
    dias_kit_lanche = list(set(dias_kit_lanche))

    valores_da_medicao = (
        ValorMedicao.objects.filter(
            medicao__solicitacao_medicao_inicial=solicitacao,
            nome_campo="kit_lanche",
            medicao__grupo__nome="Solicitações de Alimentação",
            dia__in=dias_kit_lanche,
        )
        .order_by("dia")
        .exclude(valor=None)
        .values_list("dia", flat=True)
    )
    valores_da_medicao = list(set(valores_da_medicao))
    if len(valores_da_medicao) != len(dias_kit_lanche):
        lista_erros.append(
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Kit Lanches.",
            }
        )
    return erros_unicos(lista_erros)


def validate_lanche_emergencial(solicitacao, lista_erros):
    escola = solicitacao.escola
    mes = solicitacao.mes
    ano = solicitacao.ano
    tipo_solicitacao = "Alteração"
    eh_lanche_emergencial = True

    params = {
        "mes": mes,
        "ano": ano,
        "escola_uuid": escola.uuid,
        "tipo_solicitacao": tipo_solicitacao,
        "eh_lanche_emergencial": eh_lanche_emergencial,
    }
    dias_lanche_emergencial = get_lista_dias_solicitacoes(params, escola)
    dias_lanche_emergencial = list(set(dias_lanche_emergencial))

    valores_da_medicao = (
        ValorMedicao.objects.filter(
            medicao__solicitacao_medicao_inicial=solicitacao,
            nome_campo="lanche_emergencial",
            medicao__grupo__nome="Solicitações de Alimentação",
            dia__in=dias_lanche_emergencial,
        )
        .order_by("dia")
        .exclude(valor=None)
        .values_list("dia", flat=True)
    )
    valores_da_medicao = list(set(valores_da_medicao))
    if len(valores_da_medicao) != len(dias_lanche_emergencial):
        lista_erros.append(
            {
                "periodo_escolar": "Solicitações de Alimentação",
                "erro": "Restam dias a serem lançados nos Lanches Emergenciais.",
            }
        )
    return erros_unicos(lista_erros)


def get_inclusoes_programas_projetos(solicitacao):
    primeiro_dia_mes = datetime.date(int(solicitacao.ano), int(solicitacao.mes), 1)
    ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)
    inclusoes = (
        solicitacao.escola.inclusoes_alimentacao_continua.filter(
            status="CODAE_AUTORIZADO",
            data_inicial__lte=ultimo_dia_mes,
            data_final__gte=primeiro_dia_mes,
        )
        .exclude(motivo__nome="ETEC")
        .distinct()
    )
    return inclusoes


def get_inclusoes_etec(solicitacao):
    primeiro_dia_mes = datetime.date(int(solicitacao.ano), int(solicitacao.mes), 1)
    ultimo_dia_mes = get_ultimo_dia_mes(primeiro_dia_mes)
    inclusoes = solicitacao.escola.inclusoes_alimentacao_continua.filter(
        status="CODAE_AUTORIZADO",
        data_inicial__lte=ultimo_dia_mes,
        data_final__gte=primeiro_dia_mes,
        motivo__nome="ETEC",
    ).distinct()
    return inclusoes


def append_lanches_nomes_campos(nomes_campos, tipos_alimentacao):
    if "Lanche" in tipos_alimentacao:
        nomes_campos.append("lanche")
    if "Lanche 4h" in tipos_alimentacao:
        nomes_campos.append("lanche_4h")
    return nomes_campos


def get_tipos_alimentacao(inclusoes, dia_semana):
    nomes_campos = ["frequencia"]
    tipos_alimentacao = []
    for inclusao in inclusoes:
        for qp in inclusao.quantidades_periodo.filter(
            dias_semana__icontains=dia_semana
        ):
            tipos_alimentacao += qp.tipos_alimentacao.all().values_list(
                "nome", flat=True
            )
    tipos_alimentacao = list(set(tipos_alimentacao))
    nomes_campos = append_lanches_nomes_campos(nomes_campos, tipos_alimentacao)
    return tipos_alimentacao, nomes_campos


def build_nomes_campos_alimentacoes_programas_e_projetos(inclusoes, dia_semana):
    tipos_alimentacao, nomes_campos = get_tipos_alimentacao(inclusoes, dia_semana)
    if "Refeição" in tipos_alimentacao:
        nomes_campos.append("refeicao")
        nomes_campos.append("repeticao_refeicao")
    if "Sobremesa" in tipos_alimentacao:
        nomes_campos.append("sobremesa")
        nomes_campos.append("repeticao_sobremesa")
    return nomes_campos


def valida_campo_a_campo_alimentacao_continua(
    periodo_com_erro, nomes_campos, medicao_programas_projetos, categoria, dia, eh_emebs
):
    campos_infantil_ou_fundamental = [ValorMedicao.NA]
    if eh_emebs:
        campos_infantil_ou_fundamental = [ValorMedicao.FUNDAMENTAL]
        escola = medicao_programas_projetos.solicitacao_medicao_inicial.escola
        if escola.quantidade_alunos_emebs_infantil > 0:
            campos_infantil_ou_fundamental.append(ValorMedicao.INFANTIL)
    for nome_campo in nomes_campos:
        for campo_infantil_ou_fundamental in campos_infantil_ou_fundamental:
            if not medicao_programas_projetos.valores_medicao.filter(
                categoria_medicao=categoria,
                nome_campo=nome_campo,
                dia=f"{dia:02d}",
                infantil_ou_fundamental=campo_infantil_ou_fundamental,
            ).exists():
                periodo_com_erro = True
                continue
    return periodo_com_erro


def valida_alimentacoes_solicitacoes_continuas(
    ano,
    mes,
    inclusoes,
    escola,
    quantidade_dias_mes,
    medicao_programas_projetos,
    eh_ceu_gestao=False,
    eh_emebs=False,
):
    periodo_com_erro = False
    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    for dia in range(1, quantidade_dias_mes + 1):
        feriados = calendario.holidays(int(ano))
        if dia in [
            feriado[0].day for feriado in feriados if feriado[0].month == int(mes)
        ]:
            continue
        data = datetime.date(year=int(ano), month=int(mes), day=dia)
        dia_semana = data.weekday()
        if eh_ceu_gestao and medicao_programas_projetos.nome_periodo_grupo == "ETEC":
            inclusoes_filtradas = inclusoes.filter(
                data_inicial__lte=data,
                data_final__gte=data,
                quantidades_por_periodo__cancelado=False,
            )
        else:
            inclusoes_filtradas = inclusoes.filter(
                data_inicial__lte=data,
                data_final__gte=data,
                quantidades_por_periodo__cancelado=False,
                quantidades_por_periodo__dias_semana__icontains=dia_semana,
            )
        nomes_campos = build_nomes_campos_alimentacoes_programas_e_projetos(
            inclusoes_filtradas, dia_semana
        )
        if (
            periodo_com_erro
            or not inclusoes_filtradas.exists()
            or not escola.calendario.filter(data=data).exists()
            or not escola.calendario.get(data=data).dia_letivo
        ):
            continue
        periodo_com_erro = valida_campo_a_campo_alimentacao_continua(
            periodo_com_erro,
            nomes_campos,
            medicao_programas_projetos,
            categoria,
            dia,
            eh_emebs,
        )
    return periodo_com_erro


def get_inclusoes_continuas_filtradas_emei_cemei(
    eh_ceu_gestao, medicao_programas_projetos, inclusoes, data, dia_semana
):
    if eh_ceu_gestao and medicao_programas_projetos.nome_periodo_grupo == "ETEC":
        inclusoes_filtradas = inclusoes.filter(
            data_inicial__lte=data,
            data_final__gte=data,
            quantidades_por_periodo__cancelado=False,
        )
    else:
        inclusoes_filtradas = inclusoes.filter(
            data_inicial__lte=data,
            data_final__gte=data,
            quantidades_por_periodo__cancelado=False,
            quantidades_por_periodo__dias_semana__icontains=dia_semana,
        )
    return inclusoes_filtradas


def valida_alimentacoes_solicitacoes_continuas_emei_cemei(
    ano,
    mes,
    inclusoes,
    escola,
    quantidade_dias_mes,
    medicao_programas_projetos,
    eh_ceu_gestao=False,
):
    periodo_com_erro = False
    categoria = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")

    for dia in range(1, quantidade_dias_mes + 1):
        feriados = calendario.holidays(int(ano))
        if dia in [
            feriado[0].day for feriado in feriados if feriado[0].month == int(mes)
        ]:
            continue
        data = datetime.date(year=int(ano), month=int(mes), day=dia)
        dia_semana = data.weekday()
        inclusoes_filtradas = get_inclusoes_continuas_filtradas_emei_cemei(
            eh_ceu_gestao, medicao_programas_projetos, inclusoes, data, dia_semana
        )
        if (
            periodo_com_erro
            or not inclusoes_filtradas.exists()
            or (
                not escola.calendario.filter(data=data).first().dia_letivo
                and not inclusoes_filtradas.exists()
            )
        ):
            continue
        nomes_campos = build_nomes_campos_alimentacoes_programas_e_projetos(
            inclusoes, dia_semana
        )
        for nome_campo in nomes_campos:
            if not medicao_programas_projetos.valores_medicao.filter(
                categoria_medicao=categoria,
                nome_campo=nome_campo,
                dia=f"{dia:02d}",
            ).exists():
                periodo_com_erro = True
                continue
    return periodo_com_erro


def get_nomes_campos_categoria(nomes_campos, classificacao, categorias):
    if "ENTERAL" in classificacao.nome or "AMINOÁCIDOS" in classificacao.nome:
        categoria = categorias.get(nome__icontains="enteral")
        if "refeicao" not in nomes_campos:
            nomes_campos.append("refeicao")
    else:
        categoria = categorias.exclude(nome__icontains="enteral").get(
            nome__icontains=classificacao.nome
        )
        if "refeicao" in nomes_campos:
            nomes_campos.remove("refeicao")
    return nomes_campos, categoria


def inclusoes_tem_lanche_4h(inclusoes_filtradas, dia_semana):
    tipos_alimentacao = []
    for inclusao in inclusoes_filtradas:
        for qp in inclusao.quantidades_por_periodo.filter(
            dias_semana__icontains=dia_semana
        ):
            [
                tipos_alimentacao.append(tipo_alimentacao.nome)
                for tipo_alimentacao in qp.tipos_alimentacao.all()
            ]
    return "Lanche 4h" in tipos_alimentacao


def tratar_nomes_campos_periodo_com_erro(
    nomes_campos,
    medicao_programas_projetos,
    categoria,
    dia,
    eh_ceu_gestao,
    periodo_com_erro_dieta,
    inclusoes_filtradas,
    dia_semana,
    infantil_ou_fundamental=ValorMedicao.NA,
):
    tipos_alimentacao_inclusoes = list(
        set(
            inclusoes_filtradas.values_list(
                "quantidades_por_periodo__tipos_alimentacao__nome", flat=True
            )
        )
    )
    tipos_alimentacao_inclusoes_normalizados = [
        unicodedata.normalize("NFD", nome.replace(" ", "_").lower())
        .encode("ascii", "ignore")
        .decode("utf-8")
        for nome in tipos_alimentacao_inclusoes
    ]
    if not any(
        item in tipos_alimentacao_inclusoes_normalizados for item in nomes_campos
    ):
        return periodo_com_erro_dieta
    nomes_campos_ = ["frequencia"] + [
        item
        for item in tipos_alimentacao_inclusoes_normalizados
        if item in nomes_campos
    ]
    for nome_campo in nomes_campos_:
        if (
            not inclusoes_tem_lanche_4h(inclusoes_filtradas, dia_semana)
            and nome_campo == "lanche_4h"
        ):
            continue
        if not medicao_programas_projetos.valores_medicao.filter(
            categoria_medicao=categoria,
            nome_campo=nome_campo,
            dia=f"{dia:02d}",
            infantil_ou_fundamental=infantil_ou_fundamental,
        ).exists():
            if eh_ceu_gestao and not medicao_programas_projetos.valores_medicao.filter(
                categoria_medicao=categoria,
                nome_campo="dietas_autorizadas",
                dia=f"{dia:02d}",
                valor__gt=0,
                infantil_ou_fundamental=infantil_ou_fundamental,
            ):
                continue
            periodo_com_erro_dieta = True
            continue
    return periodo_com_erro_dieta


def incluir_lanche_e_ou_lanche_4h_sol_continuas(nomes_campos, escola, medicao):
    tipos_alimentacao = list(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.filter(
            tipo_unidade_escolar=escola.tipo_unidade,
            periodo_escolar__in=escola.periodos_escolares(
                medicao.solicitacao_medicao_inicial.ano
            ),
        )
        .values_list("tipos_alimentacao__nome", flat=True)
        .distinct()
    )
    if "Lanche 4h" in tipos_alimentacao and "lanche_4h" not in nomes_campos:
        nomes_campos.append("lanche_4h")
    if "Lanche" in tipos_alimentacao and "lanche_4h" not in nomes_campos:
        nomes_campos.append("lanche")

    return nomes_campos


def valida_dietas_solicitacoes_continuas(
    escola,
    mes,
    ano,
    quantidade_dias_mes,
    inclusoes,
    medicao_programas_projetos,
    eh_ceu_gestao=False,
    infantil_ou_fundamental=ValorMedicao.NA,
):
    periodo_com_erro_dieta = False

    categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")
    nomes_campos = ["frequencia"]
    ids_categorias_existentes_no_mes = list(
        set(
            escola.logs_dietas_autorizadas.filter(
                data__month=mes,
                data__year=ano,
                quantidade__gt=0,
                periodo_escolar__nome=None,
                infantil_ou_fundamental=infantil_ou_fundamental,
            )
            .exclude(classificacao__nome="Tipo C")
            .values_list("classificacao", flat=True)
            .distinct()
        )
    )
    classificacoes = ClassificacaoDieta.objects.filter(
        id__in=ids_categorias_existentes_no_mes
    )
    for classificacao in classificacoes:
        nomes_campos, categoria = get_nomes_campos_categoria(
            nomes_campos, classificacao, categorias
        )
        nomes_campos = incluir_lanche_e_ou_lanche_4h_sol_continuas(
            nomes_campos, escola, medicao_programas_projetos
        )
        for dia in range(1, quantidade_dias_mes + 1):
            feriados = calendario.holidays(int(ano))
            if dia in [
                feriado[0].day for feriado in feriados if feriado[0].month == int(mes)
            ]:
                continue
            data = datetime.date(year=int(ano), month=int(mes), day=dia)
            dia_semana = data.weekday()
            inclusoes_filtradas = inclusoes.filter(
                data_inicial__lte=data,
                data_final__gte=data,
                quantidades_por_periodo__cancelado=False,
                quantidades_por_periodo__dias_semana__icontains=dia_semana,
            )
            if (
                periodo_com_erro_dieta
                or not inclusoes_filtradas.exists()
                or (
                    not inclusoes_filtradas.exists()
                    and not escola.calendario.filter(data=data).first().dia_letivo
                )
            ):
                continue
            periodo_com_erro_dieta = tratar_nomes_campos_periodo_com_erro(
                nomes_campos,
                medicao_programas_projetos,
                categoria,
                dia,
                eh_ceu_gestao,
                periodo_com_erro_dieta,
                inclusoes_filtradas,
                dia_semana,
                infantil_ou_fundamental,
            )
    return periodo_com_erro_dieta


def valida_dietas_solicitacoes_continuas_emei_cemei(
    escola,
    mes,
    ano,
    quantidade_dias_mes,
    inclusoes,
    medicao_programas_projetos,
    eh_ceu_gestao=False,
):
    periodo_com_erro_dieta = False

    categorias = CategoriaMedicao.objects.filter(nome__icontains="dieta")
    nomes_campos = ["frequencia"]
    ids_categorias_existentes_no_mes = list(
        set(
            escola.logs_dietas_autorizadas.filter(
                data__month=mes, data__year=ano, quantidade__gt=0
            )
            .exclude(classificacao__nome="Tipo C")
            .values_list("classificacao", flat=True)
            .distinct()
        )
    )
    classificacoes = ClassificacaoDieta.objects.filter(
        id__in=ids_categorias_existentes_no_mes
    )
    for classificacao in classificacoes:
        nomes_campos, categoria = get_nomes_campos_categoria(
            nomes_campos, classificacao, categorias
        )
        for dia in range(1, quantidade_dias_mes + 1):
            feriados = calendario.holidays(int(ano))
            if dia in [
                feriado[0].day for feriado in feriados if feriado[0].month == int(mes)
            ]:
                continue
            data = datetime.date(year=int(ano), month=int(mes), day=dia)
            dia_semana = data.weekday()
            inclusoes_filtradas = inclusoes.filter(
                data_inicial__lte=data,
                data_final__gte=data,
                quantidades_por_periodo__cancelado=False,
                quantidades_por_periodo__dias_semana__icontains=dia_semana,
            )
            log_do_dia_maior_que_zero = LogQuantidadeDietasAutorizadas.objects.filter(
                escola=escola,
                data=datetime.datetime(int(ano), int(mes), dia).date(),
                classificacao=classificacao,
                periodo_escolar__isnull=True,
                quantidade__gt=0,
                cei_ou_emei="N/A",
            )
            if (
                periodo_com_erro_dieta
                or not inclusoes_filtradas.exists()
                or (
                    not escola.calendario.filter(data=data).first().dia_letivo
                    and not inclusoes_filtradas.exists()
                )
                or not log_do_dia_maior_que_zero.exists()
            ):
                continue
            periodo_com_erro_dieta = tratar_nomes_campos_periodo_com_erro(
                nomes_campos,
                medicao_programas_projetos,
                categoria,
                dia,
                eh_ceu_gestao,
                periodo_com_erro_dieta,
                inclusoes_filtradas,
                dia_semana,
            )
    return periodo_com_erro_dieta


def validate_solicitacoes_continuas(
    solicitacao,
    lista_erros,
    inclusoes,
    medicao,
    nome_secao,
    valida_dietas,
    eh_ceu_gestao=False,
    eh_emebs=False,
):
    periodo_com_erro_dieta = False
    quantidade_dias_mes = calendar.monthrange(
        int(solicitacao.ano), int(solicitacao.mes)
    )[1]

    periodo_com_erro = valida_alimentacoes_solicitacoes_continuas(
        solicitacao.ano,
        solicitacao.mes,
        inclusoes,
        solicitacao.escola,
        quantidade_dias_mes,
        medicao,
        eh_ceu_gestao,
        eh_emebs,
    )
    if valida_dietas:
        if not eh_emebs:
            periodo_com_erro_dieta = valida_dietas_solicitacoes_continuas(
                solicitacao.escola,
                solicitacao.mes,
                solicitacao.ano,
                quantidade_dias_mes,
                inclusoes,
                medicao,
                False,
                ValorMedicao.NA,
            )

        else:
            periodo_com_erro_dieta = valida_dietas_solicitacoes_continuas(
                solicitacao.escola,
                solicitacao.mes,
                solicitacao.ano,
                quantidade_dias_mes,
                inclusoes,
                medicao,
                False,
                ValorMedicao.INFANTIL,
            ) or valida_dietas_solicitacoes_continuas(
                solicitacao.escola,
                solicitacao.mes,
                solicitacao.ano,
                quantidade_dias_mes,
                inclusoes,
                medicao,
                False,
                ValorMedicao.FUNDAMENTAL,
            )

    if periodo_com_erro_dieta:
        lista_erros.append(
            {
                "periodo_escolar": nome_secao,
                "erro": "Restam dias a serem lançados nas dietas.",
            }
        )

    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": nome_secao,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return erros_unicos(lista_erros)


def validate_solicitacoes_continuas_emei_cemei(
    solicitacao,
    lista_erros,
    inclusoes,
    medicao,
    nome_secao,
    valida_dietas,
    eh_ceu_gestao=False,
):
    periodo_com_erro_dieta = False
    quantidade_dias_mes = calendar.monthrange(
        int(solicitacao.ano), int(solicitacao.mes)
    )[1]

    periodo_com_erro = valida_alimentacoes_solicitacoes_continuas_emei_cemei(
        solicitacao.ano,
        solicitacao.mes,
        inclusoes,
        solicitacao.escola,
        quantidade_dias_mes,
        medicao,
        eh_ceu_gestao,
    )
    if valida_dietas:
        periodo_com_erro_dieta = valida_dietas_solicitacoes_continuas_emei_cemei(
            solicitacao.escola,
            solicitacao.mes,
            solicitacao.ano,
            quantidade_dias_mes,
            inclusoes,
            medicao,
            eh_ceu_gestao,
        )

    if periodo_com_erro_dieta:
        lista_erros.append(
            {
                "periodo_escolar": nome_secao,
                "erro": "Restam dias a serem lançados nas dietas.",
            }
        )

    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": nome_secao,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return erros_unicos(lista_erros)


def validate_solicitacoes_programas_e_projetos(solicitacao, lista_erros):
    inclusoes = get_inclusoes_programas_projetos(solicitacao)

    if not inclusoes:
        return lista_erros

    medicao_programas_projetos = solicitacao.get_medicao_programas_e_projetos

    return validate_solicitacoes_continuas(
        solicitacao,
        lista_erros,
        inclusoes,
        medicao_programas_projetos,
        "Programas e Projetos",
        True,
    )


# TODO: adicionar testes unitarios
def _validate_solicitacoes_programas_e_projetos_emei_cemei(
    solicitacao, lista_erros, medicao
):
    inclusoes = get_inclusoes_programas_projetos(solicitacao)

    if not inclusoes:
        return lista_erros
    return validate_solicitacoes_continuas_emei_cemei(
        solicitacao,
        lista_erros,
        inclusoes,
        medicao,
        "Programas e Projetos",
        True,
    )


def validate_solicitacoes_etec(solicitacao, lista_erros):
    inclusoes = get_inclusoes_etec(solicitacao)

    if not inclusoes:
        return lista_erros

    medicao_etec = solicitacao.get_medicao_etec

    return validate_solicitacoes_continuas(
        solicitacao, lista_erros, inclusoes, medicao_etec, "ETEC", False
    )


def valida_medicoes_inexistentes_ceu_gestao(solicitacao, lista_erros):
    periodos_escolares_comuns_com_inclusoes_normais = (
        get_periodos_escolares_comuns_com_inclusoes_normais(solicitacao)
    )
    for periodo_escolar in periodos_escolares_comuns_com_inclusoes_normais:
        if not solicitacao.medicoes.filter(
            periodo_escolar__nome=periodo_escolar.nome
        ).exists():
            lista_erros.append(
                {
                    "periodo_escolar": periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas alimentações.",
                }
            )
    lista_erros = valida_medicao_programas_e_projetos_inexistente_ceu_gestao(
        solicitacao, lista_erros
    )
    lista_erros = valida_medicao_etec_inexistente_ceu_gestao(solicitacao, lista_erros)
    return lista_erros


def validate_lancamento_alimentacoes_inclusoes_ceu_gestao(solicitacao, lista_erros):
    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    lista_inclusoes = get_lista_dias_inclusoes_ceu_gestao(solicitacao)
    for inclusao in lista_inclusoes:
        lista_erros = buscar_valores_lancamento_inclusoes(
            inclusao, solicitacao, categoria_medicao, lista_erros
        )
    return erros_unicos(lista_erros)


def validate_lancamento_dietas_inclusoes_ceu_gestao(solicitacao, lista_erros):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    lista_inclusoes = get_lista_dias_inclusoes_ceu_gestao(solicitacao)
    categorias_dietas = CategoriaMedicao.objects.filter(nome__icontains="dieta")
    ids_categorias_existentes_no_mes = list(
        set(
            escola.logs_dietas_autorizadas.filter(
                data__month=mes, data__year=ano, quantidade__gt=0
            )
            .exclude(classificacao__nome="Tipo C")
            .values_list("classificacao", flat=True)
            .distinct()
        )
    )
    classificacoes = ClassificacaoDieta.objects.filter(
        id__in=ids_categorias_existentes_no_mes
    )
    for classificacao in classificacoes:
        for inclusao in lista_inclusoes:
            nomes_campos = ["frequencia"]
            nomes_campos, categoria = get_nomes_campos_categoria(
                nomes_campos, classificacao, categorias_dietas
            )
            nomes_campos = incluir_lanche(
                nomes_campos, "lanche", lista_inclusoes, inclusao
            )
            nomes_campos = incluir_lanche(
                nomes_campos, "lanche_4h", lista_inclusoes, inclusao
            )
            lista_erros = buscar_valores_lancamento_dietas_inclusoes(
                inclusao, solicitacao, categoria, lista_erros, list(set(nomes_campos))
            )
    return erros_unicos(lista_erros)


def valida_medicao_programas_e_projetos_inexistente_ceu_gestao(
    solicitacao, lista_erros
):
    inclusoes = get_inclusoes_programas_projetos(solicitacao)
    if not inclusoes:
        return lista_erros

    medicao_programas_projetos = solicitacao.get_medicao_programas_e_projetos
    if not medicao_programas_projetos:
        lista_erros.append(
            {
                "periodo_escolar": "Programas e Projetos",
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def validate_solicitacoes_programas_e_projetos_ceu_gestao(solicitacao, lista_erros):
    inclusoes = get_inclusoes_programas_projetos(solicitacao)
    medicao_programas_projetos = solicitacao.get_medicao_programas_e_projetos
    if not inclusoes or not medicao_programas_projetos:
        return lista_erros

    return validate_solicitacoes_continuas(
        solicitacao,
        lista_erros,
        inclusoes,
        medicao_programas_projetos,
        "Programas e Projetos",
        True,
        True,
    )


def validate_solicitacoes_programas_e_projetos_emebs(solicitacao, lista_erros):
    inclusoes = get_inclusoes_programas_projetos(solicitacao)
    medicao_programas_projetos = solicitacao.get_medicao_programas_e_projetos
    if not inclusoes or not medicao_programas_projetos:
        return lista_erros

    return validate_solicitacoes_continuas(
        solicitacao,
        lista_erros,
        inclusoes,
        medicao_programas_projetos,
        "Programas e Projetos",
        True,
        False,
        True,
    )


def valida_medicao_etec_inexistente_ceu_gestao(solicitacao, lista_erros):
    inclusoes = get_inclusoes_etec(solicitacao)
    if not inclusoes:
        return lista_erros

    medicao_etec = solicitacao.get_medicao_etec
    if not medicao_etec:
        lista_erros.append(
            {
                "periodo_escolar": "ETEC",
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def validate_solicitacoes_etec_ceu_gestao(solicitacao, lista_erros):
    inclusoes = get_inclusoes_etec(solicitacao)
    medicao_etec = solicitacao.get_medicao_etec
    if not inclusoes or not medicao_etec:
        return lista_erros

    return validate_solicitacoes_continuas(
        solicitacao, lista_erros, inclusoes, medicao_etec, "ETEC", False, True
    )


# TODO: adicionar testes unitarios
def _validate_medicao_cei_cemei(
    lista_erros,
    medicao,
    escola,
    mes,
    ano,
    dias_letivos,
    categoria_alimentacao,
    dias_nao_letivos,
    inclusoes,
):
    categorias_dieta = CategoriaMedicao.objects.exclude(
        nome__icontains="ALIMENTAÇÃO"
    ).exclude(nome__icontains="ENTERAL")

    faixas_etarias = FaixaEtaria.objects.filter(ativo=True)
    logs_faixas_etarias = LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    logs_faixas_etarias_dict = list(
        set(
            logs_faixas_etarias.values_list(
                "data", "periodo_escolar_id", "faixa_etaria_id", "quantidade"
            ).distinct()
        )
    )

    logs_dietas_autorizadas = LogQuantidadeDietasAutorizadasCEI.objects.filter(
        escola=escola, data__month=mes, data__year=ano
    )
    logs_dietas_autorizadas_dict = list(
        set(
            logs_dietas_autorizadas.values_list(
                "data",
                "periodo_escolar_id",
                "faixa_etaria_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )

    lista_erros = validate_lancamento_alimentacoes_medicao_cei_cemei(
        lista_erros,
        dias_letivos,
        medicao,
        faixas_etarias,
        logs_faixas_etarias_dict,
        ano,
        mes,
        categoria_alimentacao,
    )
    lista_erros = validate_lancamento_inclusoes_cei_cemei(
        lista_erros,
        ano,
        mes,
        inclusoes,
        faixas_etarias,
        categoria_alimentacao,
        dias_nao_letivos,
        logs_faixas_etarias,
        medicao,
    )
    lista_erros = validate_lancamento_dietas_cei_cemei(
        lista_erros,
        mes,
        ano,
        categorias_dieta,
        faixas_etarias,
        logs_dietas_autorizadas_dict,
        dias_letivos,
        medicao,
    )
    lista_erros = validate_lancamento_inclusoes_dietas_cei_cemei(
        lista_erros,
        mes,
        ano,
        inclusoes,
        categorias_dieta,
        dias_nao_letivos,
        faixas_etarias,
        logs_dietas_autorizadas,
        medicao,
    )

    return lista_erros


# TODO: adicionar testes unitarios
def _validate_medicao_emei_cemei(
    lista_erros,
    solicitacao,
    escola,
    categoria_alimentacao,
    dias_letivos,
    inclusoes,
    medicao,
    mes,
    ano,
    dias_nao_letivos,
):
    categorias_dieta = CategoriaMedicao.objects.exclude(nome__icontains="ALIMENTAÇÃO")
    logs_dietas_autorizadas = LogQuantidadeDietasAutorizadas.objects.filter(
        escola=escola, data__month=mes, data__year=ano, cei_ou_emei="EMEI"
    )
    logs_dietas_autorizadas_dict = list(
        set(
            logs_dietas_autorizadas.values_list(
                "data",
                "periodo_escolar_id",
                "quantidade",
                "classificacao_id",
            ).distinct()
        )
    )
    lista_erros = validate_lancamento_alimentacoes_medicao_emei_cemei(
        solicitacao, lista_erros, escola, categoria_alimentacao, dias_letivos, medicao
    )
    lista_erros = validate_lancamento_inclusoes_emei_cemei(
        solicitacao, lista_erros, inclusoes, escola, categoria_alimentacao, medicao
    )
    lista_erros = validate_lancamento_dietas_emei_cemei(
        lista_erros,
        mes,
        ano,
        categorias_dieta,
        dias_letivos,
        logs_dietas_autorizadas_dict,
        medicao,
    )
    lista_erros = validate_lancamento_inclusoes_dietas_emei_cemei(
        lista_erros,
        inclusoes,
        categorias_dieta,
        dias_nao_letivos,
        mes,
        ano,
        logs_dietas_autorizadas_dict,
        medicao,
    )
    return lista_erros


# TODO: adicionar testes unitarios
def validate_medicao_cemei(solicitacao):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    categoria_alimentacao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=True
        ).values_list("data__day", flat=True)
    )
    dias_nao_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=False
        ).values_list("data__day", flat=True)
    )
    inclusoes = InclusaoDeAlimentacaoCEMEI.objects.filter(
        escola=escola,
        status=InclusaoDeAlimentacaoCEMEI.workflow_class.CODAE_AUTORIZADO,
        dias_motivos_da_inclusao_cemei__data__month=mes,
        dias_motivos_da_inclusao_cemei__data__year=ano,
        dias_motivos_da_inclusao_cemei__cancelado=False,
    ).order_by("dias_motivos_da_inclusao_cemei__data")
    lista_erros = []

    for medicao in solicitacao.medicoes.all():
        tipo_medicao = medicao.nome_periodo_grupo.upper()
        if tipo_medicao in ["INTEGRAL", "PARCIAL"]:
            lista_erros = _validate_medicao_cei_cemei(
                lista_erros,
                medicao,
                escola,
                mes,
                ano,
                dias_letivos,
                categoria_alimentacao,
                dias_nao_letivos,
                inclusoes,
            )
        elif tipo_medicao == "PROGRAMAS E PROJETOS":
            lista_erros = _validate_solicitacoes_programas_e_projetos_emei_cemei(
                solicitacao, lista_erros, medicao
            )
        elif tipo_medicao == "SOLICITAÇÕES DE ALIMENTAÇÃO":
            lista_erros = validate_lancamento_kit_lanche(solicitacao, lista_erros)
            lista_erros = validate_lanche_emergencial(solicitacao, lista_erros)
        else:
            lista_erros = _validate_medicao_emei_cemei(
                lista_erros,
                solicitacao,
                escola,
                categoria_alimentacao,
                dias_letivos,
                inclusoes,
                medicao,
                mes,
                ano,
                dias_nao_letivos,
            )

    return lista_erros


def valida_medicoes_inexistentes_emebs(solicitacao, lista_erros):
    for periodo_escolar in solicitacao.escola.periodos_escolares(ano=solicitacao.ano):
        if not solicitacao.medicoes.filter(periodo_escolar=periodo_escolar).exists():
            lista_erros.append(
                {
                    "periodo_escolar": periodo_escolar.nome,
                    "erro": "Restam dias a serem lançados nas alimentações.",
                }
            )
    return lista_erros


def validate_lancamento_alimentacoes_medicao_emebs(solicitacao, lista_erros):
    escola = solicitacao.escola
    tipo_unidade = escola.tipo_unidade
    categoria_medicao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    dias_letivos = get_lista_dias_letivos(solicitacao, escola)
    for periodo_escolar in escola.periodos_escolares(solicitacao.ano):
        alimentacoes_permitidas = get_alimentacoes_permitidas(
            solicitacao, escola, periodo_escolar
        )
        vinculo = (
            VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar.objects.get(
                tipo_unidade_escolar=tipo_unidade, periodo_escolar=periodo_escolar
            )
        )
        alimentacoes_vinculadas = vinculo.tipos_alimentacao.exclude(
            nome="Lanche Emergencial"
        )
        alimentacoes_vinculadas = list(
            set(alimentacoes_vinculadas.values_list("nome", flat=True))
        )
        alimentacoes = alimentacoes_vinculadas + alimentacoes_permitidas
        linhas_da_tabela = get_linhas_da_tabela(alimentacoes)
        lista_erros = buscar_valores_lancamento_alimentacoes_emebs(
            linhas_da_tabela,
            solicitacao,
            periodo_escolar,
            dias_letivos,
            categoria_medicao,
            lista_erros,
        )
    return erros_unicos(lista_erros)


def buscar_valores_lancamento_alimentacoes_emebs(
    linhas_da_tabela,
    solicitacao,
    periodo_escolar,
    dias_letivos,
    categoria_medicao,
    lista_erros,
):
    periodo_com_erro = False
    tipos_alunos = (
        LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=solicitacao.escola,
            criado_em__year=solicitacao.ano,
            criado_em__month=solicitacao.mes,
            periodo_escolar=periodo_escolar,
        )
        .exclude(Q(quantidade_alunos=0) | Q(infantil_ou_fundamental="N/A"))
        .values_list("infantil_ou_fundamental", flat=True)
    )
    tipos_alunos = list(set(tipos_alunos))
    for tipo_aluno in tipos_alunos:
        for nome_campo in linhas_da_tabela:
            valores_da_medicao = (
                ValorMedicao.objects.filter(
                    medicao__solicitacao_medicao_inicial=solicitacao,
                    nome_campo=nome_campo,
                    medicao__periodo_escolar=periodo_escolar,
                    dia__in=dias_letivos,
                    categoria_medicao=categoria_medicao,
                    infantil_ou_fundamental=tipo_aluno,
                )
                .exclude(valor=None)
                .values_list("dia", flat=True)
            )
            valores_da_medicao = list(set(valores_da_medicao))
            dias_matriculados_zero = ValorMedicao.objects.filter(
                medicao__solicitacao_medicao_inicial=solicitacao,
                nome_campo="matriculados",
                medicao__periodo_escolar=periodo_escolar,
                dia__in=dias_letivos,
                categoria_medicao=categoria_medicao,
                infantil_ou_fundamental=tipo_aluno,
                valor=0,
            )
            permissoes_especiais = get_permissoes_especiais_da_solicitacao(
                solicitacao, solicitacao.escola, periodo_escolar
            )
            permissoes_especiais_agrupadas_por_dia = (
                agrupa_permissoes_especiais_por_dia(
                    permissoes_especiais, solicitacao.mes, solicitacao.ano
                )
            )
            if len(valores_da_medicao) != (
                len(dias_letivos)
                - (0 if nome_campo == "matriculados" else len(dias_matriculados_zero))
            ):
                diferenca = list(set(dias_letivos) - set(valores_da_medicao))
                for dia_sem_preenchimento in diferenca:
                    valor_matriculados = ValorMedicao.objects.filter(
                        medicao__solicitacao_medicao_inicial=solicitacao,
                        nome_campo="matriculados",
                        medicao__periodo_escolar=periodo_escolar,
                        dia=dia_sem_preenchimento,
                        categoria_medicao=categoria_medicao,
                        infantil_ou_fundamental=tipo_aluno,
                    ).first()
                    if nome_campo in ALIMENTACOES_LANCAMENTOS_ESPECIAIS and (
                        (
                            not permissoes_especiais_agrupadas_por_dia.get(
                                dia_sem_preenchimento
                            )
                        )
                        or (valor_matriculados and valor_matriculados.valor == "0")
                    ):
                        continue
                    valor_observacao = ValorMedicao.objects.filter(
                        medicao__solicitacao_medicao_inicial=solicitacao,
                        nome_campo="observacao",
                        medicao__periodo_escolar=periodo_escolar,
                        dia=dia_sem_preenchimento,
                        categoria_medicao=categoria_medicao,
                        infantil_ou_fundamental=tipo_aluno,
                    ).exclude(valor=None)
                    periodo_com_erro = checa_valor_observacao(
                        valor_observacao, periodo_com_erro
                    )
    return checa_periodo_com_erro(periodo_com_erro, lista_erros, periodo_escolar)


def checa_periodo_com_erro(periodo_com_erro, lista_erros, periodo_escolar):
    if periodo_com_erro:
        lista_erros.append(
            {
                "periodo_escolar": periodo_escolar.nome,
                "erro": "Restam dias a serem lançados nas alimentações.",
            }
        )
    return lista_erros


def checa_valor_observacao(valor_observacao, periodo_com_erro):
    if not valor_observacao:
        periodo_com_erro = True
    return periodo_com_erro


def validate_lancamento_dietas_emebs(solicitacao, lista_erros):
    ano = solicitacao.ano
    mes = solicitacao.mes
    escola = solicitacao.escola
    categorias = CategoriaMedicao.objects.exclude(nome__icontains="ALIMENTAÇÃO")
    logs = escola.logs_dietas_autorizadas.filter(data__month=mes, data__year=ano)
    logs_ = list(
        set(
            logs.values_list(
                "data",
                "periodo_escolar_id",
                "quantidade",
                "classificacao_id",
                "infantil_ou_fundamental",
            ).distinct()
        )
    )
    dias_letivos = list(
        DiaCalendario.objects.filter(
            escola=escola, data__month=mes, data__year=ano, dia_letivo=True
        ).values_list("data__day", flat=True)
    )
    for categoria in categorias:
        classificacoes = get_classificacoes_dietas(categoria)
        for dia in dias_letivos:
            for medicao in solicitacao.medicoes.all():
                valores_medicao_ = list(
                    set(
                        medicao.valores_medicao.values_list(
                            "nome_campo",
                            "categoria_medicao_id",
                            "dia",
                            "infantil_ou_fundamental",
                        )
                    )
                )
                periodo_com_erro = False
                if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                    continue
                periodo_com_erro = (
                    validate_lancamento_alimentacoes_medicao_emebs_dietas(
                        lista_erros,
                        medicao,
                        logs_,
                        ano,
                        mes,
                        dia,
                        categoria,
                        classificacoes,
                        periodo_com_erro,
                        valores_medicao_,
                        escola,
                    )
                )
                if periodo_com_erro:
                    lista_erros.append(
                        {
                            "periodo_escolar": medicao.periodo_escolar.nome,
                            "erro": "Restam dias a serem lançados nas dietas.",
                        }
                    )
    return lista_erros


def validate_lancamento_alimentacoes_medicao_emebs_dietas(
    lista_erros,
    medicao,
    logs_,
    ano,
    mes,
    dia,
    categoria,
    classificacoes,
    periodo_com_erro,
    valores_medicao_,
    escola,
    inclusoes=None,
):
    DATA_INDEX = 0
    PERIODO_ESCOLAR_ID_INDEX = 1
    QUANTIDADE_INDEX = 2
    CLASSIFICACAO_ID_INDEX = 3
    INFANTIL_OU_FUNDAMENTAL_INDEX = 4

    NOME_CAMPO_INDEX = 0
    CATEGORIA_MEDICAO_ID_INDEX = 1
    DIA_ID = 2
    INFANTIL_OU_FUNDAMENTAL_VALOR_INDEX = 3

    nomes_campos = get_nomes_campos_emef_emebs_dietas(
        inclusoes, escola, categoria, medicao
    )
    tipos_alunos = (
        LogQuantidadeDietasAutorizadas.objects.filter(
            escola=escola,
            data__year=ano,
            data__month=mes,
            periodo_escolar=medicao.periodo_escolar,
        )
        .exclude(Q(quantidade=0) | Q(infantil_ou_fundamental="N/A"))
        .values_list("infantil_ou_fundamental", flat=True)
    )
    tipos_alunos = list(set(tipos_alunos))
    for tipo_aluno in tipos_alunos:
        for nome_campo in nomes_campos:
            if lista_erros_com_periodo(lista_erros, medicao, "dietas"):
                continue
            quantidade = 0
            for classificacao in classificacoes:
                log = next(
                    (
                        log_
                        for log_ in logs_
                        if (
                            log_[DATA_INDEX]
                            == datetime.date(int(ano), int(mes), int(dia))
                            and (
                                log_[PERIODO_ESCOLAR_ID_INDEX]
                                == medicao.periodo_escolar.id
                                if medicao.periodo_escolar
                                else None
                            )
                            and log_[CLASSIFICACAO_ID_INDEX] == classificacao.id
                            and log_[INFANTIL_OU_FUNDAMENTAL_INDEX] == tipo_aluno
                        )
                    ),
                    None,
                )
                quantidade += log[QUANTIDADE_INDEX] if log else 0
            if quantidade == 0:
                continue
            valor_medicao = next(
                (
                    valor_medicao_
                    for valor_medicao_ in valores_medicao_
                    if (
                        valor_medicao_[NOME_CAMPO_INDEX] == nome_campo
                        and valor_medicao_[CATEGORIA_MEDICAO_ID_INDEX] == categoria.id
                        and valor_medicao_[DIA_ID] == f"{dia:02d}"
                        and valor_medicao_[INFANTIL_OU_FUNDAMENTAL_VALOR_INDEX]
                        == tipo_aluno
                    )
                ),
                None,
            )
            periodo_com_erro = checa_valor_medicao(valor_medicao, periodo_com_erro)
    return periodo_com_erro


def checa_valor_medicao(valor_medicao, periodo_com_erro):
    if not valor_medicao:
        periodo_com_erro = True
    return periodo_com_erro
