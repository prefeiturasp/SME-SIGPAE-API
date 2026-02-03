import datetime
import os
from datetime import date

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()


from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import AlteracaoCardapio
from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasRecreioNasFerias,
    SolicitacaoDietaEspecial,
)
from sme_sigpae_api.escola.models import (
    DiaCalendario,
    Escola,
    GrupoUnidadeEscolar,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoUnidadeEscolar,
)
from sme_sigpae_api.escola.utils import calendario_sgp, dias_letivos_noturno
from sme_sigpae_api.medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial, ValorMedicao, CategoriaMedicao

# ./manage.py habilitar_lancamento_medicao_inicial --ano 2025 --mes 3 --data-kit-lanche 11 --data-lanche-emergencial 14

def deletar_valores_medicao2():
    # mes_medicao = mes
    # ano_medicao = ano
    # status = ["MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"]
    # solicitacoes = SolicitacaoMedicaoInicial.objects.filter(
    #     escola__nome=nome_escola, mes=mes_medicao, ano=ano_medicao, status__in=status
    # )
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(uuid='e434ebf5-33f1-4b9b-a13c-50f66860aef6')
    for solicitacao in solicitacoes:
        print(f"Solicitacao da escola {solicitacao.escola.nome}")
        medicoes = solicitacao.medicoes.all()
        for medicao in medicoes:
            if medicao.grupo:
                print(f"Deletando Grupo {medicao.grupo.nome}")
            else:
                print(f"Deletando Período Escolar {medicao.periodo_escolar.nome}")
            medicao.valores_medicao.all().delete()
        print()
        solicitacao.delete()


def log_dietas_autorizadas():
    from sme_sigpae_api.dieta_especial.models import LogQuantidadeDietasAutorizadas

    escolas = []
    for nome in escolas:
        escola = Escola.objects.get(nome=nome)
        log = LogAlunosMatriculadosPeriodoEscola.objects.filter(
            escola=escola, criado_em__year=2025, criado_em__month=12
        )
        log_dietas = LogQuantidadeDietasAutorizadas.objects.filter(
            escola=escola, data__year=2025, data__month=12
        )


def alterar_data_alteracao_de_cardapio():

    solicitacao_lanche_emergencial = AlteracaoCardapio.objects.get(
        uuid="4e3ac1b6-1523-44b3-894f-0023e64a08c5"
    )
    dia_lanche_emergencial = datetime.date(2024, 10, 15)
    solicitacao_lanche_emergencial.data_final = dia_lanche_emergencial
    solicitacao_lanche_emergencial.data_inicial = dia_lanche_emergencial
    solicitacao_lanche_emergencial.save()

    data_intervalo = solicitacao_lanche_emergencial.datas_intervalo.get()
    data_intervalo.data = dia_lanche_emergencial
    data_intervalo.save()


def cria_solicitacao_medicao_inicial_mes_atual(nome_escola, mes, ano):
    import datetime
    import logging

    from dateutil.relativedelta import relativedelta

    from sme_sigpae_api.medicao_inicial.tasks import (
        buscar_solicitacao_mes_anterior,
        copiar_alunos_periodo_parcial,
        copiar_responsaveis,
        criar_nova_solicitacao,
        solicitacao_medicao_atual_existe,
    )
    from sme_sigpae_api.perfil.models.usuario import Usuario

    logger = logging.getLogger(__name__)
    data_hoje = datetime.date(int(ano), int(mes), 6)  # datetime.date.today()
    data_mes_anterior = data_hoje + relativedelta(months=-1)
    escola = Escola.objects.get(nome=nome_escola)
    if not solicitacao_medicao_atual_existe(escola, data_hoje):
        try:
            solicitacao_mes_anterior = buscar_solicitacao_mes_anterior(
                escola, data_mes_anterior
            )
            solicitacao_atual = criar_nova_solicitacao(
                solicitacao_mes_anterior, escola, data_hoje
            )
            copiar_responsaveis(solicitacao_mes_anterior, solicitacao_atual)

            if solicitacao_atual.ue_possui_alunos_periodo_parcial:
                copiar_alunos_periodo_parcial(
                    solicitacao_mes_anterior, solicitacao_atual
                )
            usuario_admin = Usuario.objects.get(email="system@admin.com")
            solicitacao_atual.inicia_fluxo(user=usuario_admin)
        except SolicitacaoMedicaoInicial.DoesNotExist:
            message = (
                "x-x-x-x Não existe Solicitação de Medição Inicial para a escola "
                f"{escola.nome} no mês anterior ({data_mes_anterior.month:02d}/"
                f"{data_mes_anterior.year}) x-x-x-x"
            )
            logger.info(message)


