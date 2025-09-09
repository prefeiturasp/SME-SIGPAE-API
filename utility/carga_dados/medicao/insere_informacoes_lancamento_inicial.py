import datetime

from dateutil.relativedelta import relativedelta

from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create import (
    AlteracaoCardapioSerializerCreate,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import (
    MotivoAlteracaoCardapio,
)
from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao_cemei.api.serializers_create import (
    AlteracaoCardapioCEMEISerializerCreate,
)
from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
from sme_sigpae_api.escola.models import (
    FaixaEtaria,
    LogAlunosMatriculadosFaixaEtariaDia,
    LogAlunosMatriculadosPeriodoEscola,
    PeriodoEscolar,
    TipoTurma,
)
from sme_sigpae_api.escola.utils import calendario_sgp
from sme_sigpae_api.inclusao_alimentacao.api.serializers.serializers_create import (
    GrupoInclusaoAlimentacaoNormalCreationSerializer,
    InclusaoAlimentacaoContinuaCreationSerializer,
)
from sme_sigpae_api.inclusao_alimentacao.models import (
    MotivoInclusaoContinua,
    MotivoInclusaoNormal,
)
from sme_sigpae_api.kit_lanche.api.serializers.serializers_create import (
    SolicitacaoKitLancheAvulsaCreationSerializer,
    SolicitacaoKitLancheCEMEICreateSerializer,
)
from sme_sigpae_api.kit_lanche.models import KitLanche
from sme_sigpae_api.perfil.models.usuario import Usuario
from utility.carga_dados.medicao.constantes import (
    ANO,
    DATA_KIT_LANCHE,
    DATA_LANCHE_EMERGENCIAL,
    DIAS_MES,
    MES,
    NOME_USUARIO_CODAE,
    NOME_USUARIO_DRE,
    QUANTIDADE_ALUNOS,
    USERNAME_USUARIO_CODAE,
    USERNAME_USUARIO_DRE,
)


def obter_escolas():
    return [
        {
            "nome_escola": "NOME DA ESCOLA",
            "username": 0000000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": ["MANHA", "TARDE", "INTEGRAL"],
        },
        {
            "nome_escola": "EMEBS NOME DA ESCOLA ",
            "username": 0000000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": {
                "INFANTIL": ["MANHA", "TARDE", "INTEGRAL"],
                "FUNDAMENTAL": ["MANHA", "TARDE", "INTEGRAL", "NOITE"],
            },
        },
        {
            "nome_escola": "CEMEI NOME DA ESCOLA",
            "username": 00000,
            "usuario_escola": "USUARIO DA ESCOLA",
            "periodos": {"EMEI": ["MANHA", "TARDE", "INTEGRAL"], "CEI": ["INTEGRAL"]},
        },
    ]


