import datetime

from des.models import DynamicEmailConfiguration
from django.db import IntegrityError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from workalendar.america import BrazilSaoPauloCity

from ... import __version__
from ...escola.models import DiaSuspensaoAtividades, Escola
from ..behaviors import DiasSemana, TempoPasseio
from ..constants import TEMPO_CACHE_6H, obter_dias_uteis_apos_hoje
from ..models import (
    CategoriaPerguntaFrequente,
    CentralDeDownload,
    Notificacao,
    PerguntaFrequente,
    SolicitacaoAberta,
    TemplateMensagem,
)
from ..permissions import UsuarioCODAEGestaoAlimentacao
from ..utils import obter_dias_uteis_apos
from .filters import CentralDeDownloadFilter, NotificacaoFilter
from .paginations import CustomPagination, DownloadPagination
from .serializers import (
    CategoriaPerguntaFrequenteSerializer,
    CentralDeDownloadSerializer,
    ConfiguracaoEmailSerializer,
    ConfiguracaoMensagemSerializer,
    ConsultaPerguntasFrequentesSerializer,
    NotificacaoSerializer,
    PerguntaFrequenteCreateSerializer,
    PerguntaFrequenteSerializer,
    SolicitacaoAbertaSerializer,
)

calendario = BrazilSaoPauloCity()


class ApiVersion(viewsets.ViewSet):
    permission_classes = (AllowAny,)

    def list(self, request):
        return Response({"API_Version": __version__})


class DiasDaSemanaViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    @method_decorator(cache_page(TEMPO_CACHE_6H))
    def list(self, request):
        return Response(dict(DiasSemana.DIAS))


class TempoDePasseioViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    @method_decorator(cache_page(TEMPO_CACHE_6H))
    def list(self, request):
        tempo_de_passeio_descricao = {
            TempoPasseio.QUATRO: {
                "quantidade_kits": 1,
                "descricao": "até 4 horas: 1 kit",
            },
            TempoPasseio.CINCO_A_SETE: {
                "quantidade_kits": 2,
                "descricao": "entre 5 e 7 horas: 2 kits",
            },
            TempoPasseio.OITO_OU_MAIS: {
                "quantidade_kits": 3,
                "descricao": "8 ou mais horas: 3 kits",
            },
        }
        return Response(tempo_de_passeio_descricao)


class DiasUteisViewSet(ViewSet):
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        data = request.query_params.get("data")
        if data:
            data_apos_quatro_dias_uteis = obter_dias_uteis_apos(
                datetime.datetime.strptime(data, "%d/%m/%Y"), quantidade_dias=4
            )
            return Response(
                {"data_apos_quatro_dias_uteis": data_apos_quatro_dias_uteis}
            )

        dias_com_suspensao_2, dias_com_suspensao_5 = self._calcular_dias_com_suspensao(
            request
        )
        dias_uteis = self._calcular_dias_uteis(
            dias_com_suspensao_2, dias_com_suspensao_5
        )

        return Response(dias_uteis)

    def _calcular_dias_com_suspensao(self, request):
        escola_uuid = request.query_params.get("escola_uuid")
        eh_solicitacao_unificada = (
            request.query_params.get("eh_solicitacao_unificada", "false").lower()
            == "true"
        )

        if escola_uuid:
            escola = Escola.objects.get(uuid=escola_uuid)
            dias_com_suspensao_2 = DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                escola=escola, quantidade_dias=2
            )
            dias_com_suspensao_5 = DiaSuspensaoAtividades.get_dias_com_suspensao_escola(
                escola=escola, quantidade_dias=5
            )
        elif eh_solicitacao_unificada:
            dre = request.user.vinculo_atual.instituicao
            dias_com_suspensao_2 = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                    dre=dre, quantidade_dias=2
                )
            )
            dias_com_suspensao_5 = (
                DiaSuspensaoAtividades.get_dias_com_suspensao_solicitacao_unificada(
                    dre=dre, quantidade_dias=5
                )
            )
        else:
            dias_com_suspensao_2, dias_com_suspensao_5 = 0, 0

        return dias_com_suspensao_2, dias_com_suspensao_5

    def _calcular_dias_uteis(self, dias_com_suspensao_2, dias_com_suspensao_5):
        return {
            "proximos_cinco_dias_uteis": obter_dias_uteis_apos_hoje(
                5 + dias_com_suspensao_5
            ),
            "proximos_dois_dias_uteis": obter_dias_uteis_apos_hoje(
                3 + dias_com_suspensao_2
            ),
        }


class FeriadosAnoViewSet(ViewSet):
    permission_classes = (AllowAny,)

    def list(self, request):
        calendario.holidays()

        def formatar_data(data):
            return datetime.date.strftime(data, "%d/%m/%Y")

        retorno = [formatar_data(h[0]) for h in calendario.holidays()]

        return Response({"results": retorno}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        url_path="ano-atual-e-proximo",
    )
    def feriados_ano_atual_e_proximo(self, request, uuid=None):
        ano_atual = datetime.datetime.now().year
        ano_proximo = ano_atual + 1

        feriados_atual = calendario.holidays(ano_atual)
        feriados_proximo = calendario.holidays(ano_proximo)

        retorno = [h[0] for h in feriados_atual] + [h[0] for h in feriados_proximo]

        return Response({"results": retorno}, status=status.HTTP_200_OK)


