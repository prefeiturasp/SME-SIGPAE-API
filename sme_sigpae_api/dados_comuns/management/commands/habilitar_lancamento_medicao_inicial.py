import calendar
import datetime

import environ
from django.core.management import BaseCommand, CommandError

from sme_sigpae_api.escola.models import Escola
from utility.carga_dados.medicao.insere_informacoes_lancamento_inicial import (
    habilitar_dias_letivos,
    incluir_etec,
    incluir_log_alunos_matriculados,
    incluir_log_alunos_matriculados_cei,
    incluir_log_alunos_matriculados_cei_da_cemei,
    incluir_log_alunos_matriculados_emebs,
    incluir_log_alunos_matriculados_emei_da_cemei,
    incluir_programas_e_projetos,
    incluir_solicitacoes_ceu_gestao,
    obter_escolas,
    obter_usuario,
    solicitar_kit_lanche,
    solicitar_kit_lanche_cemei,
    solicitar_lanche_emergencial,
    solicitar_lanche_emergencial_cemei,
    verifica_dados_iniciais,
)

env = environ.Env()


class Command(BaseCommand):
    help = "Habilita a tela de lançamento de Medição Inicial"

    def add_arguments(self, parser):
        parser.add_argument(
            "--ano", type=int, help="Ano obrigatório para a medição", required=True
        )
        parser.add_argument(
            "--mes", type=int, help="Mês obrigatório para a medição", required=True
        )
        parser.add_argument(
            "--data-kit-lanche",
            type=int,
            help="Dia para data_kit_lanche (padrão: 15)",
            default=15,
        )
        parser.add_argument(
            "--data-lanche-emergencial",
            type=int,
            help="Dia para data_lanche_emergencial (padrão: 22)",
            default=22,
        )

    def handle(self, *args, **options):
        if env("DJANGO_ENV") == "production":
            self.stdout.write(self.style.ERROR("SÓ PODE EXECUTAR EM DESENVOLVIMENTO"))
            return
        ano, mes, dia_kit_lanche, dia_lanche_emergencial = self.parse_parametros(
            options
        )
        self.valida_parametros(ano, mes, dia_kit_lanche, dia_lanche_emergencial)

        self.stdout.write("================== INICIANDO O SCRIPT ==================")
        self.stdout.write("Obtendo a lista de escolas")
        dados_escolas = obter_escolas()

        self.stdout.write("\nVerificando os dados iniciais")
        verifica_dados_iniciais()

        # call_command("migrate", interactive=False)

        self.stdout.write("\nHabilitando dias letivos")
        nome_escolas = [dado.get("nome_escola") for dado in dados_escolas]
        data = datetime.date(ano, mes, 1)
        habilitar_dias_letivos(nome_escolas, data)

        quantidade_dias_mes = calendar.monthrange(int(ano), int(mes))[1]
        for dados in dados_escolas:
            escola = Escola.objects.get(nome=dados["nome_escola"])
            email_escola = dados["email"]
            periodos = dados["periodos"]
            email_dre = dados["usuario_dre"]
            self.stdout.write(
                f"\nIncluindo dados para a escola {escola.nome} em {mes}/{ano}"
            )
            if escola.eh_cemei:
                self.escolas_cemei(
                    escola,
                    email_escola,
                    periodos,
                    ano,
                    mes,
                    quantidade_dias_mes,
                    dia_kit_lanche,
                    dia_lanche_emergencial,
                    email_dre,
                )
            elif escola.eh_cei:
                self.escolas_cei(
                    escola,
                    periodos,
                    ano,
                    mes,
                    quantidade_dias_mes,
                )
            else:
                self.escolas_periodos_normais(
                    escola,
                    email_escola,
                    periodos,
                    ano,
                    mes,
                    quantidade_dias_mes,
                    dia_kit_lanche,
                    dia_lanche_emergencial,
                    email_dre,
                )
            self.stdout.write()

        self.stdout.write("================== FINALIZADO ==================")

    def parse_parametros(self, options):
        ano = options["ano"]
        mes = options["mes"]
        dia_kit = options.get("data_kit_lanche")
        dia_emergencial = options.get("data_lanche_emergencial")
        return ano, mes, dia_kit, dia_emergencial

    def valida_parametros(self, ano, mes, dia_kit, dia_emergencial):
        if mes < 1 or mes > 12:
            raise CommandError("Mês deve estar entre 1 e 12")
        dias_no_mes = calendar.monthrange(ano, mes)[1]

        if not 1 <= dia_kit <= dias_no_mes:
            raise CommandError(
                f"Dia do kit lanche deve estar entre 1 e {dias_no_mes} para {mes:02d}/{ano}"
            )

        if not 1 <= dia_emergencial <= dias_no_mes:
            raise CommandError(
                f"Dia do lanche emergencial deve estar entre 1 e {dias_no_mes} para {mes:02d}/{ano}"
            )

    def escolas_periodos_normais(
        self,
        escola,
        email_escola,
        periodos_escolares,
        ano,
        mes,
        quantidade_dias_mes,
        dia_kit_lanche,
        dia_lanche_emergencial,
        email_dre,
    ):
        self.stdout.write("1. Inclui Log de Alunos Matriculados por período escolar")
        if escola.eh_emebs:
            incluir_log_alunos_matriculados_emebs(
                periodos_escolares, escola, ano, mes, quantidade_dias_mes
            )
        else:
            incluir_log_alunos_matriculados(
                periodos_escolares, escola, ano, mes, quantidade_dias_mes
            )

        periodos_escolares = escola.periodos_escolares(ano=ano)
        self.stdout.write("2. Obtém dados do usuário")
        usuario = obter_usuario(email_escola)
        usuario_dre = obter_usuario(email_dre)

        self.stdout.write("3. Incluindo as Solicitações de Alimentacao")
        self.stdout.write("3.1. Criar solicitação de KIT LANCHE PASSEIO")
        solicitar_kit_lanche(escola, usuario, ano, mes, dia_kit_lanche, usuario_dre)
        self.stdout.write("3.2 Criar solicitação de LANCHE EMERGENCIAL")
        periodo_escolar_solicitacoes = periodos_escolares.get(nome="MANHA")
        solicitar_lanche_emergencial(
            escola,
            usuario,
            periodo_escolar_solicitacoes,
            ano,
            mes,
            dia_lanche_emergencial,
            usuario_dre,
        )

        self.stdout.write("4. Criar PROGRAMAS E PROJETOS")
        incluir_programas_e_projetos(
            escola,
            usuario,
            periodo_escolar_solicitacoes,
            ano,
            mes,
            dia_kit_lanche,
            usuario_dre,
        )

        if escola.eh_emef or escola.eh_ceu_gestao:
            self.stdout.write("5. Criar ETEC")
            periodo_noturno = periodos_escolares.get(nome="NOITE")
            incluir_etec(
                escola,
                usuario,
                periodo_noturno,
                ano,
                mes,
                dia_lanche_emergencial,
                usuario_dre,
            )

        if escola.eh_ceu_gestao:
            self.stdout.write("6. Cadastro específo para CEU GESTAO")
            incluir_solicitacoes_ceu_gestao(
                escola,
                usuario,
                periodos_escolares,
                ano,
                mes,
                dia_kit_lanche,
                usuario_dre,
            )

    def escolas_cemei(
        self,
        escola,
        email_escola,
        periodos_escolares,
        ano,
        mes,
        quantidade_dias_mes,
        dia_kit_lanche,
        dia_lanche_emergencial,
        email_dre,
    ):
        self.stdout.write(
            "1. Inclui Log de Alunos Matriculados por período escolar e faixa etária"
        )
        self.stdout.write("1.1. Por faixa etária")
        incluir_log_alunos_matriculados_cei_da_cemei(
            periodos_escolares, escola, ano, mes, quantidade_dias_mes
        )
        self.stdout.write("1.2. Por período escolar")
        incluir_log_alunos_matriculados_emei_da_cemei(
            periodos_escolares, escola, ano, mes, quantidade_dias_mes
        )
        periodos_escolares = escola.periodos_escolares(ano=ano)

        self.stdout.write("2. Obtém dados do usuário")
        usuario = obter_usuario(email_escola)
        usuario_dre = obter_usuario(email_dre)

        print("3. Incluindo as solicitações de alimentacao")
        self.stdout.write("3.1. Criar solicitação de KIT LANCHE PASSEIO")
        solicitar_kit_lanche_cemei(
            escola, usuario, ano, mes, dia_kit_lanche, usuario_dre
        )
        self.stdout.write("3.2 Criar solicitação de LANCHE EMERGENCIAL")
        periodo_escolar_solicitacoes = periodos_escolares.get(nome="INTEGRAL")
        solicitar_lanche_emergencial_cemei(
            escola,
            usuario,
            periodo_escolar_solicitacoes,
            ano,
            mes,
            dia_lanche_emergencial,
            usuario_dre,
        )

        self.stdout.write("4. Criar PROGRAMAS E PROJETOS")
        incluir_programas_e_projetos(
            escola,
            usuario,
            periodo_escolar_solicitacoes,
            ano,
            mes,
            dia_kit_lanche,
            usuario_dre,
        )

    def escolas_cei(
        self,
        escola,
        periodos_escolares,
        ano,
        mes,
        quantidade_dias_mes,
    ):
        self.stdout.write("1. Inclui Log de Alunos Matriculados por faixa etária")
        incluir_log_alunos_matriculados_cei(
            periodos_escolares, escola, ano, mes, quantidade_dias_mes
        )
