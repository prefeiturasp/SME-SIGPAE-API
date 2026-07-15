from rest_framework import serializers


def contrato_pertence_a_empresa(contrato, empresa):
    """Valida se o contrato pertence à empresa informada.

    Levanta ValidationError se o contrato não pertencer à empresa.
    """
    if contrato not in empresa.contratos.all():
        raise serializers.ValidationError(
            "Contrato deve pertencer a empresa selecionada"
        )
    return True


def valida_parametros_calendario(mes, ano):
    """Valida os parâmetros mês (1-12) e ano (4 dígitos) para consultas de calendário.

    Levanta ValidationError se os parâmetros forem inválidos ou ausentes.
    """
    if not (mes and ano):
        raise serializers.ValidationError(
            "Os parâmetros mes e ano são parametros obrigatórios"
        )

    try:
        mes = int(mes)
        ano = int(ano)

    except ValueError:
        raise serializers.ValidationError(
            "Os parâmetros mes e ano devem ser números inteiros."
        )

    if not (1 <= mes <= 12):
        raise serializers.ValidationError(
            "Informe um mês valido, deve ser um número inteiro entre 1 e 12"
        )

    if len(str(ano)) != 4:
        raise serializers.ValidationError(
            "Informe um ano valido, deve ser um número inteiro de 4 dígitos (Ex.: 2023)"
        )