def obter_usuario(username, nome):
    try:
        return Usuario.objects.get(username=username, nome=nome)
    except Exception:
        print(f"Nenhum usuário encontrado com  username={username} e nome={nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()


def habilitar_dias_letivos(escolas, data=None):
    if not data:
        data = datetime.date(ANO, MES, 1)
    print(f"Data: {data.strftime("%d/%m/%Y")}")
    print(f"Escolas: {", ".join(escolas)}")

    calendario_sgp(data, escolas)
    print(f"O mês referente a data {data.strftime("%d/%m/%Y")} agora é letivo")

    data_kit_lanche = data_solicitacao_kit_lanche()
    calendario_sgp(data_kit_lanche, escolas)
    print(
        f"A data do pedido de kit lanche {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo"
    )

    data_lanche_emergencial = data_solicitacao_kit_lanche()
    calendario_sgp(data_lanche_emergencial, escolas)
    print(
        f"A data do pedido do lanche emergencial {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo"
    )


# **************************** **************************** LOG DE ALUNOS MATRICULADOS **************************** ****************************


def incluir_log_alunos_matriculados(periodos, escola):
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola, periodo_escolar=pe, quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
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
                infantil_ou_fundamental="INFANTIL",
                quantidade_alunos=QUANTIDADE_ALUNOS,
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do INFANTIL para o Período {periodo} cadastrados")

    for periodo in periodo_fundamental:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, DIAS_MES + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                tipo_turma=TipoTurma.REGULAR.name,
                infantil_ou_fundamental="FUNDAMENTAL",
                quantidade_alunos=QUANTIDADE_ALUNOS,
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do FUNDAMENTAL para o Período {periodo} cadastrados")


def incluir_log_alunos_matriculados_cei(periodos, escola):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for faixa in faixas:
            for dia in range(1, DIAS_MES + 1):
                data = datetime.date(ANO, MES, dia)
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=QUANTIDADE_ALUNOS,
                    faixa_etaria=faixa,
                    data=data,
                )
                log_faixa.save()
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    id=log_faixa.id
                ).update(criado_em=data)

            print(f"Logs do Período {periodo} para faixa {faixa.__str__()} cadastrados")


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
                cei_ou_emei="CEI",
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período {periodo} cadastrados")

        for faixa in faixas:
            for dia in range(1, DIAS_MES + 1):
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=QUANTIDADE_ALUNOS,
                    faixa_etaria=faixa,
                    data=datetime.date(ANO, MES, dia),
                )
                log_faixa.save()
                data = datetime.date(ANO, MES, dia)
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    id=log_faixa.id
                ).update(criado_em=data)

            print(f"Logs do Período {periodo} para faixa {faixa.__str__()} cadastrados")


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
                cei_ou_emei=cei_ou_emei,
            )
            log.save()
            data = datetime.date(ANO, MES, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período INTANTIL {periodo} cadastrados")


# **************************** **************************** SOLICITAÇÃO DE KIT LANCHE **************************** ****************************


def data_solicitacao_kit_lanche():
    data = datetime.datetime.now() + relativedelta(months=1)
    return data.date()


def solicitar_kit_lanche(escola, usuario):

    queryset = KitLanche.objects.filter(
        edital__uuid__in=escola.editais,
        tipos_unidades=escola.tipo_unidade,
        status=KitLanche.ATIVO,
    )

    if not queryset.exists():
        print(f"Nenhum kit encontrado para escola {escola.nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()
    kit = queryset.first()
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    solicitacao_json = {
        "solicitacao_kit_lanche": {
            "kits": [kit],
            "data": data_solicitacao_kit_lanche(),
            "tempo_passeio": "0",
        },
        "escola": escola,
        "local": "Casa da História",
        "evento": "Semana da História",
        "quantidade_alunos": 10,
        "alunos_com_dieta_especial_participantes": [],
        "status": "RASCUNHO",
    }
    context = {"request": type("Request", (), {"user": usuario})}
    solicitacao_kit_lanche_avulsa = SolicitacaoKitLancheAvulsaCreationSerializer(
        context=context
    ).create(solicitacao_json)
    solicitacao_kit_lanche_avulsa.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: SolicitacaoKitLancheAvulsa UUID={solicitacao_kit_lanche_avulsa.uuid}"
    )

    solicitacao_kit_lanche_avulsa.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    solicitacao_kit_lanche_avulsa.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    dia_passeio = datetime.date(ANO, MES, DATA_KIT_LANCHE)
    solicitacao_kit_lanche = solicitacao_kit_lanche_avulsa.solicitacao_kit_lanche
    solicitacao_kit_lanche.data = dia_passeio
    solicitacao_kit_lanche.save()
    print(f"Data da solicitação alterada para {dia_passeio.strftime('%d/%m/%Y')}")

    return solicitacao_kit_lanche


def solicitar_kit_lanche_cemei(escola, usuario):
    queryset = KitLanche.objects.filter(
        edital__uuid__in=escola.editais,
        tipos_unidades=escola.tipo_unidade,
        status=KitLanche.ATIVO,
    )
    if not queryset.exists():
        print(f"Nenhum kit encontrado para escola {escola.nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()
    kit = queryset.first()
    faixas = FaixaEtaria.objects.filter(ativo=True)
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    faixas_quantidades = []
    for faixa in faixas:
        faixas_quantidades.append(
            {
                "faixa_etaria": faixa,
                "matriculados_quando_criado": 5,
                "quantidade_alunos": 1,
            }
        )

    solicitacao_json = {
        "escola": escola,
        "solicitacao_cei": {
            "kits": [kit],
            "alunos_com_dieta_especial_participantes": [],
            "faixas_quantidades": faixas_quantidades,
            "tempo_passeio": 0,
        },
        "solicitacao_emei": {
            "kits": [kit],
            "alunos_com_dieta_especial_participantes": [],
            "tempo_passeio": 0,
            "matriculados_quando_criado": QUANTIDADE_ALUNOS,
            "quantidade_alunos": 20,
        },
        "observacao": "<p>Nenhuma</p>",
        "status": "RASCUNHO",
        "local": "Casa Rural",
        "evento": "Semana da Agropecuária",
        "data": data_solicitacao_kit_lanche(),
    }

    context = {"request": type("Request", (), {"user": usuario})}
    solicitacao_kit_lanche_cemei = SolicitacaoKitLancheCEMEICreateSerializer(
        context=context
    ).create(solicitacao_json)
    solicitacao_kit_lanche_cemei.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: SolicitacaoKitLancheCEMEI UUID={solicitacao_kit_lanche_cemei.uuid}"
    )

    solicitacao_kit_lanche_cemei.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    solicitacao_kit_lanche_cemei.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    dia_passeio = datetime.date(ANO, MES, DATA_KIT_LANCHE)
    solicitacao_kit_lanche_cemei.data = dia_passeio
    solicitacao_kit_lanche_cemei.save()
    print(f"Data da solicitação alterada para {dia_passeio.strftime('%d/%m/%Y')}")

    return solicitacao_kit_lanche_cemei


# **************************** **************************** SOLICITAÇÃO DE LANCHE EMERGENCIAL **************************** ****************************


def data_solicitacao_lanche_emergencial():
    data = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data.date()


def solicitar_lanche_emergencial(escola, usuario, periodo_escolar):

    data = data_solicitacao_lanche_emergencial()
    motivo = MotivoAlteracaoCardapio.objects.get(nome="Lanche Emergencial")
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    tipo_lanche_emergencial = TipoAlimentacao.objects.get(nome="Lanche Emergencial")
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    solicitacao_json = {
        "escola": escola,
        "motivo": motivo,
        "observacao": "<p>Devido as chuvas, haverá corte de energia elétrica para manutenção da rede</p>",
        "data_inicial": data,
        "data_final": data,
        "datas_intervalo": [{"data": data}],
        "substituicoes": [
            {
                "qtd_alunos": "5",
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao_de": [tipo_alimentacao],
                "tipos_alimentacao_para": [tipo_lanche_emergencial],
            }
        ],
    }
    context = {"request": type("Request", (), {"user": usuario})}
    solicitacao_lanche_emergencial = AlteracaoCardapioSerializerCreate(
        context=context
    ).create(solicitacao_json)

    solicitacao_lanche_emergencial.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: AlteracaoCardapio UUID={solicitacao_lanche_emergencial.uuid}"
    )

    solicitacao_lanche_emergencial.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    solicitacao_lanche_emergencial.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    dia_lanche_emergencial = datetime.date(ANO, MES, DATA_LANCHE_EMERGENCIAL)
    solicitacao_lanche_emergencial.data_final = dia_lanche_emergencial
    solicitacao_lanche_emergencial.data_inicial = dia_lanche_emergencial
    solicitacao_lanche_emergencial.save()

    data_intervalo = solicitacao_lanche_emergencial.datas_intervalo.get()
    data_intervalo.data = dia_lanche_emergencial
    data_intervalo.save()

    print(
        f"Data da solicitação alterada para {dia_lanche_emergencial.strftime('%d/%m/%Y')}"
    )

    return solicitacao_lanche_emergencial


