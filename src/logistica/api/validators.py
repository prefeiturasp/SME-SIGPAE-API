from rest_framework.exceptions import ValidationError


def eh_true_ou_false(parametro, nome_parametro):
    if parametro != "true" and parametro != "false":
        raise ValidationError(f"Parametro {nome_parametro} deve ser true ou false.")
    elif parametro == "true":
        return True
    else:
        return False
