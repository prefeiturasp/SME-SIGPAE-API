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


def habilitar_dias_letivos():
    from sme_sigpae_api.escola.utils import calendario_sgp
    d = datetime.date(ANO, MES, 1)
    calendario_sgp(d)


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
    habilitar_dias_letivos(data.date())
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

if __name__ == "__main__":
    habilitar_dias_letivos()