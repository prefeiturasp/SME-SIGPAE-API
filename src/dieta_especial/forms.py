from django import forms

from src.dieta_especial.solicitacao_dieta_especial.models import AlergiaIntolerancia
from src.escola.models import DiretoriaRegional, Escola


class RelatorioDietaForm(forms.Form):
    dre = forms.ModelChoiceField(
        required=False, queryset=DiretoriaRegional.objects.all(), to_field_name="uuid"
    )
    escola = forms.ModelMultipleChoiceField(
        required=False, queryset=Escola.objects.all(), to_field_name="uuid"
    )
    diagnostico = forms.ModelMultipleChoiceField(
        required=False, queryset=AlergiaIntolerancia.objects.all()
    )
    data_inicial = forms.DateField(required=False)
    data_final = forms.DateField(required=False)
