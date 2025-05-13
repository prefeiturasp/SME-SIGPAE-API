from unittest.mock import Mock

from django.contrib.admin.sites import AdminSite

from sme_sigpae_api.dados_comuns.behaviors import PerfilDiretorSupervisao
from sme_sigpae_api.imr.admin import (
    EquipamentoAdmin,
    FormularioOcorrenciasBaseAdmin,
    InsumoAdmin,
    MobiliarioAdmin,
    ParametrizacaoOcorrenciaAdmin,
    PerfisFilter,
    ReparoEAdaptacaoAdmin,
    TipoFormularioFilter,
    TipoOcorrenciaAdmin,
    TipoPenalidadeAdmin,
    UtensilioCozinhaAdmin,
    UtensilioMesaAdmin,
)
from sme_sigpae_api.imr.models import (
    Equipamento,
    FormularioOcorrenciasBase,
    Insumo,
    Mobiliario,
    ParametrizacaoOcorrencia,
    ReparoEAdaptacao,
    TipoOcorrencia,
    TipoPenalidade,
    UtensilioCozinha,
    UtensilioMesa,
)


def test_tipo_penalidade_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao, tipo_penalidade_factory
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    tipo_penalidade = tipo_penalidade_factory()
    tipo_penalidade_admin = TipoPenalidadeAdmin(
        model=TipoPenalidade, admin_site=AdminSite()
    )
    tipo_penalidade_admin.save_model(
        obj=tipo_penalidade, request=Mock(user=usuario), form=None, change=None
    )
    assert tipo_penalidade.criado_por == usuario


def test_tipo_ocorrencia_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao, tipo_ocorrencia_factory
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    tipo_ocorrencia = tipo_ocorrencia_factory()
    tipo_ocorrencia_admin = TipoOcorrenciaAdmin(
        model=TipoOcorrencia, admin_site=AdminSite()
    )
    tipo_ocorrencia_admin.save_model(
        obj=tipo_ocorrencia, request=Mock(user=usuario), form=None, change=None
    )
    assert tipo_ocorrencia.criado_por == usuario


def test_perfis_filter_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    parametrizacao_ocorrencia_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia__perfis=[PerfilDiretorSupervisao.DIRETOR]
    )
    parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia__perfis=[PerfilDiretorSupervisao.SUPERVISAO]
    )

    perfis_filter = PerfisFilter(
        Mock(user=usuario),
        {"perfis": [PerfilDiretorSupervisao.DIRETOR]},
        PerfilDiretorSupervisao,
        ParametrizacaoOcorrenciaAdmin,
    )
    queryset = perfis_filter.queryset(
        Mock(user=usuario), ParametrizacaoOcorrencia.objects.all()
    )
    assert queryset.count() == 1

    perfis_filter = PerfisFilter(
        Mock(user=usuario),
        {"perfis": [PerfilDiretorSupervisao.SUPERVISAO]},
        PerfilDiretorSupervisao,
        ParametrizacaoOcorrenciaAdmin,
    )
    queryset = perfis_filter.queryset(
        Mock(user=usuario), ParametrizacaoOcorrencia.objects.all()
    )
    assert queryset.count() == 1

    perfis_filter = PerfisFilter(
        Mock(user=usuario),
        {"perfis": ["Tudo"]},
        PerfilDiretorSupervisao,
        ParametrizacaoOcorrenciaAdmin,
    )
    queryset = perfis_filter.queryset(
        Mock(user=usuario), ParametrizacaoOcorrencia.objects.all()
    )
    assert queryset.count() == 2


def test_parametrizacao_ocorrencia_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    parametrizacao_ocorrencia_factory,
):
    edital_numero = "78/SME/2016"
    perfis = [PerfilDiretorSupervisao.DIRETOR]
    parametrizacao_ocorrencia = parametrizacao_ocorrencia_factory.create(
        tipo_ocorrencia__edital__numero=edital_numero, tipo_ocorrencia__perfis=perfis
    )
    parametrizacao_ocorrencia_admin = ParametrizacaoOcorrenciaAdmin(
        model=ParametrizacaoOcorrencia, admin_site=AdminSite()
    )
    assert (
        parametrizacao_ocorrencia_admin.edital(parametrizacao_ocorrencia)
        == edital_numero
    )
    assert parametrizacao_ocorrencia_admin.perfis(parametrizacao_ocorrencia) == perfis


