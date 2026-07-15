from rest_framework import exceptions


class TokenAuthentication:
    keyword = "Token"
    model = None

    def get_model(self):
        if self.model is not None:
            return self.model
        from rest_framework.authtoken.models import Token

        return Token

    def authenticate(self, oWsAcessoModel):
        if oWsAcessoModel is None:
            raise exceptions.AuthenticationFailed(
                "Token inválido. Não foi enviado informações de credenciais."
            )

        if not hasattr(oWsAcessoModel, "StrToken"):
            raise exceptions.AuthenticationFailed(
                "Falha na autenticação. StrToken não foi informado."
            )

        token = oWsAcessoModel.StrToken

        return self.authenticate_credentials(token)

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related("user").get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed("Token inválido.")

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("Usuário inativo ou deletado.")

        return (token.user, token)