def solicitar_lanche_emergencial_cemei(escola, usuario, periodo_escolar):

    data = data_solicitacao_lanche_emergencial()
    motivo = MotivoAlteracaoCardapio.objects.get(nome="Lanche Emergencial")
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    tipo_lanche_emergencial = TipoAlimentacao.objects.get(nome="Lanche Emergencial")
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    solicitacao_json = {
        "escola": escola,
        "motivo": motivo,
        "alunos_cei_e_ou_emei": "EMEI",
        "alterar_dia": data,
        "substituicoes_cemei_cei_periodo_escolar": [],
        "substituicoes_cemei_emei_periodo_escolar": [
            {
                "qtd_alunos": "10",
                "matriculados_quando_criado": QUANTIDADE_ALUNOS,
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao_de": [tipo_alimentacao],
                "tipos_alimentacao_para": [tipo_lanche_emergencial],
            }
        ],
        "observacao": "<p>nenhuma</p>",
        "datas_intervalo": [{"data": data}],
    }
    context = {"request": type("Request", (), {"user": usuario})}
    solicitacao_lanche_emergencial = AlteracaoCardapioCEMEISerializerCreate(
        context=context
    ).create(solicitacao_json)

    solicitacao_lanche_emergencial.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: AlteracaoCardapioCEMEI UUID={solicitacao_lanche_emergencial.uuid}"
    )

    solicitacao_lanche_emergencial.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    solicitacao_lanche_emergencial.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    dia_lanche_emergencial = datetime.date(ANO, MES, DATA_LANCHE_EMERGENCIAL)
    solicitacao_lanche_emergencial.data_final = dia_lanche_emergencial
    solicitacao_lanche_emergencial.data_inicial = dia_lanche_emergencial
    solicitacao_lanche_emergencial.save()

    data_intervalo = solicitacao_lanche_emergencial.datas_intervalo.get()
    data_intervalo.data = dia_lanche_emergencial
    data_intervalo.save()

    print(
        f"Data da solicitação alterada para {dia_lanche_emergencial.strftime('%d/%m/%Y')}"
    )

    return solicitacao_lanche_emergencial