def atualiza_periodo_noturno():
    from sme_sigpae_api.escola.models import Escola, PeriodoEscolar
    from sme_sigpae_api.escola.utils import dias_letivos_gerais, dias_letivos_noturno

    periodo_noite = PeriodoEscolar.objects.get(nome="NOITE")
    data_inicio = "2026-01-01"
    data_fim = "2026-01-31"
    for escola in [Escola.objects.get(nome="CEI DIRET ALICE APARECIDA DE SOUZA , PROFA")]:
        dias_letivos_gerais(escola, data_inicio, data_fim)
        dias_letivos_noturno(escola, data_inicio, data_fim, periodo_noite)


# def atualiza_periodo_noturno():
#     from datetime import date

#     from sme_sigpae_api.escola.utils import calendario_sgp

#     data_inicio = date(2025, 10, 1)
#     calendario_sgp(data_inicio=data_inicio)


def encontrar_erro_eol():
    from sme_sigpae_api.escola.models import (
        AlunosMatriculadosPeriodoEscola,
        PeriodoEscolar,
    )

    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    logs = AlunosMatriculadosPeriodoEscola.objects.filter(
        alterado_em__year=2026,
        alterado_em__month=1,
        alterado_em__day=1,
        criado_em__year=2026,
        criado_em__month=1,
        criado_em__day=1,
        periodo_escolar=periodo_integral,
        tipo_turma="REGULAR",
    )
    for log in logs:
        print(f"{log.escola.nome} - {log.escola.diretoria_regional.nome}")


def remove_log_dia_31():
    from sme_sigpae_api.escola.models import (
        Escola,
        LogAlunosMatriculadosPeriodoEscola,
        PeriodoEscolar,
    )

    escolas = [
        "EMEF ALEXANDRE DE GUSMAO",
        "EMEF ALEXANDRE VANNUCHI LEME",
        "EMEF ANTONIO PEREIRA IGNACIO",
        "EMEF CAIO SERGIO POMPEU DE TOLEDO, DEP.",
        "EMEF CAMILO CASTELO BRANCO",
        "EMEF CLAUDIA BARTOLOMAZI, PROFA.",
        "EMEF ELIAS SHAMMASS",
        "EMEF FULVIO ABRAMO",
        "EMEF GIORGIO GAGLIANI CAPUTO, PE.",
        "EMEF HELINA COUTINHO LOURENCO ALVES, PROFESSORA",
        "EMEF IDEMIA DE GODOY, PROFA.",
        "EMEF INES BREGA CORDEIRO, PROFA.",
        "EMEF JOAO DE LIMA PAIVA, PROF.",
        "EMEF JUSCELINO KUBITSCHEK DE OLIVEIRA, PRES.",
        "EMEF MARIA APARECIDA MAGNANELLI FERNANDES, PROFA",
        "EMEF MEIRE DE JESUS RIBEIRO,PROF.",
        "EMEF SATURNINO PEREIRA",
        "EMEF VINTE E CINCO DE JANEIRO",
        "CEU EMEI INACIO MONTEIRO",
        "EMEI ELISA KAUFFMANN ABRAMOVICH",
    ]
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    try:
        for n, nome_escola in enumerate(escolas):
            print(f"Processando {n}: {nome_escola}")
            escola = Escola.objects.get(nome=nome_escola)
            log_mat = LogAlunosMatriculadosPeriodoEscola.objects.filter(
                criado_em__year=2025,
                criado_em__month=12,
                periodo_escolar=periodo_integral,
                tipo_turma="REGULAR",
                escola=escola,
            )
            if log_mat.count() == 1 and log_mat.criado_em.day == 31:
                try:
                    log_mat.delete()
                    print("-> Deletado")
                except Exception as ex:
                    print(f"-> Erro ao deletar: {ex}")
            else:
                print(f"-> Não Deletado. Registro do dia {log_mat.criado_em.day}")

    except Exception as ex:
        print(f"-> Erro: {ex}")