def test_tipo_formulario_filter_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    formulario_supervisao_factory,
    formulario_diretor_factory,
):
    client, usuario = client_autenticado_vinculo_coordenador_supervisao_nutricao

    formulario_supervisao_factory.create()
    formulario_diretor_factory.create()

    tipo_formulario_filter = TipoFormularioFilter(
        Mock(user=usuario),
        {"tipo_formulario": [PerfilDiretorSupervisao.DIRETOR]},
        FormularioOcorrenciasBase,
        FormularioOcorrenciasBaseAdmin,
    )
    queryset_diretor = tipo_formulario_filter.queryset(
        Mock(user=usuario), FormularioOcorrenciasBase.objects.all()
    )
    assert queryset_diretor.count() == 1

    tipo_formulario_filter = TipoFormularioFilter(
        Mock(user=usuario),
        {"tipo_formulario": [PerfilDiretorSupervisao.SUPERVISAO]},
        FormularioOcorrenciasBase,
        FormularioOcorrenciasBaseAdmin,
    )
    queryset_supervisao = tipo_formulario_filter.queryset(
        Mock(user=usuario), FormularioOcorrenciasBase.objects.all()
    )
    assert queryset_supervisao.count() == 1

    tipo_formulario_filter = TipoFormularioFilter(
        Mock(user=usuario),
        {"tipo_formulario": ["Tudo"]},
        FormularioOcorrenciasBase,
        FormularioOcorrenciasBaseAdmin,
    )
    queryset_tudo = tipo_formulario_filter.queryset(
        Mock(user=usuario), FormularioOcorrenciasBase.objects.all()
    )
    assert queryset_tudo.count() == 2


def test_utensilio_mesa_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    utensilio_mesa_factory,
):
    nome = "Faca de mesa"
    utensilio_mesa = utensilio_mesa_factory.create(nome=nome)
    utensilio_mesa_admin = UtensilioMesaAdmin(
        model=UtensilioMesa, admin_site=AdminSite()
    )
    assert utensilio_mesa_admin.nome_label(utensilio_mesa) == nome


def test_utensilio_cozinha_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    utensilio_cozinha_factory,
):
    nome = "Balde com tampa (100 litros)"
    utensilio_cozinha = utensilio_cozinha_factory.create(nome=nome)
    utensilio_cozinha_admin = UtensilioCozinhaAdmin(
        model=UtensilioCozinha, admin_site=AdminSite()
    )
    assert utensilio_cozinha_admin.nome_label(utensilio_cozinha) == nome


def test_equipamento_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    equipamento_factory,
):
    nome = "Fogão industrial com 2 queimadores (para lactário)"
    equipamento = equipamento_factory.create(nome=nome)
    equipamento_admin = EquipamentoAdmin(model=Equipamento, admin_site=AdminSite())
    assert equipamento_admin.nome_label(equipamento) == nome


def test_mobiliario_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    mobiliario_factory,
):
    nome = "Mesa de apoio inox"
    mobiliario = mobiliario_factory.create(nome=nome)
    mobiliario_admin = MobiliarioAdmin(model=Mobiliario, admin_site=AdminSite())
    assert mobiliario_admin.nome_label(mobiliario) == nome


def test_reparo_e_adaptacao_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    reparo_e_adaptacao_factory,
):
    nome = "Fiação elétrica"
    reparo_e_adaptacao = reparo_e_adaptacao_factory.create(nome=nome)
    reparo_e_adaptacao_admin = ReparoEAdaptacaoAdmin(
        model=ReparoEAdaptacao, admin_site=AdminSite()
    )
    assert reparo_e_adaptacao_admin.nome_label(reparo_e_adaptacao) == nome


def test_insumo_admin(
    client_autenticado_vinculo_coordenador_supervisao_nutricao,
    insumo_factory,
):
    nome = "Dispensador fixo ou móvel para álcool gel"
    insumo = insumo_factory.create(nome=nome)
    insumo_admin = InsumoAdmin(model=Insumo, admin_site=AdminSite())
    assert insumo_admin.nome_label(insumo) == nome