class ConfiguracaoEmailViewSet(ModelViewSet):
    queryset = DynamicEmailConfiguration.objects.all()
    serializer_class = ConfiguracaoEmailSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            return Response(
                data={
                    "error": "A configuração já existe, tente usar o método PUT",
                    "detail": f"{e}",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TemplateMensagemViewSet(ModelViewSet):
    lookup_field = "uuid"
    queryset = TemplateMensagem.objects.all()
    serializer_class = ConfiguracaoMensagemSerializer


class CategoriaPerguntaFrequenteViewSet(ModelViewSet):
    lookup_field = "uuid"
    queryset = CategoriaPerguntaFrequente.objects.all()

    def get_serializer_class(self):
        if self.action == "perguntas_por_categoria":
            return ConsultaPerguntasFrequentesSerializer
        return CategoriaPerguntaFrequenteSerializer

    @action(detail=False, url_path="perguntas-por-categoria")
    def perguntas_por_categoria(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)


class PerguntaFrequenteViewSet(ModelViewSet):
    lookup_field = "uuid"
    queryset = PerguntaFrequente.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return PerguntaFrequenteCreateSerializer
        return PerguntaFrequenteSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = (UsuarioCODAEGestaoAlimentacao,)
        return super(PerguntaFrequenteViewSet, self).get_permissions()


class NotificacaoViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [IsAuthenticated]
    queryset = Notificacao.objects.all()
    serializer_class = NotificacaoSerializer
    pagination_class = CustomPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = NotificacaoFilter

    def get_queryset(self):
        qs = (
            Notificacao.objects.filter(usuario=self.request.user)
            .all()
            .order_by("-criado_em")
        )

        return qs

    def list(self, request, *args, **kwargs):
        pendencias = self.filter_queryset(
            self.get_queryset().filter(
                tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA, resolvido=False
            )
        )
        gerais = self.filter_queryset(
            self.get_queryset().exclude(
                tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA, resolvido=False
            )
        )
        # Notificações de pendencias não resolvidas tem precedencia na listagem de notificações
        queryset = list(pendencias) + list(gerais)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificacaoSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = NotificacaoSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="gerais")
    def lista_notificacoes_gerais(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().exclude(
                tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA, resolvido=False
            )
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificacaoSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = NotificacaoSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="pendencias-nao-resolvidas")
    def lista_pendencias_nao_resolvidas(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(
                tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA, resolvido=False
            )
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = NotificacaoSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return response

        serializer = NotificacaoSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="quantidade-nao-lidos")
    def quantidade_de_nao_lidos(self, request):
        notificacoes = (
            Notificacao.objects.filter(usuario=self.request.user)
            .filter(
                lido=False,
                tipo__in=[
                    Notificacao.TIPO_NOTIFICACAO_ALERTA,
                    Notificacao.TIPO_NOTIFICACAO_AVISO,
                ],
            )
            .count()
        )
        pendencias = (
            Notificacao.objects.filter(usuario=self.request.user)
            .filter(resolvido=False, tipo=Notificacao.TIPO_NOTIFICACAO_PENDENCIA)
            .count()
        )
        data = {"quantidade_nao_lidos": notificacoes + pendencias}
        return Response(data)

    @action(detail=False, methods=["put"], url_path="marcar-lido")
    def marcar_como_lido_nao_lido(self, request):
        dado = self.request.data

        try:
            notificacao = Notificacao.objects.filter(uuid=dado["uuid"]).first()
            notificacao.lido = dado["lido"]
            notificacao.save()
        except Exception as err:
            return Response(
                dict(detail=f"Erro ao realizar atualização: {err}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultado = {"mensagem": "Notificação atualizada com sucesso"}
        status_code = status.HTTP_200_OK

        return Response(resultado, status=status_code)


class CentralDeDownloadViewSet(viewsets.ModelViewSet):
    lookup_field = "uuid"
    permission_classes = [IsAuthenticated]
    queryset = CentralDeDownload.objects.all()
    serializer_class = CentralDeDownloadSerializer
    pagination_class = DownloadPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = CentralDeDownloadFilter

    def get_queryset(self):
        qs = (
            CentralDeDownload.objects.filter(usuario=self.request.user)
            .all()
            .order_by("-criado_em")
        )

        return qs

    @action(detail=False, methods=["get"], url_path="quantidade-nao-vistos")
    def quantidade_de_nao_vistos(self, request):
        user = self.request.user
        downloads = (
            CentralDeDownload.objects.filter(usuario=user)
            .filter(visto=False)
            .exclude(status=CentralDeDownload.STATUS_EM_PROCESSAMENTO)
            .count()
        )
        data = {"quantidade_nao_vistos": downloads}
        return Response(data)

    @action(detail=False, methods=["put"], url_path="marcar-visto")
    def marcar_como_visto_nao_visto(self, request):
        dado = self.request.data

        try:
            download = CentralDeDownload.objects.filter(uuid=dado["uuid"]).first()
            download.visto = dado["visto"]
            download.save()
        except Exception as err:
            return Response(
                dict(detail=f"Erro ao realizar atualização: {err}"),
                status=status.HTTP_400_BAD_REQUEST,
            )

        resultado = {"mensagem": "Arquivo atualizado com sucesso"}
        status_code = status.HTTP_200_OK

        return Response(resultado, status=status_code)


class SolicitacaoAbertaViewSet(ModelViewSet):
    lookup_field = "id"
    queryset = SolicitacaoAberta.objects.all()
    serializer_class = SolicitacaoAbertaSerializer
    pagination_class = None
