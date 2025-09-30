import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.contenttypes.models import ContentType

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
from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
)
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
from sme_sigpae_api.perfil.models.perfil import Perfil, Vinculo
from sme_sigpae_api.perfil.models.usuario import Usuario

QUANTIDADE_ALUNOS = 100


def dados_usuario_periodos():

    return [
        # ESCOLA EMEF
        {
            "nome_escola": "",
            "email": "escolaemef@admin.com",
            "periodos": ["MANHA", "TARDE", "NOITE", "INTEGRAL"],
        },
        # ESCOLA EMEI
        {
            "nome_escola": "",
            "email": "escolaemei@admin.com",
            "periodos": ["MANHA", "TARDE", "INTEGRAL"],
        },
        # ESCOLA CIEJA
        {
            "nome_escola": "",
            "email": "escolacieja@admin.com",
            "periodos": ["MANHA", "TARDE", "NOITE", "INTERMEDIARIO", "VESPERTINO"],
        },
        # ESCOLA CEU GESTÃO
        {
            "nome_escola": "",
            "email": "ceugestao@admin.com",
            "periodos": ["MANHA", "TARDE", "NOITE", "INTEGRAL"],
        },
        # ESCOLA EMEBS
        {
            "nome_escola": "",
            "email": "escolaemebs@admin.com",
            "periodos": {
                "INFANTIL": ["MANHA", "TARDE", "INTEGRAL"],
                "FUNDAMENTAL": ["MANHA", "TARDE", "INTEGRAL", "NOITE"],
            },
        },
        # ESCOLA CEMEI
        {
            "nome_escola": "",
            "email": "escolacemei@admin.com",
            "periodos": {"EMEI": ["MANHA", "TARDE", "INTEGRAL"], "CEI": ["INTEGRAL"]},
        },
        # ESCOLA CEI
        {
            "nome_escola": "",
            "email": "escolacei@admin.com",
            "periodos": ["MANHA", "TARDE", "INTEGRAL"],
        },
    ]


def obter_usuario_dre(diretoria_regional, index):
    try:
        content_type = ContentType.objects.get(
            app_label="escola", model="diretoriaregional"
        )
        perfil = Perfil.objects.get(nome="COGESTOR_DRE")
        vinculo = Vinculo.objects.filter(
            content_type=content_type, object_id=diretoria_regional.id, perfil=perfil
        ).first()
        usuario = vinculo.usuario.email
        print(f"{index}.1 Usuário DRE: {usuario}")
    except Exception as e:
        print(f"----> Erro ao buscar usuário DRE:\n{e}")
        raise

    return usuario


def obter_escolas():
    "Escolas da mesma DRE"
    erro = False
    dados = dados_usuario_periodos()
    for index, informacao in enumerate(dados, start=1):
        usuario = obter_usuario(informacao["email"])
        try:
            instituicao = usuario.vinculo_atual.instituicao
            informacao["nome_escola"] = instituicao.nome
            print(
                f"{index}. {informacao["email"]} está vinculado a escola {informacao["nome_escola"]}"
            )
            informacao["usuario_dre"] = obter_usuario_dre(
                instituicao.diretoria_regional, index
            )
        except Exception as e:
            erro = True
            print(f"----> Erro ao buscar vinculo para {informacao["email"]}:\n{e}")

    if erro:
        print("================== SCRIP CANCELADO ==================")
        exit()

    return dados


def obter_usuario(email):
    try:
        return Usuario.objects.get(email=email)
    except Exception:
        print(f"Nenhum usuário encontrado com  email {email}")
        print("================== SCRIP CANCELADO ==================")
        exit()


def obter_usuario_codae():
    return obter_usuario(email="codae@admin.com")


def habilitar_dias_letivos(escolas, data):

    print(f"1.Habilitando a data {data.strftime("%d/%m/%Y")} para as escolas: ")
    print(f"{"\n".join(escolas)}")
    calendario_sgp(data, escolas)
    print(f"1.1 O mês referente a data {data.strftime("%d/%m/%Y")} agora é letivo")

    data_kit_lanche = data_solicitacao_kit_lanche()
    calendario_sgp(data_kit_lanche, escolas)
    print(
        f"2. A data do pedido de kit lanche {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo"
    )

    data_lanche_emergencial = data_solicitacao_lanche_emergencial()
    calendario_sgp(data_lanche_emergencial, escolas)
    print(
        f"3. A data do pedido do lanche emergencial {data_kit_lanche.strftime("%d/%m/%Y")} agora é letivo"
    )


