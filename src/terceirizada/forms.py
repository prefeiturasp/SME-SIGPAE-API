from django import forms


class RelatorioQuantitativoForm(forms.Form):
    nome_terceirizada = forms.CharField(required=False)
    data_inicial = forms.DateField(required=False)
    data_final = forms.DateField(required=False)