# **************************** **************************** PROGRAMAS E PROJETOS **************************** ****************************
def data_programas_e_projetos_etec():
    data_inicial = datetime.datetime.now() + relativedelta(months=1)
    data_final = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data_inicial.date(), data_final.date()


def incluir_programas_e_projetos(escola, usuario, periodo_escolar):

    data_inicial, data_final = data_programas_e_projetos_etec()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoContinua.objects.get(nome="Programas/Projetos Específicos")
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)
    solicitacao_json = {
        "escola": escola,
        "status": "RASCUNHO",
        "quantidades_periodo": [
            {
                "dias_semana": ["0", "1", "2", "3", "4"],
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao": [tipo_alimentacao],
                "numero_alunos": "10",
                "observacao": "<p>nenhuma</p>",
            }
        ],
        "motivo": motivo,
        "data_inicial": data_inicial,
        "data_final": data_final,
    }
    context = {"request": type("Request", (), {"user": usuario})}
    programas_e_projetos = InclusaoAlimentacaoContinuaCreationSerializer(
        context=context
    ).create(solicitacao_json)
    programas_e_projetos.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: InclusaoAlimentacaoContinua UUID={programas_e_projetos.uuid}"
    )
    programas_e_projetos.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    programas_e_projetos.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    nova_data_inicio = datetime.date(ANO, MES, DATA_KIT_LANCHE)
    nova_data_fim = datetime.date(ANO, MES, DATA_KIT_LANCHE) + relativedelta(days=5)
    programas_e_projetos.data_final = nova_data_fim
    programas_e_projetos.data_inicial = nova_data_inicio
    programas_e_projetos.save()

    print(
        f"Data da solicitação alterada para {nova_data_inicio.strftime('%d/%m/%Y')} até {nova_data_fim.strftime('%d/%m/%Y')}"
    )
    return programas_e_projetos