# **************************** **************************** VERIFICANDO DADOS INICIAIS **************************** ****************************
def verifica_dados_iniciais():
    print("1. Verificando Kit")
    kit_lanche()
    print("2. Verificando Faixa Etaria")
    faixas_etarias()
    print("3. Verificando MotivoAlteracaoCardapio")
    motivo_alteracao_cardapio()
    print("4. Verificando TipoAlimentacao")
    tipo_alimentacao()
    print("5. Verificando MotivoInclusaoContinua")
    motivo_inclusao_continua()
    print("6. Verificando MotivoInclusaoNormal")
    motivo_inclusao_normal()
    print("7. Verificando ClassificacaoDieta")
    classificacao_dieta()


def kit_lanche():
    kit = KitLanche.objects.filter(
        status=KitLanche.ATIVO,
    )
    if not kit.exists():
        print("1.1 Nenhum kit encontrado. Cadastrando ...")
        KitLanche.objects.create(
            nome="Kit - Medicao Inicial",
            status=KitLanche.ATIVO,
            descricao="<p>Suco e Bolo</p>",
        ).save()
        print("1.2 Kit cadastrado.")


def faixas_etarias():
    faixas = FaixaEtaria.objects.filter(ativo=True)
    if not faixas.exists():
        print("2.1. Nenhuma faixa encontrada. Cadastrando ...")

        faixas_etarias = [
            FaixaEtaria(inicio=0, fim=1, ativo=True),
            FaixaEtaria(inicio=1, fim=4, ativo=True),
            FaixaEtaria(inicio=4, fim=6, ativo=True),
            FaixaEtaria(inicio=6, fim=7, ativo=True),
            FaixaEtaria(inicio=7, fim=12, ativo=True),
            FaixaEtaria(inicio=12, fim=48, ativo=True),
            FaixaEtaria(inicio=48, fim=73, ativo=True),
        ]
        FaixaEtaria.objects.bulk_create(faixas_etarias)
        print("2.2. Faixas cadastradas.")


def motivo_alteracao_cardapio():
    lanche_emergencial = MotivoAlteracaoCardapio.objects.filter(
        nome="Lanche Emergencial"
    )
    if not lanche_emergencial.exists():
        print(
            " 3.1. Nenhum MotivoAlteracaoCardapio para Lanche Emergencial encontrado. Cadastrando..."
        )
        MotivoAlteracaoCardapio.objects.create(
            nome="Lanche Emergencial", ativo=True
        ).save()
        print("3.2. MotivoAlteracaoCardapio Lanche Emergencial cadastrado.")


def tipo_alimentacao():
    lanche_quatro_horas = TipoAlimentacao.objects.filter(nome="Lanche 4h")
    if not lanche_quatro_horas.exists():
        print("4.1. Nenhum TipoAlimentacao para Lanche 4h encontrado. Cadastrando...")
        TipoAlimentacao.objects.create(nome="Lanche 4h").save()
        print("4.2. TipoAlimentacao Lanche 4h cadastrado.")

    lanche_emergencial = TipoAlimentacao.objects.filter(nome="Lanche Emergencial")
    if not lanche_emergencial.exists():
        print(
            " 4.3. Nenhum TipoAlimentacao para Lanche emergencial encontrado. Cadastrando..."
        )
        TipoAlimentacao.objects.create(nome="Lanche Emergencial").save()
        print("4.4. TipoAlimentacao Lanche Emergencial cadastrado.")


def motivo_inclusao_continua():
    programa_projetos = MotivoInclusaoContinua.objects.filter(
        nome="Programas/Projetos Específicos"
    )
    if not programa_projetos.exists():
        print(
            " 5.1. Nenhum MotivoInclusaoContinua para Programas/Projetos Específicos encontrado. Cadastrando..."
        )
        MotivoInclusaoContinua.objects.create(
            nome="Programas/Projetos Específicos"
        ).save()
        print("5.2. MotivoInclusaoContinua Programas/Projetos Específicos cadastrado.")

    etec = MotivoInclusaoContinua.objects.filter(nome="ETEC")
    if not etec.exists():
        print("5.3 Nenhum MotivoInclusaoContinua para ETEC encontrado. Cadastrando...")
        MotivoInclusaoContinua.objects.create(nome="ETEC").save()
        print("5.4 MotivoInclusaoContinua ETEC cadastrado.")


