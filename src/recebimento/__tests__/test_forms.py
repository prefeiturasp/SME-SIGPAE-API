import pytest

from src.recebimento.forms import QuestaoForm

pytestmark = pytest.mark.django_db


def test_questao_conferencia_wedget_attrs_form_validation():
    # testa o widget attrs
    questao_form = QuestaoForm()
    questao_widget = questao_form.fields["questao"].widget
    assert (
        questao_widget.attrs.get("oninput") == "this.value = this.value.toUpperCase();"
    )
    assert questao_widget.attrs.get("size") == "100"


def test_questao_conferencia_form_clean_method_validation(questao_conferencia_factory):
    questao_conferencia_factory.create(
        questao="IDENTIFICACAO PRODUTO",
        tipo_questao=["PRIMARIA"],
        pergunta_obrigatoria=True,
        posicao=1,
        status="ATIVO",
    )

    data = {
        "questao": "IDENTIFICACAO fabricante",
        "tipo_questao": ["PRIMARIA"],
        "pergunta_obrigatoria": True,
        "posicao": 2,
        "status": "ATIVO",
    }
    form = QuestaoForm(data=data)

    # Checca se o formulário é válido
    assert form.is_valid() == True

    # remove a posição para validar o erro
    data["posicao"] = None
    form = QuestaoForm(data=data)

    #  Com a alteração o form não pode ser mais valido
    assert form.is_valid() == False
    assert form.errors["posicao"] == [
        "Posição é obrigatória se a pergunta for obrigatória."
    ]

    # Altera a posição para um valor já existente para validar a tratativa de erro
    data["posicao"] = 1
    form = QuestaoForm(data=data)

    #  Com a alteração o form não pode ser mais valido
    assert form.is_valid() == False
    assert form.errors["posicao"] == [
        "Já existe uma pergunta com essa posição para este tipo de questão."
    ]
