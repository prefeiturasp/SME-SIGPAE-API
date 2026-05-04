class DataSolicitacaoContextMixin:
    context_data_field = "data"

    def get_serializer_context(self):
        context = super().get_serializer_context()

        try:
            obj = self.get_object()
        except Exception:
            return context

        data = getattr(obj, self.context_data_field, None)
        if data:
            context["data"] = data

        return context


class EscolaNomeHistoricoSerializerMixin:
    def get_nome(self, obj) -> str:
        data = self.context.get("data")
        return obj.nome_historico(data) if data else obj.nome