def remove_medicao_integral():
    from sme_sigpae_api.escola.models import PeriodoEscolar
    from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial

    ano = "2025"
    mes = "12"
    escolas = [
        "EMEF BELKICE MANHAES REIS, PROFA.",
        "EMEF CLARINA AMARAL GURGEL, PROFA.",
        "EMEF DAMIAO, FREI",
        "EMEF ELIZA RACHEL MACEDO DE SOUZA, PROFA.",
        "EMEF ERNESTINO LOPES DA SILVA, PROF.",
        "EMEF GERSON DE MOURA MUZEL, PROF.",
        "EMEF HEITOR DE ANDRADE",
        "EMEF JOAO DE DEUS CARDOSO DE MELLO",
        "EMEF JOSE AMADEI, ENG.",
        "EMEF MIGUEL VIEIRA FERREIRA, DR.",
        "EMEF MILTON FERREIRA DE ALBUQUERQUE, PROF.",
        "EMEF OLEGARIO MARIANO",
        "EMEF PEDRO GERALDO SCHUNCK",
        "EMEF PLINIO SALGADO",
        "EMEF TEODOMIRO TOLEDO PIZA, DES.",
        "EMEF VARGEM GRANDE II",
        "EMEI LUIS TRAVASSOS",
        "EMEI OSVALDO CORDEIRO DE FARIAS, MAL.",
        "EMEF ANDRE RODRIGUES DE ALCKMIN, PROF.",
        "EMEF CECILIA MORAES DE VASCONCELOS, PROFA.",
        "EMEF DALILA DE ANDRADE COSTA, PROFA.",
        "EMEF ERICO VERISSIMO",
        "EMEF FREDERICO GUSTAVO DOS SANTOS, TTE. AVIADOR",
        "EMEF GARCIA DAVILA, CTE.",
        "EMEF GILBERTO DUPAS, PROF",
        "EMEF JARDIM DAMASCENO I - PROFESSOR JOAO ANTONIO FELICIO",
        "EMEF JOAO AMOS COMENIUS",
        "EMEF JOSE HERMINIO RODRIGUES, CEL. PM",
        "EMEF LILIAN MASO, PROFA",
        "EMEF MARCILIO DIAS",
        "EMEF OSMAR BASTOS CONCEICAO, PROF.",
        "EMEF TAUNAY, VISCONDE DE",
        "EMEF THEO DUTRA",
        "EMEF ZILKA SALABERRY DE CARVALHO",
        "EMEI 25 DE JANEIRO",
        "EMEI ANTONIO CALLADO",
        "EMEI MADALENA CARAMURU",
        "EMEI MARIA LUCIA PETIT DA SILVA, PROFA.",
        "EMEF ANTONIO CARLOS DE ANDRADA E SILVA",
        "EMEF ARMANDO CRIDEY RIGHETTI",
        "EMEF CAPISTRANO DE ABREU",
        "EMEF CARLOS PASQUALE, PROF.",
        "EMEF EPITACIO PESSOA, PRES.",
        "EMEF EUZEBIO ROCHA FILHO",
        "EMEF EZEQUIEL RAMOS JUNIOR",
        "EMEF JOSE AMERICO DE ALMEIDA",
        "EMEF JOSE BENTO DE ASSIS, PROF.",
        "EMEF JOSE BORGES ANDRADE",
        "EMEF JOSE BORGES DOS SANTOS JUNIOR, REV.",
        "EMEF JOSE HONORIO RODRIGUES",
        "EMEF JOSE MARIO PIRES AZANHA, PROF.",
        "EMEF JURANDI GOMES DE ARAUJO, PROF.",
        "EMEF LAURO CELIDONIO GOMES DOS REIS, DR.",
        "EMEF LUIS SAIA, ARQ.",
        "EMEF NEUZA AVELINO DA SILVA MELO",
        "EMEF NEWTON REIS, GEN.",
        "EMEF NILDO DO AMARAL JUNIOR, PE.",
        "EMEF PEDRO ALEIXO, DR.",
        "EMEF PEDRO FUKUYEI YAMAGUCHI FERREIRA",
        "EMEF RAIMUNDO CORREIA",
        "EMEF THOMAZ RODRIGUES ALCKMIN",
        "EMEF VICENTE AMATO SOBRINHO, COM.",
        "EMEI ALDO GIANNINI, ENG.",
        "EMEI APARECIDA DE LOURDES CARRILHO JARDIM, PROFA",
        "EMEI JOSE DE ALENCAR",
        "EMEI LOURO ROSA",
    ]
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    for nome_escola in escolas:
        solicitacoes = SolicitacaoMedicaoInicial.objects.filter(
            escola__nome=nome_escola, mes=mes, ano=ano
        )
        for solicitacao in solicitacoes:
            print(f"Solicitacao da escola {solicitacao.escola.nome}")
            medicao_integral = solicitacao.medicoes.filter(
                periodo_escolar=periodo_integral
            )
            if medicao_integral.exists():
                medicao_integral.first().delete()
                print("---> Medição integral deletada!")

