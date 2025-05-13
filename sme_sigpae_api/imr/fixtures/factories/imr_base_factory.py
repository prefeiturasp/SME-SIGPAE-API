import factory
from factory import Sequence, SubFactory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger
from faker import Faker

from sme_sigpae_api.escola.fixtures.factories.escola_factory import EscolaFactory
from sme_sigpae_api.imr.models import (
    AnexosFormularioBase,
    CategoriaOcorrencia,
    EditalEquipamento,
    EditalInsumo,
    EditalMobiliario,
    EditalReparoEAdaptacao,
    EditalUtensilioCozinha,
    EditalUtensilioMesa,
    Equipamento,
    FaixaPontuacaoIMR,
    FormularioDiretor,
    FormularioOcorrenciasBase,
    FormularioSupervisao,
    Insumo,
    Mobiliario,
    ObrigacaoPenalidade,
    OcorrenciaNaoSeAplica,
    ParametrizacaoOcorrencia,
    PerfilDiretorSupervisao,
    PeriodoVisita,
    ReparoEAdaptacao,
    RespostaCampoNumerico,
    RespostaCampoTextoSimples,
    TipoGravidade,
    TipoOcorrencia,
    TipoPenalidade,
    TipoPerguntaParametrizacaoOcorrencia,
    TipoRespostaModelo,
    UtensilioCozinha,
    UtensilioMesa,
)
from sme_sigpae_api.medicao_inicial.fixtures.factories.solicitacao_medicao_inicial_base_factory import (
    SolicitacaoMedicaoInicialFactory,
)
from sme_sigpae_api.perfil.fixtures.factories.perfil_base_factories import (
    UsuarioFactory,
)
from sme_sigpae_api.terceirizada.fixtures.factories.terceirizada_factory import (
    EditalFactory,
)

fake = Faker("pt_BR")


class TipoGravidadeFactory(DjangoModelFactory):
    class Meta:
        model = TipoGravidade

    tipo = Sequence(lambda n: f"tipo - {fake.unique.name()}")


class TipoPenalidadeFactory(DjangoModelFactory):
    class Meta:
        model = TipoPenalidade

    edital = SubFactory(EditalFactory)
    numero_clausula = Sequence(lambda n: fake.unique.random_int(min=1, max=1000))
    descricao = Sequence(lambda n: f"descrição - {fake.unique.name()}")
    gravidade = SubFactory(TipoGravidadeFactory)


class ObrigacaoPenalidadeFactory(DjangoModelFactory):
    class Meta:
        model = ObrigacaoPenalidade

    tipo_penalidade = SubFactory(TipoPenalidadeFactory)
    descricao = Sequence(lambda n: f"descrição - {fake.unique.name()}")


class TipoRespostaModeloFactory(DjangoModelFactory):
    class Meta:
        model = TipoRespostaModelo

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class TipoPerguntaParametrizacaoOcorrenciaFactory(DjangoModelFactory):
    class Meta:
        model = TipoPerguntaParametrizacaoOcorrencia

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")
    tipo_resposta = SubFactory(TipoRespostaModeloFactory)


class CategoriaOcorrenciaFactory(DjangoModelFactory):
    class Meta:
        model = CategoriaOcorrencia

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")
    perfis = Sequence(
        lambda n: [
            fake.random_element(
                [PerfilDiretorSupervisao.DIRETOR, PerfilDiretorSupervisao.SUPERVISAO]
            )
        ]
    )
    posicao = FuzzyInteger(1)


class TipoOcorrenciaFactory(DjangoModelFactory):
    class Meta:
        model = TipoOcorrencia

    edital = SubFactory(EditalFactory)
    titulo = Sequence(lambda n: f"titulo - {fake.unique.name()}")
    descricao = Sequence(lambda n: f"descrição - {fake.unique.name()}")
    categoria = SubFactory(CategoriaOcorrenciaFactory)
    penalidade = SubFactory(TipoPenalidadeFactory)
    perfis = Sequence(
        lambda n: [
            fake.random_element(
                [PerfilDiretorSupervisao.DIRETOR, PerfilDiretorSupervisao.SUPERVISAO]
            )
        ]
    )
    posicao = FuzzyInteger(1)


class ParametrizacaoOcorrenciaFactory(DjangoModelFactory):
    class Meta:
        model = ParametrizacaoOcorrencia

    titulo = Sequence(lambda n: f"nome - {fake.unique.name()}")
    tipo_ocorrencia = SubFactory(TipoOcorrenciaFactory)
    tipo_pergunta = SubFactory(TipoPerguntaParametrizacaoOcorrenciaFactory)


class PeriodoVisitaFactory(DjangoModelFactory):
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")

    class Meta:
        model = PeriodoVisita


