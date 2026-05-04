import functools
import operator

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from src.recebimento.models import QuestaoConferencia


class QuestaoForm(forms.ModelForm):
    class Meta:
        model = QuestaoConferencia
        fields = "__all__"
        widgets = {
            "questao": forms.TextInput(
                attrs={
                    "oninput": "this.value = this.value.toUpperCase();",
                    "size": "100",
                }
            ),
        }

    def full_clean(self, *args, **kwargs):
        super().full_clean()
        # Limpa os erros extras para o campo 'posicao'
        if "posicao" in self.errors and len(self.errors["posicao"]) > 1:
            self.errors["posicao"] = self.error_class([self.errors["posicao"][0]])

    def clean(self):
        cleaned_data = super().clean()
        posicao = cleaned_data.get("posicao", None)
        tipo_questao = cleaned_data.get("tipo_questao", None)

        if posicao and tipo_questao:
            tipos_questoes = list(tipo_questao)
            filtro = functools.reduce(
                operator.or_,
                (
                    Q(tipo_questao__icontains=tipo, posicao=posicao)
                    for tipo in tipos_questoes
                ),
            )
            qs = QuestaoConferencia.objects.filter(filtro)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError(
                    {
                        "posicao": "Já existe uma pergunta com essa posição para este tipo de questão."
                    }
                )
