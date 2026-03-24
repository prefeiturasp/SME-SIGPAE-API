import pytest
from rest_framework.serializers import ValidationError

from sme_sigpae_api.dados_comuns.fluxo_status import FichaTecnicaDoProdutoWorkflow
from sme_sigpae_api.pre_recebimento.ficha_tecnica.api.validators import ServiceValidacaoCorrecaoFichaTecnica
from sme_sigpae_api.pre_recebimento.ficha_tecnica.fixtures.factories.ficha_tecnica_do_produto_factory import (
    FichaTecnicaFactory,
    AnaliseFichaTecnicaFactory,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import FichaTecnicaDoProduto

pytestmark = pytest.mark.django_db

def test_valida_campos_flv_sucesso():
    # Criar ficha FLV Ponto a Ponto
    ficha = FichaTecnicaFactory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO
    )
    # Criar análise com alguns campos não conferidos (precisam de correção)
    analise = AnaliseFichaTecnicaFactory(
        ficha_tecnica=ficha,
        fabricante_envasador_conferido=False,
        detalhes_produto_conferido=False,
        responsavel_tecnico_conferido=True,
        outras_informacoes_conferido=True
    )

    attrs = {
        "fabricante": ficha.fabricante.fabricante.uuid,
        "organico": True,
        "mecanismo_controle": FichaTecnicaDoProduto.MECANISMO_CERTIFICACAO,
        "especie_variedade": "Banana Nanica",
    }

    validator = ServiceValidacaoCorrecaoFichaTecnica(ficha, attrs)
    # Não deve levantar exceção
    validator.valida_campos_obrigatorios_por_collapse()
    validator.valida_campos_nao_permitidos_por_collapse()

def test_valida_campos_flv_erro_campo_obrigatorio_faltando():
    ficha = FichaTecnicaFactory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO
    )
    AnaliseFichaTecnicaFactory(
        ficha_tecnica=ficha,
        detalhes_produto_conferido=False
    )

    # Faltando 'especie_variedade' que é obrigatório para FLV em detalhes_produto
    attrs = {
        "organico": True,
        "mecanismo_controle": "Audit"
    }

    validator = ServiceValidacaoCorrecaoFichaTecnica(ficha, attrs)
    with pytest.raises(ValidationError) as excinfo:
        validator.valida_campos_obrigatorios_por_collapse()
    
    assert "especie_variedade" in excinfo.value.detail

def test_valida_campos_flv_erro_campo_nao_permitido():
    ficha = FichaTecnicaFactory(
        categoria=FichaTecnicaDoProduto.CATEGORIA_FLV,
        tipo_entrega=FichaTecnicaDoProduto.PONTO_A_PONTO,
        status=FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO
    )
    AnaliseFichaTecnicaFactory(
        ficha_tecnica=ficha,
        detalhes_produto_conferido=False,
        informacoes_nutricionais_conferido=True # Já conferido, não pode enviar campos dele
    )

    attrs = {
        "organico": True,
        "especie_variedade": "Nanica",
        "porcao": "100g" # NÃO PERMITIDO para FLV ou se já conferido
    }

    validator = ServiceValidacaoCorrecaoFichaTecnica(ficha, attrs)
    with pytest.raises(ValidationError) as excinfo:
        validator.valida_campos_nao_permitidos_por_collapse()
    
    assert "porcao" in excinfo.value.detail
