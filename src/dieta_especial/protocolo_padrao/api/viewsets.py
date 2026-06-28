import json
from datetime import datetime

from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from src.dieta_especial.protocolo_padrao.api.serializers import (
    ProtocoloPadraoDietaEspecialSerializer,
    ProtocoloPadraoDietaEspecialSimplesSerializer,
)
from src.dieta_especial.protocolo_padrao.api.serializers_create import (
    ProtocoloPadraoDietaEspecialSerializerCreate,
)

from ....terceirizada.models import Contrato, Edital
from ...solicitacao_dieta_especial.models import SolicitacaoDietaEspecial
from ..models import ProtocoloPadraoDietaEspecial
from .pagination import ProtocoloPadraoPagination


class ProtocoloPadraoDietaEspecialViewSet(ModelViewSet):
    lookup_field = "uuid"
    permission_classes = (IsAuthenticated,)
    queryset = ProtocoloPadraoDietaEspecial.objects.filter(ativo=True).order_by(
        "nome_protocolo"
    )
    serializer_class = ProtocoloPadraoDietaEspecialSerializer
    pagination_class = ProtocoloPadraoPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("nome_protocolo", "status")

    def get_serializer_class(self):
        if self.action in ["create", "update"]:
            return ProtocoloPadraoDietaEspecialSerializerCreate
        return ProtocoloPadraoDietaEspecialSerializer

    def get_queryset(self):
        queryset = ProtocoloPadraoDietaEspecial.objects.filter(ativo=True)
        if "editais[]" in self.request.query_params:
            queryset = queryset.filter(
                editais__uuid__in=self.request.query_params.getlist("editais[]")
            ).distinct()
        return queryset.order_by("nome_protocolo")

    @action(detail=False, methods=["GET"], url_path="lista-status")
    def lista_status(self, request):
        list_status = ProtocoloPadraoDietaEspecial.STATUS_NOMES.keys()

        return Response({"results": list_status})

    @action(detail=False, methods=["GET"], url_path="nomes")
    def nomes(self, request):
        nomes = self.queryset.values_list("nome_protocolo", flat=True).distinct()

        return Response({"results": nomes})

    @action(detail=False, methods=["GET"], url_path="lista-protocolos-liberados")
    def lista_protocolos_liberados(self, request):
        dieta_uuid = request.query_params.get("dieta_especial_uuid", None)
        solicitacao = SolicitacaoDietaEspecial.objects.get(uuid=dieta_uuid)
        escola = solicitacao.escola
        if escola.eh_parceira:
            editais_uuid = Edital.objects.filter(numero__iexact="PARCEIRA").values_list(
                "uuid", flat=True
            )
        else:
            editais_uuid = Contrato.objects.filter(lotes__in=[escola.lote]).values_list(
                "edital__uuid", flat=True
            )
        protocolos_liberados = (
            self.get_queryset()
            .filter(
                status=ProtocoloPadraoDietaEspecial.STATUS_LIBERADO,
                editais__uuid__in=editais_uuid,
            )
            .distinct()
        )
        response = {
            "results": ProtocoloPadraoDietaEspecialSimplesSerializer(
                protocolos_liberados, many=True
            ).data
        }
        return Response(response)

    @action(
        detail=False, methods=["GET"], url_path="lista-protocolos-liberados-por-edital"
    )
    def lista_protocolos_liberados_por_edital(self, request):
        edital_uuid = request.query_params.get("edital_uuid", None)
        protocolos_liberados = self.get_queryset().filter(
            status=ProtocoloPadraoDietaEspecial.STATUS_LIBERADO,
            editais__uuid__in=[edital_uuid],
        )
        response = {
            "results": ProtocoloPadraoDietaEspecialSimplesSerializer(
                protocolos_liberados, many=True
            ).data
        }
        return Response(response)

    def criar_historico_editais(self, protocolo, validated_data):
        historico = {}
        changes = []

        outras_informacoes = validated_data.get("outras_informacoes")

        editais_antes = protocolo.editais.all()
        editais_depois = Edital.objects.filter(
            uuid__in=validated_data.get("editais_destino", [])
        )
        soma_todos_editais = editais_antes | editais_depois
        diferenca = soma_todos_editais.distinct().difference(editais_antes)

        if diferenca and diferenca.count() > 0:
            changes.append(
                {
                    "field": "editais",
                    "from": [
                        edital.numero for edital in editais_antes.order_by("numero")
                    ],
                    "to": [
                        edital.numero
                        for edital in soma_todos_editais.distinct().order_by("numero")
                    ],
                }
            )

        if (protocolo.outras_informacoes != outras_informacoes) and (
            outras_informacoes != ""
        ):
            changes.append(
                {
                    "field": "outras informacoes",
                    "from": protocolo.outras_informacoes,
                    "to": outras_informacoes,
                }
            )

        if changes and len(changes) > 0:
            historico["updated_at"] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
            historico["user"] = {
                "uuid": str(self.request.user.uuid),
                "email": self.request.user.email,
                "nome": self.request.user.nome,
                "username": self.request.user.username,
            }
            historico["action"] = "UPDATE_VINCULOS"
            historico["changes"] = changes
        return historico

    @action(detail=False, methods=["PUT"], url_path="atualizar-editais")
    def atualizar_editais(self, request):
        protocolos_padrao = request.data.get("protocolos_padrao", None)
        editais_destino = request.data.get("editais_destino", None)
        outras_informacoes = request.data.get("outras_informacoes", "")

        validated_data = {
            "editais_destino": editais_destino,
            "outras_informacoes": outras_informacoes,
        }

        if protocolos_padrao and editais_destino:
            editais = Edital.objects.filter(uuid__in=editais_destino)
            protocolos = self.get_queryset().filter(uuid__in=protocolos_padrao)
            for protocolo in protocolos:
                historico = self.criar_historico_editais(protocolo, validated_data)
                if len(historico) > 0:
                    hist = (
                        json.loads(protocolo.historico) if protocolo.historico else []
                    )
                    hist.append(historico)
                    protocolo.historico = json.dumps(hist)

                protocolo.outras_informacoes = outras_informacoes
                protocolo.editais.add(*editais)
                protocolo.save()
            return Response(
                {"results": "Protacolos relacionados com sucesso."},
                status=status.HTTP_200_OK,
            )
        if not protocolos_padrao:
            return Response(
                {"results": "É necessário selecionar um Protocolo Padrão."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not editais_destino:
            return Response(
                {"results": "É necessário selecionar um Edital."},
                status=status.HTTP_400_BAD_REQUEST,
            )
