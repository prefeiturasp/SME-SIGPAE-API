import datetime
from dateutil.relativedelta import relativedelta
from sme_sigpae_api.escola.utils import calendario_sgp
from utility.carga_dados.medicao.constantes import ANO, DIAS_MES, MES, QUANTIDADE_ALUNOS
from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola, PeriodoEscolar, TipoTurma, FaixaEtaria, LogAlunosMatriculadosFaixaEtariaDia
    
    
def obter_escolas():
    return [
        {
            "nome_escola": "NOME DA ESCOLA",
            "username": 0000000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": ["MANHA", "TARDE", "INTEGRAL"]
        },
        {
            "nome_escola": "EMEBS NOME DA ESCOLA ",
            "username": 0000000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": {
                "INFANTIL": ["MANHA", "TARDE", "INTEGRAL"],
                "FUNDAMENTAL": ["MANHA", "TARDE", "INTEGRAL", "NOITE"]
            }
        },
        {
            "nome_escola": "CEMEI NOME DA ESCOLA",
            "username": 00000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": {
                "EMEI": ["MANHA", "TARDE", "INTEGRAL"],
                "CEI": ["INTEGRAL"]
            }
        },
    ]
    
    
def habilitar_dias_letivos(escolas, data=None):
    if not data:
        data = datetime.date(ANO, MES, 1)
    print(f"Data: {data.strftime("%d/%m/%Y")}")
    print(f"Escolas: {", ".join(escolas)}")
    
    calendario_sgp(data, escolas)
    print(f"O mês referente a data {data.strftime("%d/%m/%Y")} agora é letivo")

    data_kit_lanche = data_solicitacao_kit_lanche()
    calendario_sgp(data_kit_lanche, escolas)
    print(f"A data do pedido de kit lanche {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo")

    data_lanche_emergencial = data_solicitacao_kit_lanche()
    calendario_sgp(data_lanche_emergencial, escolas)
    print(f"A data do pedido do lanche emergencial {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo")


def data_solicitacao_kit_lanche():
    data = datetime.datetime.now() + relativedelta(months=1)
    return data.date()


def data_solicitacao_lanche_emergencial():
    data = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data.date()

# **************************** **************************** LOG DE ALUNOS MATRICULADOS **************************** ****************************

def incluir_log_alunos_matriculados(periodos, escola):
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
        print(f"Logs do Período {periodo} cadastrados")


def incluir_log_alunos_matriculados_emebs(periodos, escola):
    periodo_infantil = periodos["INFANTIL"]
    periodo_fundamental = periodos["FUNDAMENTAL"]
    
    for periodo in periodo_infantil:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                tipo_turma=TipoTurma.REGULAR.name,
                infantil_ou_fundamental='INFANTIL',
                quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
        print(f"Logs do INFANTIL para o Período {periodo} cadastrados")
        
    for periodo in periodo_fundamental:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                tipo_turma=TipoTurma.REGULAR.name,
                infantil_ou_fundamental='FUNDAMENTAL',
                quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
        print(f"Logs do FUNDAMENTAL para o Período {periodo} cadastrados")


def incluir_log_alunos_matriculados_cei(periodos, escola):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            data = datetime.date(ANO, MES, dia)
            for faixa in faixas:
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=QUANTIDADE_ALUNOS,
                    faixa_etaria=faixa,
                    data=data
                )
                log_faixa.save()
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(id=log_faixa.id).update(criado_em=data)

        print(f"Logs do Período {periodo} cadastrados")
       

def incluir_log_alunos_matriculados_cei_da_cemei(periodos, escola):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    
    for periodo in periodos["CEI"]:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=QUANTIDADE_ALUNOS,
                tipo_turma=TipoTurma.REGULAR.name,
                cei_ou_emei="CEI"
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
            
            for faixa in faixas:
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=QUANTIDADE_ALUNOS,
                    faixa_etaria=faixa,
                    data=datetime.date(ANO, MES, dia)
                )
                log_faixa.save()
                data = datetime.date(ANO, MES, dia)
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(id=log_faixa.id).update(criado_em=data)

        print(f"Logs do Período {periodo} cadastrados")
        
        
def incluir_log_alunos_matriculados_emei_da_cemei(periodos, escola):
    for periodo in periodos["EMEI"]:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        cei_ou_emei = "EMEI" if pe.nome == "INTEGRAL" else "N/A"
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=QUANTIDADE_ALUNOS,
                tipo_turma=TipoTurma.REGULAR.name,
                cei_ou_emei=cei_ou_emei
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(criado_em=data)
        print(f"Logs do Período INTANTIL {periodo} cadastrados")