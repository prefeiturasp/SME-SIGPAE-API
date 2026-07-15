from django import forms

from ..dados_comuns.fluxo_status import HomologacaoProdutoWorkflow
from .models import Fabricante, Marca


class ProdutoPorParametrosForm(forms.Form):
    uuid = forms.UUIDField(required=False)
    nome_fabricante = forms.CharField(required=False)
    nome_marca = forms.CharField(required=False)
    nome_edital = forms.CharField(required=False)
    tipo = forms.CharField(required=False)
    nome_produto = forms.CharField(required=False)
    nome_terceirizada = forms.CharField(required=False)
    data_inicial = forms.DateField(required=False)
    data_final = forms.DateField(required=False)
    status = forms.MultipleChoiceField(
        required=False,
        choices=[(str(state), state) for state in HomologacaoProdutoWorkflow.states],
    )


class ProdutoPorParametrosFormHomologados(forms.Form):
    uuid = forms.UUIDField(required=False)
    nome_fabricante = forms.CharField(required=False)
    nome_marca = forms.CharField(required=False)
    nome_edital = forms.CharField(required=False)
    tipo = forms.CharField(required=False)
    nome_produto = forms.CharField(required=False)
    nome_terceirizada = forms.CharField(required=False)
    data_homologacao = forms.DateField(required=False)
    status = forms.MultipleChoiceField(
        required=False,
        choices=[(str(state), state) for state in HomologacaoProdutoWorkflow.states],
    )


class ProdutoJaExisteForm(forms.Form):
    fabricante = forms.ModelChoiceField(Fabricante.objects.all(), to_field_name="uuid")
    marca = forms.ModelChoiceField(Marca.objects.all(), to_field_name="uuid")
    nome = forms.CharField()


class NomeDeProdutoEditalForm(forms.ModelForm):
    class Meta:
        fields = ("nome", "ativo", "tipo_produto")

    def __init__(self, *args, **kwargs):  # noqa D107
        super().__init__(*args, **kwargs)
        self.fields["nome"].required = True
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            self.fields["ativo"].disabled = False
        else:
            self.fields["ativo"].disabled = True
