import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .api.serializers import SolicitacaoAbertaSerializer
from .models import SolicitacaoAberta

logger = logging.getLogger(__name__)


@receiver(post_save, sender=SolicitacaoAberta)
def post_save(sender, instance, created, **kwargs):
    try:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "solicitacoes_abertas",
            {
                "type": "solicitacao.message",
                "data": {
                    "message": SolicitacaoAbertaSerializer(
                        SolicitacaoAberta.objects.all(), many=True
                    ).data
                },
            },
        )

    except Exception as e:
        logger.error(e)


@receiver(post_delete, sender=SolicitacaoAberta)
def post_delete(sender, instance, **kwargs):
    try:
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "solicitacoes_abertas",
            {
                "type": "solicitacao.message",
                "data": {
                    "message": SolicitacaoAbertaSerializer(
                        SolicitacaoAberta.objects.all(), many=True
                    ).data
                },
            },
        )

    except Exception as e:
        logger.error(e)