class FaixaPontuacaoFactory(DjangoModelFactory):
    class Meta:
        model = FaixaPontuacaoIMR

    pontuacao_minima = Sequence(lambda n: fake.unique.random_int(min=1, max=100))
    pontuacao_maxima = Sequence(lambda n: fake.unique.random_int(min=1, max=100))
    porcentagem_desconto = Sequence(lambda n: fake.unique.random_int(min=1, max=100))


class UtensilioMesaFactory(DjangoModelFactory):
    class Meta:
        model = UtensilioMesa

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalUtensilioMesaFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def utensilios_mesa(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for utensilio_mesa in extracted:
                self.utensilios_mesa.add(utensilio_mesa)

    class Meta:
        model = EditalUtensilioMesa


class UtensilioCozinhaFactory(DjangoModelFactory):
    class Meta:
        model = UtensilioCozinha

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalUtensilioCozinhaFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def utensilios_cozinha(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for utensilio_cozinha in extracted:
                self.utensilios_cozinha.add(utensilio_cozinha)

    class Meta:
        model = EditalUtensilioCozinha


class EquipamentoFactory(DjangoModelFactory):
    class Meta:
        model = Equipamento

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalEquipamentoFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def equipamentos(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for equipamento in extracted:
                self.equipamentos.add(equipamento)

    class Meta:
        model = EditalEquipamento


class MobiliarioFactory(DjangoModelFactory):
    class Meta:
        model = Mobiliario

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalMobiliarioFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def mobiliarios(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for mobiliario in extracted:
                self.mobiliarios.add(mobiliario)

    class Meta:
        model = EditalMobiliario


class ReparoEAdaptacaoFactory(DjangoModelFactory):
    class Meta:
        model = ReparoEAdaptacao

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalReparoEAdaptacaoFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def reparos_e_adaptacoes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for reparo_e_adaptacao in extracted:
                self.reparos_e_adaptacoes.add(reparo_e_adaptacao)

    class Meta:
        model = EditalReparoEAdaptacao


class InsumoFactory(DjangoModelFactory):
    class Meta:
        model = Insumo

    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")


class EditalInsumoFactory(DjangoModelFactory):
    edital = SubFactory(EditalFactory)

    @factory.post_generation
    def insumos(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for insumo in extracted:
                self.insumos.add(insumo)

    class Meta:
        model = EditalInsumo


class FormularioOcorrenciasBaseFactory(DjangoModelFactory):
    usuario = SubFactory(UsuarioFactory)
    data = factory.faker.Faker("date")

    class Meta:
        model = FormularioOcorrenciasBase


class AnexosFormularioBaseFactory(DjangoModelFactory):
    anexo = factory.django.FileField()
    nome = Sequence(lambda n: f"nome - {fake.unique.name()}")
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)

    class Meta:
        model = AnexosFormularioBase


class FormularioSupervisaoFactory(DjangoModelFactory):
    escola = SubFactory(EscolaFactory)
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)
    periodo_visita = SubFactory(PeriodoVisitaFactory)
    nome_nutricionista_empresa = Sequence(lambda n: f"nome - {fake.unique.name()}")
    maior_frequencia_no_periodo = Sequence(lambda n: fake.random.randint(100, 300))
    status = FormularioSupervisao.workflow_class.EM_PREENCHIMENTO

    class Meta:
        model = FormularioSupervisao


class FormularioDiretorFactory(DjangoModelFactory):
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)
    solicitacao_medicao_inicial = SubFactory(SolicitacaoMedicaoInicialFactory)

    class Meta:
        model = FormularioDiretor


class RespostaCampoTextoSimplesFactory(DjangoModelFactory):
    resposta = Sequence(lambda n: f"resposta - {fake.unique.name()}")
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)
    parametrizacao = SubFactory(ParametrizacaoOcorrenciaFactory)
    grupo = Sequence(lambda n: fake.random.randint(1, 5))

    class Meta:
        model = RespostaCampoTextoSimples


class RespostaCampoNumericoFactory(DjangoModelFactory):
    resposta = Sequence(lambda n: fake.random.randint(1, 300))
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)
    parametrizacao = SubFactory(ParametrizacaoOcorrenciaFactory)
    grupo = Sequence(lambda n: fake.random.randint(1, 5))

    class Meta:
        model = RespostaCampoNumerico


class OcorrenciaNaoSeAplicaFactory(DjangoModelFactory):
    grupo = Sequence(lambda n: fake.random.randint(1, 5))
    descricao = Sequence(lambda n: f"descricao - {fake.unique.name()}")
    formulario_base = SubFactory(FormularioOcorrenciasBaseFactory)
    tipo_ocorrencia = SubFactory(TipoOcorrenciaFactory)

    class Meta:
        model = OcorrenciaNaoSeAplica