def motivo_inclusao_normal():
    evento = MotivoInclusaoNormal.objects.filter(nome="Evento Específico")
    if not evento.exists():
        print(
            " 6.1 Nenhum MotivoInclusaoNormal para Evento Específico encontrado. Cadastrando..."
        )
        MotivoInclusaoNormal.objects.create(nome="Evento Específico").save()
        print("6.2 MotivoInclusaoNormal Evento Específico cadastrado.")


def classificacao_dieta():
    classificacao = ClassificacaoDieta.objects.all()
    if not classificacao.exists():
        print("7.1. Nenhuma ClassificacaoDieta encontrada. Cadastrando ...")
        classificacao = [
            ClassificacaoDieta(nome="Tipo A"),
            ClassificacaoDieta(nome="Tipo A RESTRIÇÃO DE AMINOÁCIDOS"),
            ClassificacaoDieta(nome="Tipo A ENTERAL"),
            ClassificacaoDieta(nome="Tipo B"),
            ClassificacaoDieta(nome="Tipo C"),
        ]
        ClassificacaoDieta.objects.bulk_create(classificacao)
        print("7.2. ClassificacaoDieta cadastradas.")


# **************************** **************************** LOG DE ALUNOS MATRICULADOS **************************** ****************************


def incluir_log_alunos_matriculados(periodos, escola, ano, mes, quantidade_dias_mes):
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola, periodo_escolar=pe, quantidade_alunos=QUANTIDADE_ALUNOS
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período {periodo} cadastrados")


def incluir_log_alunos_matriculados_emebs(
    periodos, escola, ano, mes, quantidade_dias_mes
):
    periodo_infantil = periodos["INFANTIL"]
    periodo_fundamental = periodos["FUNDAMENTAL"]

    for periodo in periodo_infantil:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                tipo_turma=TipoTurma.REGULAR.name,
                infantil_ou_fundamental="INFANTIL",
                quantidade_alunos=QUANTIDADE_ALUNOS,
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do INFANTIL para o Período {periodo} cadastrados")

    for periodo in periodo_fundamental:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                tipo_turma=TipoTurma.REGULAR.name,
                infantil_ou_fundamental="FUNDAMENTAL",
                quantidade_alunos=QUANTIDADE_ALUNOS,
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do FUNDAMENTAL para o Período {periodo} cadastrados")


def incluir_log_alunos_matriculados_cei(
    periodos, escola, ano, mes, quantidade_dias_mes
):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    quantidade_alunos = int(QUANTIDADE_ALUNOS / faixas.count())
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=quantidade_alunos * faixas.count(),
                tipo_turma=TipoTurma.REGULAR.name,
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período {periodo} cadastrados")
        for faixa in faixas:
            for dia in range(1, quantidade_dias_mes + 1):
                data = datetime.date(ano, mes, dia)
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=quantidade_alunos,
                    faixa_etaria=faixa,
                    data=data,
                )
                log_faixa.save()
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    id=log_faixa.id
                ).update(criado_em=data)

            print(f"Logs do Período {periodo} para faixa {faixa.__str__()} cadastrados")


def incluir_log_alunos_matriculados_cei_da_cemei(
    periodos, escola, ano, mes, quantidade_dias_mes
):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    quantidade_alunos = int(QUANTIDADE_ALUNOS / faixas.count())

    for periodo in periodos["CEI"]:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=quantidade_alunos * faixas.count(),
                tipo_turma=TipoTurma.REGULAR.name,
                cei_ou_emei="CEI",
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período {periodo} cadastrados")

        for faixa in faixas:
            for dia in range(1, quantidade_dias_mes + 1):
                log_faixa = LogAlunosMatriculadosFaixaEtariaDia(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=quantidade_alunos,
                    faixa_etaria=faixa,
                    data=datetime.date(ano, mes, dia),
                )
                log_faixa.save()
                data = datetime.date(ano, mes, dia)
                LogAlunosMatriculadosFaixaEtariaDia.objects.filter(
                    id=log_faixa.id
                ).update(criado_em=data)

            print(f"Logs do Período {periodo} para faixa {faixa.__str__()} cadastrados")


