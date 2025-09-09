from django.conf import settings
from django.core.management import BaseCommand

from sme_sigpae_api.escola.models import Escola
from utility.carga_dados.medicao.constantes import ANO, MES
from utility.carga_dados.medicao.insere_informacoes_lancamento_inicial import (
    habilitar_dias_letivos,
    incluir_etec,
    incluir_log_alunos_matriculados,
    incluir_log_alunos_matriculados_cei,
    incluir_log_alunos_matriculados_cei_da_cemei,
    incluir_log_alunos_matriculados_emebs,
    incluir_log_alunos_matriculados_emei_da_cemei,
    incluir_programas_e_projetos,
    obter_escolas,
    obter_usuario,
    solicitar_kit_lanche,
    solicitar_kit_lanche_cemei,
    solicitar_lanche_emergencial,
    solicitar_lanche_emergencial_cemei,
)


class Command(BaseCommand):
    help = "Habilita a tela de lançamento de Medição Inicial"

    def handle(self, *args, **options):
        if settings.DEBUG:
            self.stdout.write(
                "================== INICIANDO O SCRIPT =================="
            )
            self.stdout.write("Obtendo a lista de escolas")
            dados_escolas = obter_escolas()

            self.stdout.write("Habilitando dias letivos")
            # nome_escolas = [dado.get("nome_escola") for dado in dados_escolas]
            # habilitar_dias_letivos(escolas=nome_escolas)

            for dados in dados_escolas:
                escola = Escola.objects.get(nome=dados["nome_escola"])
                username = dados["username"]
                usuario_escola = dados["usuario_escola"]
                periodos = dados["periodos"]

                self.stdout.write(
                    f"Incluindo dados para a escola {escola.nome} em {MES}/{ANO}"
                )
                if escola.eh_cemei:
                    self.escolas_cemei(escola, username, usuario_escola, periodos)
                elif escola.eh_cei:
                    self.escolas_cei(escola, username, usuario_escola, periodos)
                else:
                    self.escolas_periodos_normais(
                        escola, username, usuario_escola, periodos
                    )
                self.stdout.write()

    def escolas_periodos_normais(
        self, escola, username, usuario_escola, periodos_escolares
    ):
        self.stdout.write("1. Inclui Log de Alunos Matriculados por período escolar")
        if escola.eh_emebs:
            incluir_log_alunos_matriculados_emebs(periodos_escolares, escola)
        else:
            incluir_log_alunos_matriculados(periodos_escolares, escola)

        periodos_escolares = escola.periodos_escolares(ano=ANO)
        self.stdout.write(f"2. Obtém dados do usuário {usuario_escola}")
        usuario = obter_usuario(username, usuario_escola)

        self.stdout.write("3. Incluindo as Solicitações de Alimentacao")
        self.stdout.write("3.1. Criar solicitação de KIT LANCHE PASSEIO")
        solicitar_kit_lanche(escola, usuario)
        self.stdout.write("3.2 Criar solicitação de LANCHE EMERGENCIAL")
        periodo_escolar_solicitacoes = periodos_escolares.get(nome="MANHA")
        solicitar_lanche_emergencial(escola, usuario, periodo_escolar_solicitacoes)
        
        self.stdout.write("4. Criar PROGRAMAS E PROJETOS")
        incluir_programas_e_projetos(escola, usuario, periodo_escolar_solicitacoes)
        
        if escola.eh_emef or escola.eh_ceu_gestao:
            self.stdout.write("5. Criar ETEC")
            periodo_noturno = periodos_escolares.get(nome="NOITE")
            incluir_etec(escola, usuario, periodo_noturno)
       

    def escolas_cemei(self, escola, username, usuario_escola, periodos_escolares):
        self.stdout.write(
            "1. Inclui Log de Alunos Matriculados por período escolar e faixa etária"
        )
        self.stdout.write("1.1. Por faixa etária")
        incluir_log_alunos_matriculados_cei_da_cemei(periodos_escolares, escola)
        self.stdout.write("1.2. Por período escolar")
        incluir_log_alunos_matriculados_emei_da_cemei(periodos_escolares, escola)
        periodos_escolares = escola.periodos_escolares(ano=ANO)

        self.stdout.write(f"2. Obtém dados do usuário {usuario_escola}")
        usuario = obter_usuario(username, usuario_escola)

        print("3. Incluindo as solicitações de alimentacao")
        self.stdout.write("3.1. Criar solicitação de KIT LANCHE PASSEIO")
        solicitar_kit_lanche_cemei(escola, usuario)
        self.stdout.write("3.2 Criar solicitação de LANCHE EMERGENCIAL")
        periodo_escolar_solicitacoes = periodos_escolares.get(nome="INTEGRAL")
        solicitar_lanche_emergencial_cemei(
            escola, usuario, periodo_escolar_solicitacoes
        )
        
        self.stdout.write("4. Criar PROGRAMAS E PROJETOS")
        incluir_programas_e_projetos(escola, usuario, periodo_escolar_solicitacoes)

    def escolas_cei(self, escola, username, usuario_escola, periodos_escolares):
        self.stdout.write("1. Inclui Log de Alunos Matriculados por faixa etária")
        incluir_log_alunos_matriculados_cei(periodos_escolares, escola)
