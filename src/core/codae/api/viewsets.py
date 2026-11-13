from rest_framework.viewsets import ModelViewSet

from ...api.serializers import CODAESerializer
from ...models import Codae


class CODAESimplesViewSet(ModelViewSet):
    lookup_field = "uuid"
    queryset = Codae.objects.all()
    serializer_class = CODAESerializer
