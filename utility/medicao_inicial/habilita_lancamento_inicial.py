import os
import django
import datetime
from dateutil.relativedelta import relativedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()


ANO = 2024
MES = 10
DIAS_MES = 31
QUANTIDADE_ALUNOS = 25


def habilitar_dias_letivos(data=None):
    from sme_sigpae_api.escola.utils import calendario_sgp
    print("Habilitando dias letivos...")
    if not data:
        data = datetime.date(ANO, MES, 1)
    calendario_sgp(data)
    print(f"O mês referente a data {data.strftime("%d/%m%Y")} agora é letivo")

    data_kit_lanche = data_solicitacao_kit_lanche()
    calendario_sgp(data_kit_lanche)
    print(f"A data do pedido de kit lanche {data_kit_lanche.strftime("%d/%m%Y")} agora é letivo")

    data_lanche_emergencial = data_solicitacao_kit_lanche()
    calendario_sgp(data_lanche_emergencial)
    print(f"A data do pedido do lanche emergencial {data_kit_lanche.strftime("%d/%m%Y")} agora é letivo")


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


def obter_usuario(username, nome):
    from sme_sigpae_api.perfil.models.usuario import Usuario
    try:
        return Usuario.objects.get(username=username, nome=nome)
    except Exception:
        print(f"Nenhum usuário encontrado com  username={username} e nome={nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()


def data_solicitacao_kit_lanche():
    data = datetime.datetime.now() + relativedelta(months=1)
    return data.date()


def solicitar_kit_lanche(escola, usuario):
    "TIPOS DE UNIDADE: EMEI, EMEF"
    from sme_sigpae_api.kit_lanche.models import KitLanche
    from sme_sigpae_api.kit_lanche.api.serializers.serializers_create import SolicitacaoKitLancheAvulsaCreationSerializer
    
    queryset = KitLanche.objects.filter(edital__uuid__in=escola.editais, tipos_unidades=escola.tipo_unidade, status=KitLanche.ATIVO)
    if not queryset.exists():
        print(f"Nenhum kit encontrado para escola {escola.nome}")
        print("================== SCRIP CANCELADO ==================")
        exit()
    kit = queryset.first()
    solicitacao_json = {
        "solicitacao_kit_lanche": {
            "kits": [kit],
            "data": data_solicitacao_kit_lanche(),
            "tempo_passeio": "0"
        },
        "escola": escola,
        "local": "Casa da História",
        "evento": "Semana da História",
        "quantidade_alunos": 10,
        "alunos_com_dieta_especial_participantes": [],
        "status": "RASCUNHO"
    }
    context = {
        "request": type(
            "Request", (), {"user": usuario}
        )
    }
    solicitacao_kit_lanche_avulsa = SolicitacaoKitLancheAvulsaCreationSerializer(context=context).create(
        solicitacao_json
    )
    solicitacao_kit_lanche_avulsa.inicia_fluxo(user=usuario)
    print(f"Solicitação cadastrada: SolicitacaoKitLancheAvulsa UUID={solicitacao_kit_lanche_avulsa.uuid}")
    
    usuario_dre = obter_usuario(26755818011, "DRE ADMIN")
    solicitacao_kit_lanche_avulsa.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")
    
    usuario_codae = obter_usuario("01341145409", "CODAE ADMIN")
    solicitacao_kit_lanche_avulsa.codae_autoriza(user=usuario_codae, justificativa="Sem observações por parte da CODAE")
    print("Solicitação aprovado pela CODAE")
    
    dia_passeio = datetime.date(ANO, MES, 15)
    solicitacao_kit_lanche = solicitacao_kit_lanche_avulsa.solicitacao_kit_lanche
    solicitacao_kit_lanche.data = dia_passeio
    solicitacao_kit_lanche.save()
    print(f"Data da solicitação alterada para {dia_passeio.strftime('%d/%m/%Y')}")
    
    return solicitacao_kit_lanche


def data_solicitacao_kit_emergencial():
    data = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data.date()


def solicitar_lanche_emergencial(escola, usuario, periodo_escolar):
    from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.models import MotivoAlteracaoCardapio
    from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
    from sme_sigpae_api.cardapio.alteracao_tipo_alimentacao.api.serializers_create import AlteracaoCardapioSerializerCreate
  
    data = data_solicitacao_kit_emergencial()
    motivo = MotivoAlteracaoCardapio.objects.get(nome="Lanche Emergencial")
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    tipo_lanche_emergencial = TipoAlimentacao.objects.get(nome="Lanche Emergencial")
    
    solicitacao_json = {
        "escola": escola,
        "motivo": motivo,
        "observacao": "<p>Devido as chuvas, haverá corte de energia elétrica para manutenção da rede</p>",
        "data_inicial": data,
        "data_final": data,
        "datas_intervalo": [
            {
                "data": data
            }
        ],
        "substituicoes": [
            {
                "qtd_alunos": "5",
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao_de": [tipo_alimentacao],
                "tipos_alimentacao_para": [tipo_lanche_emergencial]
            }
        ],

    }
    context = {
        "request": type(
            "Request", (), {"user": usuario}
        )
    }
    solicitacao_lanche_emergencial = AlteracaoCardapioSerializerCreate(context=context).create(
        solicitacao_json
    )

    solicitacao_lanche_emergencial.inicia_fluxo(user=usuario)
    print(f"Solicitação cadastrada: AlteracaoCardapio UUID={solicitacao_lanche_emergencial.uuid}")
    
    usuario_dre = obter_usuario(26755818011, "DRE ADMIN")
    solicitacao_lanche_emergencial.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")
    
    usuario_codae = obter_usuario("01341145409", "CODAE ADMIN")
    solicitacao_lanche_emergencial.codae_autoriza(user=usuario_codae, justificativa="Sem observações por parte da CODAE")
    print("Solicitação aprovado pela CODAE")
    
    dia_lanche_emergencial = datetime.date(ANO, MES, 22)
    solicitacao_lanche_emergencial.data_final = dia_lanche_emergencial
    solicitacao_lanche_emergencial.data_inicial = dia_lanche_emergencial
    solicitacao_lanche_emergencial.save()
    
    data_intervalo = solicitacao_lanche_emergencial.datas_intervalo.get()
    data_intervalo.data = dia_lanche_emergencial
    data_intervalo.save()
    
    print(f"Data da solicitação alterada para {dia_lanche_emergencial.strftime('%d/%m/%Y')}")
    
    return solicitacao_lanche_emergencial


def data_programas_e_projetos():
    data_inicial = datetime.datetime.now() + relativedelta(months=1)
    data_final = datetime.datetime.now() + relativedelta(months=1, days=5)
    return data_inicial.date(), data_final.date()


def incluir_programas_e_projetos(escola, usuario, periodo_escolar):
    from sme_sigpae_api.cardapio.base.models import TipoAlimentacao
    from sme_sigpae_api.inclusao_alimentacao.models import MotivoInclusaoContinua
    from sme_sigpae_api.inclusao_alimentacao.api.serializers.serializers_create import InclusaoAlimentacaoContinuaCreationSerializer

    data_inicial, data_final = data_programas_e_projetos()
    tipo_alimentacao = TipoAlimentacao.objects.get(nome="Lanche 4h")
    motivo = MotivoInclusaoContinua.objects.get(nome="Programas/Projetos Específicos")    
    
    solicitacao_json = {
        "escola": escola,
        "status": "RASCUNHO",
        "quantidades_periodo": [
            {
                "dias_semana": [
                    "0",
                    "1",
                    "2",
                    "3",
                    "4"
                ],
                "periodo_escolar": periodo_escolar,
                "tipos_alimentacao": [
                    tipo_alimentacao
                ],
                "numero_alunos": "10",
                "observacao": "<p>nenhuma</p>"
            }
        ],
        "motivo": motivo,
        "data_inicial": data_inicial,
        "data_final": data_final
    }
    context = {
        "request": type(
            "Request", (), {"user": usuario}
        )
    }
    programas_e_projetos = InclusaoAlimentacaoContinuaCreationSerializer(context=context).create(
        solicitacao_json
    )
    programas_e_projetos.inicia_fluxo(user=usuario)
    print(f"Solicitação cadastrada: InclusaoAlimentacaoContinua UUID={programas_e_projetos.uuid}")
    
    usuario_dre = obter_usuario(26755818011, "DRE ADMIN")
    programas_e_projetos.dre_valida(user=usuario_dre)
    print("Solicitação aprovado pela DRE")
    
    usuario_codae = obter_usuario("01341145409", "CODAE ADMIN")
    programas_e_projetos.codae_autoriza(user=usuario_codae, justificativa="Sem observações por parte da CODAE")
    print("Solicitação aprovado pela CODAE")
    
    nova_data_inicio = datetime.date(ANO, MES, 22)
    nova_data_fim = datetime.date(ANO, MES, 22) + relativedelta(days=5)
    programas_e_projetos.data_final = nova_data_fim
    programas_e_projetos.data_inicial = nova_data_inicio
    programas_e_projetos.save()
    
    print(f"Data da solicitação alterada para {nova_data_inicio.strftime('%d/%m/%Y')} até {nova_data_fim.strftime('%d/%m/%Y')}")

if __name__ == "__main__":
    habilitar_dias_letivos()