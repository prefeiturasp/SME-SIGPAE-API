from django.db import models
from django.db.models import Q


class EditalManager(models.Manager):
    def check_editais_already_has_nome_protocolo(self, editais, nome_protocolo):
        return (
            self.filter(
                Q(uuid__in=editais),
                Q(
                    protocolos_padroes_dieta_especial__nome_protocolo__iexact=nome_protocolo
                ),
            )
            .values("numero")
            .distinct()
        )
