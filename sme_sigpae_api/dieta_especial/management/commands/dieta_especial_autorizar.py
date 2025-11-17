from django.core.management.base import BaseCommand
from faker import Faker

from sme_sigpae_api.dieta_especial.models import (
    AlergiaIntolerancia,
    Alimento,
    ClassificacaoDieta,
    SolicitacaoDietaEspecial,
    SubstituicaoAlimento,
)
from sme_sigpae_api.perfil.models import Usuario

faker = Faker()
fake = Faker("pt-br")


def autorizar_dieta(dieta_uuid):
    usuario = Usuario.objects.get(email="nutricodae@admin.com")
    alergias_intolerancias = AlergiaIntolerancia.objects.first()
    classificacao = ClassificacaoDieta.objects.first()

    dieta = SolicitacaoDietaEspecial.objects.get(uuid__startswith=dieta_uuid)
    dieta.ativo = True
    dieta.codae_autoriza(user=usuario)
    dieta.nome_protocolo = alergias_intolerancias.descricao
    dieta.classificacao = classificacao
    dieta.informacoes_adicionais = f"<p>{fake.paragraph(nb_sentences=10)}</p>"
    dieta.registro_funcional_nutricionista = (
        f"Elaborado por {usuario.nome} - CRN {usuario.crn_numero}"
    )
    dieta.alergias_intolerancias.add(alergias_intolerancias)
    dieta.save()

    # SubstituicaoAlimento
    alimento = Alimento.objects.first()
    # Escolhe os 3 primeiros alimentos (diferentes do alimento escolhido acima).
    alimentos_substitutos = Alimento.objects.exclude(pk=alimento.pk)[:3]

    substituicao_alimento = SubstituicaoAlimento.objects.create(
        solicitacao_dieta_especial=dieta,
        alimento=alimento,
        tipo="S",
        # substitutos=,
    )
    for i in alimentos_substitutos:
        substituicao_alimento.alimentos_substitutos.add(i)
    substituicao_alimento.save()

    return dieta


class Command(BaseCommand):
    help = """
    Autoriza uma Dieta Especial, informando o uuid da Dieta.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--uuid",
            "-u",
            dest="uuid",
            help="Informar uuid (5 primeiros dígitos) da dieta.",
        )

    def handle(self, *args, **options):
        uuid = options["uuid"]
        dieta = autorizar_dieta(uuid)
        self.stdout.write(f"Dieta Autorizada: {dieta}")
