import datetime
import logging
import timeit

import environ
import requests
from django.core.management.base import BaseCommand
from requests import ConnectionError
from rest_framework import status

from ....dados_comuns.constants import DJANGO_EOL_SGP_API_TOKEN, DJANGO_EOL_SGP_API_URL
from ...models import (
    Aluno,
    Escola,
    LogAtualizaDadosAluno,
    LogRotinaDiariaAlunos,
    PeriodoEscolar,
)

env = environ.Env()

logger = logging.getLogger("sigpae.cmd_atualiza_alunos_escolas")


class Command(BaseCommand):
    help = "Atualiza os dados de alunos das Escolas baseados na api do SGP"
    headers = {"x-api-eol-key": f"{DJANGO_EOL_SGP_API_TOKEN}"}
    timeout = 10
    contador_alunos = 0
    total_alunos = 0
    status_matricula_ativa = [1, 6, 10, 13]  # status para matrículas ativas
    codigo_turma_regular = 1  # código da turma para matrículas do tipo REGULAR

    def __init__(self):
        """Atualiza os dados de alunos das Escolas baseados na api do SGP."""
        super().__init__()
        lista_tipo_turnos = list(
            PeriodoEscolar.objects.filter(tipo_turno__isnull=False).values_list(
                "tipo_turno", flat=True
            )
        )
        dict_periodos_escolares_por_tipo_turno = {}
        for tipo_turno in lista_tipo_turnos:
            dict_periodos_escolares_por_tipo_turno[
                tipo_turno
            ] = PeriodoEscolar.objects.get(tipo_turno=tipo_turno)
        self.dict_periodos_escolares_por_tipo_turno = (
            dict_periodos_escolares_por_tipo_turno
        )

    def handle(self, *args, **options):
        try:
            tic = timeit.default_timer()

            quantidade_alunos_antes = Aluno.objects.all().count()

            hoje = datetime.date.today()
            ano = hoje.year
            ultimo_dia_setembro = datetime.date(ano, 10, 1) - datetime.timedelta(days=1)

            if hoje > ultimo_dia_setembro:
                self._atualiza_todas_as_escolas_d_menos_2()
            else:
                self._atualiza_todas_as_escolas_d_menos_1()

            quantidade_alunos_atual = Aluno.objects.all().count()

            LogRotinaDiariaAlunos.objects.create(
                quantidade_alunos_antes=quantidade_alunos_antes,
                quantidade_alunos_atual=quantidade_alunos_atual,
            )

            toc = timeit.default_timer()
            result = round(toc - tic, 2)
            if result > 60:
                logger.debug(f"Total time: {round(result // 60, 2)} min")
            else:
                logger.debug(f"Total time: {round(result, 2)} s")

        except MaxRetriesExceeded as e:
            logger.error(str(e))
            self.stdout.write(
                self.style.ERROR("Execution stopped due to repeated failures.")
            )

    def _salva_logs_requisicao(self, response, cod_eol_escola):
        if not response.status_code == status.HTTP_404_NOT_FOUND:
            msg_erro = "" if response.status_code == 200 else response.text
            log_erro = LogAtualizaDadosAluno(
                status=response.status_code,
                codigo_eol=cod_eol_escola,
                criado_em=datetime.date.today(),
                msg_erro=msg_erro,
            )
            log_erro.save()

    def get_response_alunos_por_escola(self, cod_eol_escola, ano_param=None):
        ano = datetime.date.today().year
        return requests.get(
            f"{DJANGO_EOL_SGP_API_URL}/alunos/ues/{cod_eol_escola}/anosLetivos/{ano_param or ano}",
            headers=self.headers,
        )

    def _obtem_alunos_escola(self, cod_eol_escola, ano_param=None):
        tentativas = 0
        max_tentativas = 10

        while tentativas < max_tentativas:
            try:
                response = self.get_response_alunos_por_escola(
                    cod_eol_escola, ano_param
                )
                self._salva_logs_requisicao(response, cod_eol_escola)

                if response.status_code == status.HTTP_200_OK:
                    return response.json()
                elif response.status_code == status.HTTP_404_NOT_FOUND:
                    return []

                tentativas += 1
                logger.warning(
                    f"Tentativa {tentativas}/{max_tentativas} for escola {cod_eol_escola}: Status {response.status_code}"
                )

            except ConnectionError as e:
                tentativas += 1
                msg = f"Erro de conexão na API do EOL para escola {cod_eol_escola}: {e}"
                log_erro = LogAtualizaDadosAluno(
                    status=502,
                    codigo_eol=cod_eol_escola,
                    criado_em=datetime.date.today(),
                    msg_erro=msg,
                )
                log_erro.save()
                logger.error(msg)
                self.stdout.write(self.style.ERROR(msg))

        raise MaxRetriesExceeded(
            f"Máximo de tentativas alcançada para a escola {cod_eol_escola}. Abortado."
        )

    def _monta_obj_aluno(self, registro, escola, data_nascimento):
        obj_aluno = Aluno(
            nome=registro["nomeAluno"].strip(),
            codigo_eol=registro["codigoAluno"],
            data_nascimento=data_nascimento,
            escola=escola,
            serie=registro["turmaNome"],
            periodo_escolar=self.dict_periodos_escolares_por_tipo_turno[
                registro["tipoTurno"]
            ],
            etapa=registro.get("etapaEnsino", None),
            ciclo=registro.get("cicloEnsino", None),
            desc_etapa=registro.get("descEtapaEnsino", ""),
            desc_ciclo=registro.get("descCicloEnsino", ""),
        )
        return obj_aluno

    def _atualiza_aluno(self, aluno, registro, data_nascimento, escola):
        aluno.nome = registro["nomeAluno"].strip()
        aluno.codigo_eol = registro["codigoAluno"]
        aluno.data_nascimento = data_nascimento
        aluno.escola = escola
        aluno.nao_matriculado = False
        aluno.serie = registro["turmaNome"]
        aluno.periodo_escolar = self.dict_periodos_escolares_por_tipo_turno[
            registro["tipoTurno"]
        ]
        aluno.etapa = registro.get("etapaEnsino", None)
        aluno.ciclo = registro.get("cicloEnsino", None)
        aluno.desc_etapa = registro.get("descEtapaEnsino", "")
        aluno.desc_ciclo = registro.get("descCicloEnsino", "")

    def get_todos_os_registros(self):
        escolas = Escola.objects.prefetch_related("aluno_set")
        proximo_ano = datetime.date.today().year + 1

        todos_os_registros = []
        total = escolas.count()
        for i, escola in enumerate(escolas):
            if (i + 1) % 10 == 0:
                logger.debug(f"{i + 1}/{total} - {escola}")
            dados_alunos_escola = self._processa_dados_alunos(
                self._obtem_alunos_escola(escola.codigo_eol), escola
            )
            dados_alunos_escola_prox_ano = self._processa_dados_alunos(
                self._obtem_alunos_escola(escola.codigo_eol, proximo_ano), escola
            )
            todos_os_registros.extend(dados_alunos_escola)
            todos_os_registros.extend(dados_alunos_escola_prox_ano)

        todos_os_registros.sort(key=lambda x: (x["codigoAluno"], x["anoLetivo"]))
        return todos_os_registros

    def _processa_dados_alunos(self, dados_alunos, escola):
        if dados_alunos and isinstance(dados_alunos, list):
            for dado in dados_alunos:
                dado["codigoEolEscola"] = escola.codigo_eol
            return dados_alunos
        return []

    def _atualiza_todas_as_escolas_d_menos_2(self):
        todos_os_registros = self.get_todos_os_registros()
        self.total_alunos += len(todos_os_registros)
        alunos_ativos = set()
        novos_alunos = {}
        alunos_para_atualizar = []
        registros_alunos_novos = {}

        for registro in todos_os_registros:
            self.contador_alunos += 1
            if self.contador_alunos % 10 == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{self.contador_alunos} DE UM TOTAL DE {self.total_alunos} MATRICULAS"
                    )
                )
            if registro["codigoAluno"] in alunos_ativos:
                continue
            if registro["codigoTipoTurma"] != self.codigo_turma_regular:
                continue

            escola = Escola.objects.get(codigo_eol=registro["codigoEolEscola"])
            self._trata_alunos_status_ativo_d_menos_2(
                registro,
                alunos_ativos,
                alunos_para_atualizar,
                novos_alunos,
                registros_alunos_novos,
                escola,
            )
            self._trata_alunos_status_NAO_ativo_d_menos_2(registro, escola)

        self.stdout.write(self.style.SUCCESS("criando alunos... aguarde..."))
        Aluno.objects.bulk_create(novos_alunos.values())
        self.stdout.write(self.style.SUCCESS("atualizando alunos... aguarde..."))
        self._atualiza_alunos(alunos_para_atualizar)
        self.stdout.write(self.style.SUCCESS("desvinculando alunos... aguarde..."))
        self.stdout.write(
            self.style.SUCCESS("Criando histórico de matrículas... aguarde...")
        )
        self._lida_com_matricula_alunos_novos(novos_alunos, registros_alunos_novos)

    def _trata_alunos_status_ativo_d_menos_2(
        self,
        registro,
        alunos_ativos,
        alunos_para_atualizar,
        novos_alunos,
        registros_alunos_novos,
        escola,
    ):
        if registro["codigoSituacaoMatricula"] in self.status_matricula_ativa:
            alunos_ativos.add(registro["codigoAluno"])
            aluno = Aluno.objects.filter(codigo_eol=registro["codigoAluno"]).first()
            data_nascimento = registro["dataNascimento"].split("T")[0]
            if aluno:
                self._atualiza_aluno(aluno, registro, data_nascimento, escola)
                alunos_para_atualizar.append(aluno)
                self._lida_com_matricula_aluno_existente(aluno, registro)
            else:
                novos_alunos[registro["codigoAluno"]] = self._monta_obj_aluno(
                    registro, escola, data_nascimento
                )
                registros_alunos_novos[registro["codigoAluno"]] = registro

    def _trata_alunos_status_NAO_ativo_d_menos_2(self, registro, escola):
        if registro["codigoSituacaoMatricula"] not in self.status_matricula_ativa:
            aluno = Aluno.objects.filter(codigo_eol=registro["codigoAluno"]).first()
            if aluno:
                self._lida_com_matricula_aluno_existente_outra_escola(
                    aluno, registro, escola
                )

    def _desvincular_matriculas(self, alunos):
        alunos.update(nao_matriculado=True, escola=None)

    def aluno_matriculado_prox_ano(self, dados, aluno_nome):
        aluno_encontrado = next(
            (aluno for aluno in dados if aluno["nomeAluno"] == aluno_nome), None
        )
        return (
            aluno_encontrado
            and aluno_encontrado["codigoSituacaoMatricula"]
            in self.status_matricula_ativa
        )

    def _atualiza_alunos_da_escola(
        self, escola, dados_alunos_escola, dados_alunos_escola_prox_ano
    ):
        novos_alunos = {}
        registros_alunos_novos = {}
        self.total_alunos += len(dados_alunos_escola)
        codigos_consultados = []
        alunos_para_atualizar = []
        for registro in dados_alunos_escola:
            self.contador_alunos += 1
            if self.contador_alunos % 10 == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"{self.contador_alunos} DE UM TOTAL DE {self.total_alunos} MATRICULAS"
                    )
                )
            if registro["codigoTipoTurma"] != self.codigo_turma_regular:
                continue
            self._trata_aluno_status_ativo(
                registro,
                escola,
                dados_alunos_escola_prox_ano,
                codigos_consultados,
                alunos_para_atualizar,
                novos_alunos,
                registros_alunos_novos,
            )
            self._trata_alunos_status_NAO_ativo(
                registro, escola, dados_alunos_escola_prox_ano
            )

        alunos_nao_consultados = Aluno.objects.filter(escola=escola).exclude(
            codigo_eol__in=codigos_consultados
        )
        self._desvincular_matriculas(alunos_nao_consultados)
        Aluno.objects.bulk_create(novos_alunos.values())
        self.stdout.write(self.style.SUCCESS("atualizando alunos... aguarde..."))
        self._atualiza_alunos(alunos_para_atualizar)
        self.stdout.write(
            self.style.SUCCESS("Criando histórico de matrículas... aguarde...")
        )
        self._lida_com_matricula_alunos_novos(novos_alunos, registros_alunos_novos)

    def _trata_aluno_status_ativo(
        self,
        registro,
        escola,
        dados_alunos_escola_prox_ano,
        codigos_consultados,
        alunos_para_atualizar,
        novos_alunos,
        registros_alunos_novos,
    ):
        if registro[
            "codigoSituacaoMatricula"
        ] in self.status_matricula_ativa or self.aluno_matriculado_prox_ano(
            dados_alunos_escola_prox_ano, registro["nomeAluno"]
        ):
            codigos_consultados.append(registro["codigoAluno"])
            aluno = Aluno.objects.filter(codigo_eol=registro["codigoAluno"]).first()
            data_nascimento = registro["dataNascimento"].split("T")[0]
            if aluno:
                self._atualiza_aluno(aluno, registro, data_nascimento, escola)
                alunos_para_atualizar.append(aluno)
                self._lida_com_matricula_aluno_existente(aluno, registro)
            else:
                novos_alunos[registro["codigoAluno"]] = self._monta_obj_aluno(
                    registro, escola, data_nascimento
                )
                registros_alunos_novos[registro["codigoAluno"]] = registro

    def _trata_alunos_status_NAO_ativo(
        self, registro, escola, dados_alunos_escola_prox_ano
    ):
        if not (
            registro["codigoSituacaoMatricula"] in self.status_matricula_ativa
            or self.aluno_matriculado_prox_ano(
                dados_alunos_escola_prox_ano, registro["nomeAluno"]
            )
        ):
            aluno = Aluno.objects.filter(codigo_eol=registro["codigoAluno"]).first()
            if aluno:
                self._lida_com_matricula_aluno_existente_outra_escola(
                    aluno, registro, escola
                )

    def _atualiza_todas_as_escolas_d_menos_1(self):
        escolas = Escola.objects.prefetch_related("aluno_set")
        proximo_ano = datetime.date.today().year + 1

        total = escolas.count()
        for i, escola in enumerate(escolas):
            logger.debug(f"{i+1}/{total} - {escola}")
            dados_alunos_escola = self._obtem_alunos_escola(escola.codigo_eol)
            dados_alunos_escola_prox_ano = self._obtem_alunos_escola(
                escola.codigo_eol, proximo_ano
            )
            if (
                dados_alunos_escola
                and type(dados_alunos_escola) is list
                and len(dados_alunos_escola) > 0
            ):
                self._atualiza_alunos_da_escola(
                    escola, dados_alunos_escola, dados_alunos_escola_prox_ano
                )

    def _lida_com_matricula_aluno_existente(self, aluno: Aluno, registro: dict):
        codigo_situacao = registro["codigoSituacaoMatricula"]
        situacao = registro["situacaoMatricula"]

        if not aluno.historico.exists():
            aluno.cria_historico(codigo_situacao, situacao)
            return

        if not aluno.historico.filter(escola=aluno.escola).exists():
            aluno.cria_historico(codigo_situacao, situacao)

        if codigo_situacao not in self.status_matricula_ativa:
            aluno.historico.filter(escola=aluno.escola).update(
                data_fim=datetime.date.today(),
                codigo_situacao=codigo_situacao,
                situacao=situacao,
            )

    def _lida_com_matricula_alunos_novos(
        self, dict_alunos: dict[Aluno], registros_alunos_novos: dict
    ):
        for codigo_eol, aluno in dict_alunos.items():
            codigo_situacao = registros_alunos_novos[aluno.codigo_eol][
                "codigoSituacaoMatricula"
            ]
            situacao = registros_alunos_novos[aluno.codigo_eol]["situacaoMatricula"]
            aluno_obj = Aluno.objects.get(codigo_eol=aluno.codigo_eol)
            aluno_obj.cria_historico(codigo_situacao, situacao)

    def _lida_com_matricula_aluno_existente_outra_escola(
        self, aluno: Aluno, registro: dict, escola: Escola
    ):
        codigo_situacao = registro["codigoSituacaoMatricula"]
        situacao = registro["situacaoMatricula"]

        if not aluno.historico.filter(escola=escola).exists():
            aluno.cria_historico(codigo_situacao, situacao, escola)

        if aluno.historico.filter(escola=escola, data_fim=None).exists():
            aluno.historico.filter(escola=escola).update(
                data_fim=datetime.date.today(),
                codigo_situacao=codigo_situacao,
                situacao=situacao,
            )

    def _atualiza_alunos(self, lista_alunos: list[Aluno]):
        fields_to_update = [
            "nome",
            "codigo_eol",
            "data_nascimento",
            "escola",
            "periodo_escolar",
            "cpf",
            "nao_matriculado",
            "serie",
            "etapa",
            "ciclo",
            "desc_etapa",
            "desc_ciclo",
        ]
        Aluno.objects.bulk_update(lista_alunos, fields=fields_to_update)


class MaxRetriesExceeded(Exception):
    pass
