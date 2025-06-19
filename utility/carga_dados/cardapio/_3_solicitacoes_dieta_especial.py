"""
Antes de rodar isso vc deve ter rodado as escolas e as fixtures e associar usuarios as instituicoes
"""

import datetime
import random
import string

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from faker import Faker

from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    Anexo,
    ClassificacaoDieta,
    MotivoNegacao,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
)
from sme_sigpae_api.escola.models import Aluno, Escola
from sme_sigpae_api.perfil.models import Usuario

f = Faker("pt-br")
f.seed(420)


def fluxo_escola_felix_dieta_especial(obj, user, index):  # noqa: C901
    obj.inicia_fluxo(user=user, notificar=True)
    jogada_de_dado = random.randint(1, 5)
    if jogada_de_dado == 1:
        pass  # Mantém a solicitação em status "aguardando autorização"
    elif jogada_de_dado == 2:
        obj.cancelar_pedido(user=user, justificativa="")
    else:
        obj.registro_funcional_nutricionista = (
            f"Elaborado por {f.name()} - CRN {random.randint(10000000, 99999999)}"
        )
        if jogada_de_dado == 3:
            obj.motivo_negacao = _get_random_motivo_negacao()
            obj.justificativa_negacao = f.text()[:50]
            obj.codae_nega(user=user, notificar=True)
        else:
            obj.codae_autoriza(user=user, notificar=True)
            obj.nome_protocolo = f.text()[:25]
            obj.informacoes_adicionais = f.text()[:100]
            obj.classificacao = _get_random_classificacao_de_dieta()
            obj.ativo = True if random.randint(0, 1) == 1 else False
            for _ in range(random.randint(1, 3)):
                obj.alergias_intolerancias.add(_get_random_alergia())
            for _ in range(random.randint(1, 3)):
                subst = SubstituicaoAlimento.objects.create(
                    solicitacao_dieta_especial=obj,
                    alimento=_get_random_alimento(),
                    tipo="I" if random.randint(0, 1) == 1 else "S",
                )
                for __ in range(random.randint(1, 5)):
                    subst.substitutos.add(_get_random_alimento())
            if jogada_de_dado == 5:
                obj.terceirizada_toma_ciencia(user=user, notificar=True)
            obj.save()


def _get_random_from_queryset(qs):
    return qs[random.randint(0, len(qs) - 1)]


classificacoes_dieta = ClassificacaoDieta.objects.all()


def _get_random_classificacao_de_dieta():
    return _get_random_from_queryset(classificacoes_dieta)


alergias = AlergiaIntolerancia.objects.all()


def _get_random_alergia():
    return _get_random_from_queryset(alergias)


escola = Escola.objects.all()


def _get_random_escola():
    return _get_random_from_queryset(escola)


motivos_negacao = MotivoNegacao.objects.all()


def _get_random_motivo_negacao():
    return _get_random_from_queryset(motivos_negacao)


alimentos = Alimento.objects.all()


def _get_random_alimento():
    return _get_random_from_queryset(alimentos)


@transaction.atomic
def cria_solicitacoes_dieta_especial(qtd=50):
    user = Usuario.objects.get(email="escola@admin.com")
    codigos_eol = random.sample(range(100000, 999999), qtd)
    alunos = []
    for cod_eol in codigos_eol:
        alunos.append(
            Aluno(
                nome=f.name(),
                codigo_eol=str(cod_eol),
                data_nascimento=datetime.date(2015, 10, 19),
                escola=_get_random_escola(),
            )
        )
    Aluno.objects.bulk_create(alunos)

    with open(
        "sme_sigpae_api/static/files/425-cuidado-area-de-teste.jpg", "rb"
    ) as image_file:
        test_file = SimpleUploadedFile(f.file_name(extension="jpg"), image_file.read())

    for index in range(qtd):
        if index % 10 == 0:
            print(f"{index / 10}% COMPLETO")

        for i in range(random.randint(1, 7)):
            solicitacao_dieta_especial = SolicitacaoDietaEspecial.objects.create(
                criado_por=user,
                nome_completo_pescritor=f.name(),
                registro_funcional_pescritor="".join(
                    random.choice(string.digits) for x in range(6)
                ),
                observacoes=f.text()[:50],
                aluno=alunos[index],
            )

            for _ in range(random.randint(2, 4)):
                Anexo.objects.create(
                    solicitacao_dieta_especial=solicitacao_dieta_especial,
                    arquivo=test_file,
                    nome=f.file_name(extension="jpg"),
                )
            fluxo_escola_felix_dieta_especial(solicitacao_dieta_especial, user, index)


# QTD_PEDIDOS = 1000
QTD_PEDIDOS = 50

print("-> criando solicitacoes dieta especial")
cria_solicitacoes_dieta_especial(QTD_PEDIDOS)
