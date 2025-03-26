from rest_framework import serializers

from sme_sigpae_api.dados_comuns.fluxo_status import FichaTecnicaDoProdutoWorkflow
from sme_sigpae_api.pre_recebimento.models.cronograma import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
)


def contrato_pertence_a_empresa(contrato, empresa):
    if contrato not in empresa.contratos.all():
        raise serializers.ValidationError(
            "Contrato deve pertencer a empresa selecionada"
        )
    return True


def valida_parametros_calendario(mes, ano):
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


def valida_campos_pereciveis_ficha_tecnica(attrs):
    attrs_obrigatorios_pereciveis = {
        "agroecologico",
        "organico",
        "prazo_validade_descongelamento",
        "temperatura_congelamento",
        "temperatura_veiculo",
        "condicoes_de_transporte",
        "variacao_percentual",
    }

    if not attrs_obrigatorios_pereciveis.issubset(attrs.keys()):
        raise serializers.ValidationError(
            "Fichas Técnicas de Produtos PERECÍVEIS exigem que sejam forncecidos valores para os campos"
            + " agroecologico, organico, prazo_validade_descongelamento, temperatura_congelamento"
            + ", temperatura_veiculo, condicoes_de_transporte e variacao_percentual."
        )


def valida_campos_nao_pereciveis_ficha_tecnica(attrs):
    attrs_obrigatorios_pereciveis = {
        "agroecologico",
        "organico",
        "produto_eh_liquido",
    }

    if not attrs_obrigatorios_pereciveis.issubset(attrs.keys()):
        raise serializers.ValidationError(
            "Fichas Técnicas de Produtos NÃO PERECÍVEIS exigem que sejam forncecidos valores para os campos"
            + " agroecologico, organico, e produto_eh_liquido"
        )


def valida_campos_dependentes_ficha_tecnica(attrs):
    if attrs.get("organico") is True and not attrs.get("mecanismo_controle"):
        raise serializers.ValidationError(
            "É obrigatório fornecer um valor para o atributo mecanismo_controle quando o produto for orgânico."
        )

    valida_ingredientes_alergenicos_ficha_tecnica(attrs)

    if attrs.get("lactose") is True and not attrs.get("lactose_detalhe"):
        raise serializers.ValidationError(
            "É obrigatório fornecer um valor para o atributo lactose_detalhe quando o produto possuir lactose."
        )

    if attrs.get("produto_eh_liquido") is True and (
        not attrs.get("volume_embalagem_primaria")
        or not attrs.get("unidade_medida_volume_primaria")
    ):
        raise serializers.ValidationError(
            "É obrigatório fornecer um valor para os atributos volume_embalagem_primaria e unidade_medida_volume_primaria quando o produto for líquido."
        )


def valida_ingredientes_alergenicos_ficha_tecnica(attrs):
    if attrs.get("alergenicos") is True and not attrs.get("ingredientes_alergenicos"):
        raise serializers.ValidationError(
            "É obrigatório fornecer um valor para o atributo ingredientes_alergenicos quando o produto for alergênico."
        )


