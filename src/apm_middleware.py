from elasticapm.contrib.django.apps import (
    _request_started_handler,
    _should_start_transaction,
)


class APMEnsureTransactionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from elasticapm.contrib.django.client import get_client

        client = get_client()
        if client and _should_start_transaction(client):
            scope = getattr(request, "scope", None)
            if scope:
                _request_started_handler(client, sender=None, scope=scope)
            else:
                environ = getattr(request, "environ", None)
                if environ:
                    _request_started_handler(client, sender=None, environ=environ)

        response = self.get_response(request)

        if client and _should_start_transaction(client):
            client.end_transaction()

        return response
