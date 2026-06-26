from django.db import models


def ExportModelOperationsMixin(model_name):
    return type(
        f"Export{model_name}OperationsMixin",
        (models.Model,),
        {
            "__module__": "src.dados_comuns.prometheus_mixin",
            "Meta": type("Meta", (), {"abstract": True}),
        },
    )
