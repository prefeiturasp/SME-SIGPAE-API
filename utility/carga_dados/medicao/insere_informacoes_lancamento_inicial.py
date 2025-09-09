import datetime
from dateutil.relativedelta import relativedelta
from sme_sigpae_api.escola.utils import calendario_sgp
from utility.carga_dados.medicao.constantes import ANO, DIAS_MES, MES, QUANTIDADE_ALUNOS

def obter_escolas():
    return [
        {
            "nome_escola": "NOME DA ESCOLA",
            "username": 0000000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": ["MANHA", "TARDE", "INTEGRAL"]
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


def incluir_log_alunos_matriculados(periodos, escola):
    from sme_sigpae_api.escola.models import LogAlunosMatriculadosPeriodoEscola, PeriodoEscolar
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
