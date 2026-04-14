from django import forms

from ..escola.models import DiretoriaRegional, Escola, Lote
from ..terceirizada.models import Terceirizada
from .models import ProtocoloPadraoDietaEspecial, SolicitacaoDietaEspecial
from .solicitacao_dieta_especial.models import (
    AlergiaIntolerancia,
    ClassificacaoDieta,
)


class NegaDietaEspecialForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoDietaEspecial
        fields = [
            "justificativa_negacao",
            "motivo_negacao",
            "registro_funcional_nutricionista",
        ]


class SolicitacoesAtivasInativasPorAlunoForm(forms.Form):
    codigo_eol = forms.CharField(required=False)
    nome_aluno = forms.CharField(required=False)
    escola = forms.ModelChoiceField(
        required=False, queryset=Escola.objects.all(), to_field_name="uuid"
    )
    dre = forms.ModelChoiceField(
        required=False, queryset=DiretoriaRegional.objects.all(), to_field_name="uuid"
    )


class RelatorioQuantitativoSolicDietaEspForm(forms.Form):
    dre = forms.ModelMultipleChoiceField(
        required=False, queryset=DiretoriaRegional.objects.all(), to_field_name="uuid"
    )
    escola = forms.ModelMultipleChoiceField(
        required=False, queryset=Escola.objects.all(), to_field_name="uuid"
    )
    diagnostico = forms.ModelMultipleChoiceField(
        required=False, queryset=AlergiaIntolerancia.objects.all()
    )
    classificacao = forms.ModelMultipleChoiceField(
        required=False, queryset=ClassificacaoDieta.objects.all()
    )
    status = forms.ChoiceField(
        required=False,
        choices=(
            ("", "Todos"),
            ("ativas", "Ativa"),
            ("inativas", "Inativa"),
            ("pendentes", "Pendente de aprovação"),
        ),
    )
    data_inicial = forms.DateField(required=False)
    data_final = forms.DateField(required=False)


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


class RelatorioDietaTerceirizadaForm(forms.Form):
    terceirizada_uuid = forms.ModelChoiceField(
        required=False, queryset=Terceirizada.objects.all(), to_field_name="uuid"
    )
    status = forms.ChoiceField(
        required=False,
        choices=(
            ("AUTORIZADAS", "Autorizadas"),
            ("CANCELADAS", "Canceladas"),
        ),
    )
    lote = forms.ModelMultipleChoiceField(
        required=False,
        queryset=Lote.objects.all(),
    )
    classificacao_dieta = forms.ModelMultipleChoiceField(
        required=False, queryset=ClassificacaoDieta.objects.all()
    )
    protocolo_padrao = forms.ModelMultipleChoiceField(
        required=False, queryset=ProtocoloPadraoDietaEspecial.objects.all()
    )
    data_inicial = forms.DateField(required=False)
    data_final = forms.DateField(required=False)


class PanoramaForm(forms.Form):
    escola = forms.ModelChoiceField(
        required=False, queryset=Escola.objects.all(), to_field_name="uuid"
    )