def verifica_valores_medicao():
    mes_medicao = "01"
    ano_medicao = "2026"
    nome_escola = ""
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(
        escola__nome=nome_escola, mes=mes_medicao, ano=ano_medicao
    )
    periodo_manha = PeriodoEscolar.objects.get(nome="MANHA")
    periodo_tarde = PeriodoEscolar.objects.get(nome="TARDE")

    for solicitacao in solicitacoes:
        print(f"Solicitacao da escola {solicitacao.escola.nome}")
        medicao_manha = solicitacao.medicoes.filter(periodo_escolar=periodo_manha)
        print(f"MANHA: {medicao_manha.first().valores_medicao.count()}")

        medicao_tarde = solicitacao.medicoes.filter(periodo_escolar=periodo_tarde)
        print(f"TARDE: {medicao_tarde.first().valores_medicao.count()}")

def logs_dietas_especiais_recreio():
    import datetime
    from sme_sigpae_api.dieta_especial.models import ClassificacaoDieta, LogQuantidadeDietasAutorizadasRecreioNasFerias
    from sme_sigpae_api.escola.models import Escola
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    ano = 2025
    mes = 12
    escola = Escola.objects.get(nome="EMEF ANGELINA MAFFEI VITA, DA.")
    for dia in range(9, 23):
        if dia not in [13, 14, 20, 21]:
            for classificacao in classificacoes_dieta:
                log = LogQuantidadeDietasAutorizadasRecreioNasFerias(
                    escola=escola,
                    quantidade=2,
                    data=datetime.date(ano, mes, dia),
                    classificacao=classificacao,
                )
                log.save()
                data = datetime.date(ano, mes, dia)
                LogQuantidadeDietasAutorizadasRecreioNasFerias.objects.filter(
                    id=log.id
                ).update(criado_em=data)

def logs_cei():
    from sme_sigpae_api.dieta_especial.models import ClassificacaoDieta, LogQuantidadeDietasAutorizadasCEI
    from sme_sigpae_api.escola.models import Escola, FaixaEtaria, TipoTurma, LogAlunosMatriculadosFaixaEtariaDia
    
    CLASSIFICACAO_DIETA_NOME_TIPO_A = "Tipo A"
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    faixas = FaixaEtaria.objects.filter(ativo=True)
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    escola = Escola.objects.get(nome="CEI DIRET ALICE APARECIDA DE SOUZA , PROFA")
    quantidade_alunos = int(100 / faixas.count())
    
    # for dia in range(1, 31 + 1):
    #     log = LogAlunosMatriculadosPeriodoEscola(
    #         escola=escola,
    #         periodo_escolar=periodo_integral,
    #         quantidade_alunos=quantidade_alunos * faixas.count(),
    #         tipo_turma=TipoTurma.REGULAR.name,
    #     )
    #     log.save()
    #     data = datetime.date(2026, 1, dia)
    #     LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
    #         criado_em=data
    #     )
    
    for faixa in faixas:
        for dia in range(1, 31 + 1):
            data = datetime.date(2026, 1, dia)
            log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                escola=escola,
                periodo_escolar=periodo_integral,
                quantidade=quantidade_alunos,
                faixa_etaria=faixa,
                data=data,
            )
            log_faixa.save()
            LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                id=log_faixa.id
            ).update(criado_em=data)

        print(f"Logs do Período {periodo_integral} para faixa {faixa.__str__()} cadastrados")
    
    # for periodo in [periodo_integral]:
    #     for classificacao in classificacoes_dieta:
    #         quantidade = 1 if CLASSIFICACAO_DIETA_NOME_TIPO_A in classificacao.nome else 2
    #         for faixa in faixas:
    #             for dia in range(1, 31 + 1):
    #                 log = LogQuantidadeDietasAutorizadasCEI(
    #                     escola=escola,
    #                     periodo_escolar=periodo,
    #                     quantidade=quantidade,
    #                     data=datetime.date(2026, 1, dia),
    #                     classificacao=classificacao,
    #                     faixa_etaria=faixa,
    #                 )
    #                 log.save()
    #             print(
    #                 f"Logs dieta {classificacao.nome} para faixa {faixa.__str__()} no Período {periodo} cadastrados"
    #             )