class ServiceValidacaoCorrecaoFichaTecnica:
    CAMPOS_OBRIGATORIOS_COMUNS = {
        "informacoes_nutricionais_conferido": {
            "obrigatorios": [
                "porcao",
                "unidade_medida_porcao",
                "valor_unidade_caseira",
                "unidade_medida_caseira",
                "informacoes_nutricionais",
            ]
        },
        "armazenamento_conferido": {
            "obrigatorios": [
                "embalagem_primaria",
                "embalagem_secundaria",
            ]
        },
    }

    CAMPOS_PERECIVEIS = {
        **CAMPOS_OBRIGATORIOS_COMUNS,
        "detalhes_produto_conferido": {
            "obrigatorios": [
                "prazo_validade",
                "agroecologico",
                "organico",
                "componentes_produto",
                "alergenicos",
                "gluten",
                "lactose",
            ],
            "dependentes": [
                "mecanismo_controle",
                "ingredientes_alergenicos",
                "lactose_detalhe",
            ],
        },
        "conservacao_conferido": {
            "obrigatorios": [
                "prazo_validade_descongelamento",
                "condicoes_de_conservacao",
            ]
        },
        "temperatura_e_transporte_conferido": {
            "obrigatorios": [
                "temperatura_congelamento",
                "temperatura_veiculo",
                "condicoes_de_transporte",
            ]
        },
        "embalagem_e_rotulagem_conferido": {
            "obrigatorios": [
                "embalagens_de_acordo_com_anexo",
                "material_embalagem_primaria",
                "peso_liquido_embalagem_primaria",
                "unidade_medida_primaria",
                "peso_liquido_embalagem_secundaria",
                "unidade_medida_secundaria",
                "peso_embalagem_primaria_vazia",
                "unidade_medida_primaria_vazia",
                "peso_embalagem_secundaria_vazia",
                "unidade_medida_secundaria_vazia",
                "sistema_vedacao_embalagem_secundaria",
                "variacao_percentual",
                "rotulo_legivel",
            ]
        },
    }

    CAMPOS_NAO_PERECIVEIS = {
        **CAMPOS_OBRIGATORIOS_COMUNS,
        "detalhes_produto_conferido": {
            "obrigatorios": [
                "prazo_validade",
                "componentes_produto",
                "alergenicos",
                "gluten",
                "lactose",
            ],
            "dependentes": [
                "ingredientes_alergenicos",
                "lactose_detalhe",
            ],
        },
        "conservacao_conferido": {
            "obrigatorios": [
                "condicoes_de_conservacao",
            ]
        },
        "embalagem_e_rotulagem_conferido": {
            "obrigatorios": [
                "embalagens_de_acordo_com_anexo",
                "material_embalagem_primaria",
                "peso_liquido_embalagem_primaria",
                "unidade_medida_primaria",
                "peso_liquido_embalagem_secundaria",
                "unidade_medida_secundaria",
                "peso_embalagem_primaria_vazia",
                "unidade_medida_primaria_vazia",
                "peso_embalagem_secundaria_vazia",
                "unidade_medida_secundaria_vazia",
                "sistema_vedacao_embalagem_secundaria",
                "produto_eh_liquido",
                "rotulo_legivel",
            ],
            "dependentes": [
                "volume_embalagem_primaria",
                "unidade_medida_volume_primaria",
            ],
        },
    }

    CAMPOS_OPCIONAIS_COMUNS = [
        "numero_registro",
    ]

    def __init__(self, ficha_tecnica, attrs) -> None:
        self._ficha_tecnica = ficha_tecnica
        self._attrs = attrs
        self._campos_collapses = self._obter_campos_collapses_por_categoria()
        self._collapses_com_correcao = self._obter_collapses_com_correcao()

    def valida_status_enviada_para_correcao(self):
        status_atual = self._ficha_tecnica.status
        if status_atual != FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO:
            raise serializers.ValidationError(
                {
                    "status": f"Não é possível corrigir uma Ficha no status {status_atual}"
                }
            )

    def valida_campos_obrigatorios_por_collapse(self):
        for collapse in self._collapses_com_correcao:
            campos_obrigatorios_collapse = self._campos_collapses[collapse].get(
                "obrigatorios", []
            )

            for campo in campos_obrigatorios_collapse:
                if campo not in self._attrs:
                    raise serializers.ValidationError(
                        {campo: "Este campo é obrigatório."}
                    )

    def valida_campos_nao_permitidos_por_collapse(self):
        campos_nao_permitidos = {}
        campos_validos = set()

        for collapse in self._collapses_com_correcao:
            self._buscar_campos_nao_permitidos_e_validos_por_collapse(
                collapse, campos_nao_permitidos, campos_validos
            )

        self._remover_campos_validos_dos_nao_permitidos(
            campos_nao_permitidos, campos_validos
        )

        if campos_nao_permitidos:
            raise serializers.ValidationError(campos_nao_permitidos)

    def _buscar_campos_nao_permitidos_e_validos_por_collapse(
        self, collapse, campos_nao_permitidos, campos_validos
    ):
        campos_obrigatorios_collapse = self._campos_collapses[collapse].get(
            "obrigatorios", []
        )

        campos_dependentes_collapse = self._campos_collapses[collapse].get(
            "dependentes", []
        )

        campos_collapse = campos_obrigatorios_collapse + campos_dependentes_collapse + self.CAMPOS_OPCIONAIS_COMUNS

        for attr in self._attrs:
            if attr not in campos_collapse:
                campos_nao_permitidos[
                    attr
                ] = "Este campo não é permitido nesta correção."

            else:
                campos_validos.add(attr)

    def _remover_campos_validos_dos_nao_permitidos(
        self, campos_nao_permitidos, campos_validos
    ):
        for campo in campos_nao_permitidos.copy():
            if campo in campos_validos:
                campos_nao_permitidos.pop(campo)

    def _obter_campos_collapses_por_categoria(self):
        return (
            self.CAMPOS_PERECIVEIS
            if self._ficha_tecnica.categoria
            == FichaTecnicaDoProduto.CATEGORIA_PERECIVEIS
            else self.CAMPOS_NAO_PERECIVEIS
        )

    def _obter_collapses_com_correcao(self):
        analise = (
            AnaliseFichaTecnica.objects.filter(ficha_tecnica=self._ficha_tecnica)
            .order_by("-criado_em")
            .first()
        )

        return [
            campo.name
            for campo in analise._meta.fields
            if (
                campo.name in self._campos_collapses.keys()
                and getattr(analise, campo.name) is False
            )
        ]
