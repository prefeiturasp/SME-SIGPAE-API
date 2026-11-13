from django import forms


class AlunosPorFaixaEtariaForm(forms.Form):
    data_referencia = forms.DateField()