def deletar_valores_medicao(nome_escola, mes, ano):
    mes_medicao = mes
    ano_medicao = ano
    status = ["MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"]
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(
        escola__nome=nome_escola, mes=mes_medicao, ano=ano_medicao, status__in=status
    )
    for solicitacao in solicitacoes:
        print(f"Solicitacao da escola {solicitacao.escola.nome}")
        medicoes = solicitacao.medicoes.all()
        for medicao in medicoes:
            if medicao.grupo:
                print(f"Deletando os valores do Grupo {medicao.grupo.nome}")
            else:
                print(f"Deletando os valores do Período Escolar {medicao.periodo_escolar.nome}")
            medicao.valores_medicao.all().delete()
            print()
        
def exibe_criado_em_medicao():
    uuid_prod = "f60989ab-4308-40e2-8416-da837a391269"
    nome_escola = "EMEF MAILSON DELANE, PROF."
    mes_medicao = '01'
    ano_medicao = '2026'
    solicitacoes = SolicitacaoMedicaoInicial.objects.filter(uuid=uuid_prod, escola__nome=nome_escola, mes=mes_medicao, ano=ano_medicao, status__in=["MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE"])
    for solicitacao in solicitacoes:
        print(f"Solicitacao da escola {solicitacao.escola.nome}")
        medicoes = solicitacao.medicoes.all()
        for medicao in medicoes:
            if medicao.grupo:
                print(f"Grupo {medicao.grupo.nome}: criado em {medicao.criado_em.strftime("%d/%m/%Y")}")
            else:
                print(f"Período Escolar {medicao.periodo_escolar.nome} criado em {medicao.criado_em.strftime("%d/%m/%Y")}")
            print(medicao.criado_em)
        print()
        
def busca_medicoes_iguais():
    from sme_sigpae_api.medicao_inicial.models import Medicao, CategoriaMedicao
    alimentacao = CategoriaMedicao.objects.get(nome="ALIMENTAÇÃO")
    # dia = "01"
    medicoes = Medicao.objects.filter(
        valores_medicao__nome_campo="frequencia",
        valores_medicao__valor="246",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).filter(
        valores_medicao__nome_campo="lanche",
        valores_medicao__valor="164",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).filter(
        valores_medicao__nome_campo="refeicao",
        valores_medicao__valor="169",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).filter(
        valores_medicao__nome_campo="repeticao_refeicao",
        valores_medicao__valor="14",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).filter(
        valores_medicao__nome_campo="sobremesa",
        valores_medicao__valor="174",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).filter(
        valores_medicao__nome_campo="repeticao_sobremesa",
        valores_medicao__valor="12",
        # valores_medicao__dia=dia,
        valores_medicao__categoria_medicao=alimentacao
    ).distinct()
    for medicao in medicoes:
        solicitacao = medicao.solicitacao_medicao_inicial
        print(f"Solicitação: UUID {solicitacao.uuid}")
        print(f"{solicitacao.escola.nome} - {solicitacao.mes}/{solicitacao.ano}")
        if medicao.grupo:
            print(f"Grupo {medicao.grupo.nome}: criado em {medicao.criado_em.strftime("%d/%m/%Y")}")
        else:
            print(f"Período Escolar {medicao.periodo_escolar.nome} criado em {medicao.criado_em.strftime("%d/%m/%Y")}")
        print()
        
def resetar_medicao(uuid_solicitacao):
    from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
    # uuid_solicitacao = ''
    s = SolicitacaoMedicaoInicial.objects.get(uuid=uuid_solicitacao)
    s.status = s.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
    s.logs.last().delete()
    s.save()
    for m in s.medicoes.all():
        m.status = m.workflow_class.MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE
        m.logs.last().delete()
        m.save()