def incluir_log_alunos_matriculados_emei_da_cemei(
    periodos, escola, ano, mes, quantidade_dias_mes
):
    for periodo in periodos["EMEI"]:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        cei_ou_emei = "EMEI" if pe.nome == "INTEGRAL" else "N/A"
        for dia in range(1, quantidade_dias_mes + 1):
            log = LogAlunosMatriculadosPeriodoEscola(
                escola=escola,
                periodo_escolar=pe,
                quantidade_alunos=QUANTIDADE_ALUNOS,
                tipo_turma=TipoTurma.REGULAR.name,
                cei_ou_emei=cei_ou_emei,
            )
            log.save()
            data = datetime.date(ano, mes, dia)
            LogAlunosMatriculadosPeriodoEscola.objects.filter(id=log.id).update(
                criado_em=data
            )
        print(f"Logs do Período INTANTIL {periodo} cadastrados")


# **************************** **************************** SOLICITAÇÃO DE KIT LANCHE **************************** ****************************


def data_solicitacao_kit_lanche():
    data = datetime.datetime.now() + relativedelta(months=1)
    return data.date()


def solicitar_kit_lanche(escola, usuario, ano, mes, data_kit_lanche, usuario_dre):

    queryset = KitLanche.objects.filter(
        status=KitLanche.ATIVO,
    )

    if not queryset.exists():
        print(f"Nenhum kit encontrado para escola {escola.nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()
    kit = queryset.first()
    usuario_codae = obter_usuario_codae()

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

    dia_passeio = datetime.date(ano, mes, data_kit_lanche)
    solicitacao_kit_lanche = solicitacao_kit_lanche_avulsa.solicitacao_kit_lanche
    solicitacao_kit_lanche.data = dia_passeio
    solicitacao_kit_lanche.save()
    print(f"Data da solicitação alterada para {dia_passeio.strftime('%d/%m/%Y')}")

    return solicitacao_kit_lanche


def solicitar_kit_lanche_cemei(escola, usuario, ano, mes, data_kit_lanche, usuario_dre):
    queryset = KitLanche.objects.filter(
        status=KitLanche.ATIVO,
    )
    if not queryset.exists():
        print(f"Nenhum kit encontrado para escola {escola.nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()
    kit = queryset.first()
    faixas = FaixaEtaria.objects.filter(ativo=True)
    usuario_codae = obter_usuario_codae()

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

    dia_passeio = datetime.date(ano, mes, data_kit_lanche)
    solicitacao_kit_lanche_cemei.data = dia_passeio
    solicitacao_kit_lanche_cemei.save()
    print(f"Data da solicitação alterada para {dia_passeio.strftime('%d/%m/%Y')}")

    return solicitacao_kit_lanche_cemei


# **************************** **************************** SOLICITAÇÃO DE LANCHE EMERGENCIAL **************************** ****************************


def data_solicitacao_lanche_emergencial():
    data = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data.date()


def solicitar_lanche_emergencial(
    escola, usuario, periodo_escolar, ano, mes, data_lanche_emercencial, usuario_dre
):

    data = data_solicitacao_lanche_emergencial()
    motivo = MotivoAlteracaoCardapio.objects.get(nome="Lanche Emergencial")
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    tipo_lanche_emergencial = TipoAlimentacao.objects.get(nome="Lanche Emergencial")
    usuario_codae = obter_usuario_codae()

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

    dia_lanche_emergencial = datetime.date(ano, mes, data_lanche_emercencial)
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


def solicitar_lanche_emergencial_cemei(
    escola, usuario, periodo_escolar, ano, mes, data_lanche_emercencial, usuario_dre
):

    data = data_solicitacao_lanche_emergencial()
    motivo = MotivoAlteracaoCardapio.objects.get(nome="Lanche Emergencial")
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    tipo_lanche_emergencial = TipoAlimentacao.objects.get(nome="Lanche Emergencial")
    usuario_codae = obter_usuario_codae()

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

    dia_lanche_emergencial = datetime.date(ano, mes, data_lanche_emercencial)
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


def incluir_programas_e_projetos(
    escola, usuario, periodo_escolar, ano, mes, data_kit_lanche, usuario_dre
):

    data_inicial, data_final = data_programas_e_projetos_etec()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoContinua.objects.get(nome="Programas/Projetos Específicos")
    usuario_codae = obter_usuario_codae()
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

    nova_data_inicio = datetime.date(ano, mes, data_kit_lanche)
    nova_data_fim = datetime.date(ano, mes, data_kit_lanche) + relativedelta(days=2)
    programas_e_projetos.data_final = nova_data_fim
    programas_e_projetos.data_inicial = nova_data_inicio
    programas_e_projetos.save()

    print(
        f"Data da solicitação alterada para {nova_data_inicio.strftime('%d/%m/%Y')} até {nova_data_fim.strftime('%d/%m/%Y')}"
    )
    return programas_e_projetos


# **************************** **************************** ETEC **************************** ****************************


def incluir_etec(
    escola, usuario, periodo_escolar, ano, mes, data_lanche_emergencial, usuario_dre
):

    data_inicial, data_final = data_programas_e_projetos_etec()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoContinua.objects.get(nome="ETEC")
    usuario_codae = obter_usuario_codae()

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

    nova_data_inicio = datetime.date(ano, mes, data_lanche_emergencial)
    nova_data_fim = datetime.date(ano, mes, data_lanche_emergencial) + relativedelta(
        days=2
    )
    etec.data_final = nova_data_fim
    etec.data_inicial = nova_data_inicio
    etec.save()

    print(
        f"Data da solicitação alterada para {nova_data_inicio.strftime('%d/%m/%Y')} até {nova_data_fim.strftime('%d/%m/%Y')}"
    )

    return etec


# **************************** **************************** SOLICITAÇÕES CEU GESTÃO **************************** ****************************


def incluir_solicitacoes_ceu_gestao(
    escola, usuario, periodos_escolares, ano, mes, data_kit_lanche, usuario_dre
):

    data = data_solicitacao_kit_lanche()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoNormal.objects.get(nome="Evento Específico")
    usuario_codae = obter_usuario_codae()

    quantidades_periodo = []

    for periodo in periodos_escolares:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        quantidades_periodo.append(
            {
                "periodo_escolar": pe,
                "tipos_alimentacao": [tipo_alimentacao],
                "numero_alunos": "50",
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

    nova_data = datetime.date(ano, mes, data_kit_lanche)
    periodo_inclusao = ceu_gestao.inclusoes_normais.all()[0]
    periodo_inclusao.data = nova_data
    periodo_inclusao.save()
    ceu_gestao.save()

    print(f"Data da solicitação alterada para {nova_data.strftime('%d/%m/%Y')}")

    return ceu_gestao


# **************************** **************************** DIETAS ESPECIAIS **************************** ****************************


def incluir_dietas_especiais(escola, periodos_escolares, ano, mes, quantidade_dias_mes):
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    quantidade = 2
    for periodo in periodos_escolares:
        for classificacao in classificacoes_dieta:
            for dia in range(1, quantidade_dias_mes + 1):
                log = LogQuantidadeDietasAutorizadas(
                    escola=escola,
                    periodo_escolar=periodo,
                    quantidade=quantidade,
                    data=datetime.date(ano, mes, dia),
                    classificacao=classificacao,
                )
                log.save()
            print(
                f"Logs da dieta {classificacao.nome} para o Período {periodo} cadastrados"
            )


def incluir_dietas_especiais_ceu_gestao(escola, ano, mes, dia_kit_lanche):
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    quantidade = 2

    for classificacao in classificacoes_dieta:
        log = LogQuantidadeDietasAutorizadas(
            escola=escola,
            periodo_escolar=None,
            quantidade=quantidade,
            data=datetime.date(ano, mes, dia_kit_lanche),
            classificacao=classificacao,
        )
        log.save()
        print(f"Logs da dieta {classificacao.nome} cadastrados")


def incluir_dietas_especiais_emebs(escola, ano, mes, quantidade_dias_mes, periodos):
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")

    cadastra_periodo_emebs(
        escola,
        classificacoes_dieta,
        periodos["INFANTIL"],
        quantidade_dias_mes,
        ano,
        mes,
        "INFANTIL",
    )

    cadastra_periodo_emebs(
        escola,
        classificacoes_dieta,
        periodos["FUNDAMENTAL"],
        quantidade_dias_mes,
        ano,
        mes,
        "FUNDAMENTAL",
    )


def cadastra_periodo_emebs(
    escola,
    classificacoes_dieta,
    periodos,
    quantidade_dias_mes,
    ano,
    mes,
    infantil_ou_fundamental,
):
    quantidade = 2
    for periodo in periodos:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for classificacao in classificacoes_dieta:
            for dia in range(1, quantidade_dias_mes + 1):
                log = LogQuantidadeDietasAutorizadas(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=quantidade,
                    data=datetime.date(ano, mes, dia),
                    classificacao=classificacao,
                    infantil_ou_fundamental=infantil_ou_fundamental,
                )
                log.save()
            print(
                f"Logs da dieta {classificacao.nome} do {infantil_ou_fundamental} para o Período {periodo}  cadastrados"
            )


def incluir_dietas_especiais_cei(
    escola, ano, mes, quantidade_dias_mes, periodos_escolares
):
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for periodo in periodos_escolares:
        for classificacao in classificacoes_dieta:
            quantidade = 1 if "Tipo A" in classificacao.nome else 2
            for faixa in faixas:
                for dia in range(1, quantidade_dias_mes + 1):
                    log = LogQuantidadeDietasAutorizadasCEI(
                        escola=escola,
                        periodo_escolar=periodo,
                        quantidade=quantidade,
                        data=datetime.date(ano, mes, dia),
                        classificacao=classificacao,
                        faixa_etaria=faixa,
                    )
                    log.save()
                print(
                    f"Logs dieta {classificacao.nome} para faixa {faixa.__str__()} no Período {periodo} cadastrados"
                )


def incluir_dietas_especiais_cemei(
    escola, ano, mes, quantidade_dias_mes, periodos_escolares
):
    classificacoes_dieta = ClassificacaoDieta.objects.all().order_by("nome")
    cadastra_cei_da_cemei(
        escola,
        ano,
        mes,
        quantidade_dias_mes,
        classificacoes_dieta,
        periodos_escolares["CEI"],
    )
    cadastra_emei_da_cemei(
        escola,
        ano,
        mes,
        quantidade_dias_mes,
        classificacoes_dieta,
        periodos_escolares["EMEI"],
    )


def cadastra_cei_da_cemei(
    escola, ano, mes, quantidade_dias_mes, classificacoes_dieta, periodos_cei_cemei
):
    faixas = FaixaEtaria.objects.filter(ativo=True)
    for periodo in periodos_cei_cemei:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for classificacao in classificacoes_dieta:
            quantidade = 1 if "Tipo A" in classificacao.nome else 2
            for faixa in faixas:
                for dia in range(1, quantidade_dias_mes + 1):
                    log = LogQuantidadeDietasAutorizadasCEI(
                        escola=escola,
                        periodo_escolar=pe,
                        quantidade=quantidade,
                        data=datetime.date(ano, mes, dia),
                        classificacao=classificacao,
                        faixa_etaria=faixa,
                    )
                    log.save()
                print(
                    f"Logs dieta {classificacao.nome} para faixa {faixa.__str__()} no Período {periodo} cadastrados"
                )


def cadastra_emei_da_cemei(
    escola, ano, mes, quantidade_dias_mes, classificacoes_dieta, periodos_emei_cemei
):
    for periodo in periodos_emei_cemei:
        pe = PeriodoEscolar.objects.get(nome=periodo)
        for classificacao in classificacoes_dieta:
            quantidade = 1 if "Tipo A" in classificacao.nome else 2
            for dia in range(1, quantidade_dias_mes + 1):
                log = LogQuantidadeDietasAutorizadas(
                    escola=escola,
                    periodo_escolar=pe,
                    quantidade=quantidade,
                    data=datetime.date(ano, mes, dia),
                    classificacao=classificacao,
                    cei_ou_emei="EMEI",
                )
                log.save()
            print(
                f"Logs da dieta {classificacao.nome} para o Período {periodo} cadastrados"
            )