# **************************** **************************** ETEC **************************** ****************************


def incluir_etec(escola, usuario, periodo_escolar):

    data_inicial, data_final = data_programas_e_projetos_etec()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoContinua.objects.get(nome="ETEC")
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    solicitacao_json = {
        "escola": escola,
        "status": "RASCUNHO",
        "quantidades_periodo": [
            {
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao": [tipo_alimentacao],
                "numero_alunos": "10",
                "observacao": "<p>nenhuma</p>",
            }
        ],
        "motivo": motivo,
        "data_inicial": data_inicial,
        "data_final": data_final,
    }

    context = {"request": type("Request", (), {"user": usuario})}

    etec = InclusaoAlimentacaoContinuaCreationSerializer(context=context).create(
        solicitacao_json
    )
    etec.inicia_fluxo(user=usuario)
    print(f"Solicitação cadastrada: InclusaoAlimentacaoContinua UUID={etec.uuid}")

    etec.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    etec.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    nova_data_inicio = datetime.date(ANO, MES, DATA_LANCHE_EMERGENCIAL)
    nova_data_fim = datetime.date(ANO, MES, DATA_LANCHE_EMERGENCIAL) + relativedelta(
        days=5
    )
    etec.data_final = nova_data_fim
    etec.data_inicial = nova_data_inicio
    etec.save()

    print(
        f"Data da solicitação alterada para {nova_data_inicio.strftime('%d/%m/%Y')} até {nova_data_fim.strftime('%d/%m/%Y')}"
    )

    return etec


# **************************** **************************** SOLICITAÇÕES CEU GESTÃO **************************** ****************************


def incluir_solicitacoes_ceu_gestao(escola, usuario, periodos_escolares):

    data = data_solicitacao_kit_lanche()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoNormal.objects.get(nome="Evento Específico")
    usuario_dre = obter_usuario(USERNAME_USUARIO_DRE, NOME_USUARIO_DRE)
    usuario_codae = obter_usuario(USERNAME_USUARIO_CODAE, NOME_USUARIO_CODAE)

    quantidades_periodo = []

    for periodo in periodos_escolares:
        quantidades_periodo.append(
            {
                "periodo_escolar": periodo,
                "tipos_alimentacao": [tipo_alimentacao],
                "numero_alunos": "10",
            }
        )
    solicitacao_json = {
        "escola": escola,
        "inclusoes": [
            {
                "motivo": motivo,
                "data": data,
                "evento": "Evento para conscientização de higiene bucal",
            }
        ],
        "quantidades_periodo": quantidades_periodo,
        "status": "RASCUNHO",
    }

    context = {"request": type("Request", (), {"user": usuario})}

    ceu_gestao = GrupoInclusaoAlimentacaoNormalCreationSerializer(
        context=context
    ).create(solicitacao_json)

    ceu_gestao.inicia_fluxo(user=usuario)
    print(
        f"Solicitação cadastrada: GrupoInclusaoAlimentacaoNormal UUID={ceu_gestao.uuid}"
    )

    ceu_gestao.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")

    ceu_gestao.codae_autoriza(
        user=usuario_codae, justificativa="Sem observações por parte da CODAE"
    )
    print("Solicitação aprovado pela CODAE")

    nova_data = datetime.date(ANO, MES, DATA_KIT_LANCHE)
    periodo = ceu_gestao.inclusoes_normais.all()[0]
    periodo.data = nova_data
    periodo.save()
    ceu_gestao.save()

    print(f"Data da solicitação alterada para {nova_data.strftime('%d/%m/%Y')}")

    return ceu_gestao