def remove_semana_vazia():
    import json
    solicitacao = SolicitacaoMedicaoInicial.objects.get(uuid="")
    historico = solicitacao.historico
    historico_json = json.loads(historico)

    for alteracao in historico_json[0].get("alteracoes"):
        for tabela in alteracao.get('tabelas_lancamentos', []):
            tabela['semanas'] = [semana for semana in tabela.get('semanas', []) if semana.get('semana', '') != '']
            
    solicitacao.historico = json.dumps(historico_json)
    solicitacao.save()

def pesquisa_data_criacao_geral():
    datas_unicas = set()
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    solicitacao = SolicitacaoMedicaoInicial.objects.get(escola__nome="EMEF MAILSON DELANE, PROF.", mes="01", ano="2026")
    medicao_integral = solicitacao.medicoes.get(periodo_escolar=periodo_integral)
    for valor in medicao_integral.valores_medicao.all():
        datas_unicas.add(valor.criado_em)
    for data in sorted(datas_unicas):
        print(data.strftime('%d/%m/%Y'))
        
def pesquisa_data_criacao_mailson():
    import datetime
    periodo_integral = PeriodoEscolar.objects.get(nome="INTEGRAL")
    solicitacao = SolicitacaoMedicaoInicial.objects.get(escola__nome="EMEF MAILSON DELANE, PROF.", mes="01", ano="2026")
    medicao_integral = solicitacao.medicoes.get(periodo_escolar=periodo_integral)
    for valor in medicao_integral.valores_medicao.filter(criado_em__date=datetime.date(2026, 1, 5), semana="1"):
        print(f"Dia {valor.dia} da semana {valor.semana} para {valor.tipo_alimentacao}({valor.nome_campo}) e categoria {valor.categoria_medicao.nome}: criado em {valor.criado_em.strftime("%d/%m/%Y %H:%M:%S")}")
        
def pesquisa_data_criacao_pedro():
    import datetime
    periodo_manha = PeriodoEscolar.objects.get(nome="MANHA")
    solicitacao = SolicitacaoMedicaoInicial.objects.get(escola__nome="EMEF PEDRO AMERICO", mes="01", ano="2026")
    medicao_integral = solicitacao.medicoes.get(periodo_escolar=periodo_manha)
    for valor in medicao_integral.valores_medicao.filter(dia__in=["16", "17", "18"], semana="3"):
        print(f"Dia {valor.dia} da semana {valor.semana} para {valor.tipo_alimentacao}({valor.nome_campo}) e categoria {valor.categoria_medicao.nome}: criado em {valor.criado_em.strftime("%d/%m/%Y %H:%M:%S")}")


def backup():
    from sme_sigpae_api.medicao_inicial.models import SolicitacaoMedicaoInicial
    mes_medicao = "01"
    ano_medicao = "2026"
    escolas = ["EMEF MAILSON DELANE, PROF.", "EMEF PEDRO AMERICO", "CEI DIRET MARIELCIA FLORENCIO DE MORAIS, PROFA"]
    for nome_escola in escolas:
        solicitacao = SolicitacaoMedicaoInicial.objects.get(
            escola__nome=nome_escola, mes=mes_medicao, ano=ano_medicao, recreio_nas_ferias__isnull=True
        )
        print(f"Solicitacao da escola {solicitacao.escola.nome} [{solicitacao.uuid}] criado em {solicitacao.criado_em.strftime("%d/%m/%Y %H:%M:%S")}")
        medicoes = solicitacao.medicoes.all()
        for medicao in medicoes:
            if medicao.grupo:
                print(f"Grupo {medicao.grupo.nome} [{medicao.uuid}]: criado em {medicao.criado_em.strftime("%d/%m/%Y %H:%M:%S")} e alterado em {medicao.alterado_em.strftime("%d/%m/%Y %H:%M:%S") if medicao.alterado_em else "Não encontrado"}")
            else:
                print(f"Período Escolar {medicao.periodo_escolar.nome} [{medicao.uuid}]: criado em {medicao.criado_em.strftime("%d/%m/%Y %H:%M:%S")} e alterado em {medicao.alterado_em.strftime("%d/%m/%Y %H:%M:%S") if medicao.alterado_em else "Não encontrado"}")
        print()

        
