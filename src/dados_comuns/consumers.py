import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .api.serializers import SolicitacaoAbertaSerializer
from .models import SolicitacaoAberta

logger = logging.getLogger()


class SolicitacoesAbertasConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("solicitacoes_abertas", self.channel_name)
        await self.accept()

        solicitacoes_abertas = await self.get_solicitacoes_abertas()

        await self.send(text_data=json.dumps({"message": solicitacoes_abertas}))

    @database_sync_to_async
    def get_solicitacoes_abertas(self):
        return SolicitacaoAbertaSerializer(
            SolicitacaoAberta.objects.all(), many=True
        ).data

    async def disconnect(self, code):
        solicitacoes_abertas = await self.get_solicitacoes_abertas()

        await self.send(text_data=json.dumps({"message": solicitacoes_abertas}))

        await self.channel_layer.group_discard(
            "solicitacoes_abertas", self.channel_name
        )

    async def solicitacao_message(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    async def dispatch(self, message):
        """Created because when the ValueErrorException is raised the connection is broken."""
        try:
            return await super().dispatch(message)

        except ValueError as exception:
            logger.error(exception)