if __name__ == "__main__":
    # deletar_valores_medicao('CEI DIRET ODILIA ALVES ALMEIDA SANTOS', '11', '2023')
    # resetar_medicao("604bf78d-378e-42bf-aa6e-641dfed09570")
    # atualiza_periodo_noturno()
    # logs_cei()
    # teste = [
    #     {
    #         "usuario": {
    #             "uuid": "49ee0ab2-51c6-4ec6-b2ab-7a9eec8ffe3d",
    #             "nome": "JESSICA PRISCILA GOMES DRUMOND",
    #             "username": "8785571",
    #             "email": "jessica.drumond@sme.prefeitura.sp.gov.br"
    #         },
    #         "criado_em": "13/01/2026 14:58:15",
    #         "acao": "MEDICAO_CORRECAO_SOLICITADA_CODAE",
    #         "alteracoes": [
    #             {
    #                 "periodo_escolar": "TARDE",
    #                 "justificativa": "<p>Prezados, boa tarde!</p><p>Nos dias 18 e 19, os números de matriculados constam como zerados. Solicitamos, por gentileza, a correção dessas informações.</p><p>Atenciosamente,</p>",
    #                 "tabelas_lancamentos": [
    #                     {
    #                         "categoria_medicao": "ALIMENTAÇÃO",
    #                         "semanas": [
    #                             {
    #                                 "semana": "",
    #                                 "dias": [
    #                                     "18",
    #                                     "19"
    #                                 ]
    #                             },
    #                             {
    #                                 "semana": "3",
    #                                 "dias": [
    #                                     "18",
    #                                     "19"
    #                                 ]
    #                             }
    #                         ]
    #                     },
    #                     {
    #                         "categoria_medicao": "DIETA ESPECIAL - TIPO B",
    #                         "semanas": [
    #                             {
    #                                 "semana": "",
    #                                 "dias": [
    #                                     "19"
    #                                 ]
    #                             },
    #                             {
    #                                 "semana": "3",
    #                                 "dias": [
    #                                     "19"
    #                                 ]
    #                             }
    #                         ]
    #                     }
    #                 ]
    #             },
    #             {
    #                 "periodo_escolar": "MANHA",
    #                 "justificativa": "<p>Prezados, boa tarde!</p><p>Nos dias 18 e 19, os números de matriculados constam como zerados. Solicitamos, por gentileza, a correção dessas informações.</p><p>Atenciosamente,</p>",
    #                 "tabelas_lancamentos": [
    #                     {
    #                         "categoria_medicao": "ALIMENTAÇÃO",
    #                         "semanas": [
    #                             {
    #                                 "semana": "",
    #                                 "dias": [
    #                                     "18",
    #                                     "19"
    #                                 ]
    #                             },
    #                             {
    #                                 "semana": "3",
    #                                 "dias": [
    #                                     "18",
    #                                     "19"
    #                                 ]
    #                             }
    #                         ]
    #                     },
    #                     {
    #                         "categoria_medicao": "DIETA ESPECIAL - TIPO B",
    #                         "semanas": [
    #                             {
    #                                 "semana": "",
    #                                 "dias": [
    #                                     "19"
    #                                 ]
    #                             },
    #                             {
    #                                 "semana": "3",
    #                                 "dias": [
    #                                     "19"
    #                                 ]
    #                             }
    #                         ]
    #                     }
    #                 ]
    #             }
    #         ]
    #     }
    # ]
    # historico_str = json.dumps(teste)
    # deletar_valores_medicao2()
    # remove_semana_vazia()
    # solicitacao = SolicitacaoMedicaoInicial.objects.get(escola__nome="EMEBS MARIO PEREIRA BICUDO, PROF.", mes="03", ano="2025", recreio_nas_ferias__isnull=True)
    # pesquisa_data_criacao()
    # backup()
    # for dia in [11, 12, 13]:
    #     log = LogQuantidadeDietasAutorizadas(
    #         escola=Escola.objects.get(nome="CIEJA CLOVIS CAITANO MIQUELAZZO - IPIRANGA"),
    #         periodo_escolar=None,
    #         quantidade=3,
    #         data=datetime.date(2025, 3, dia),
    #         classificacao=ClassificacaoDieta.objects.get(nome="Tipo B"),
    #     )
    #     log.save()
    
    dieta = SolicitacaoDietaEspecial.objects.get(uuid='d81f71ab-6216-4646-8a72-4f9cc3db4b3b')
    