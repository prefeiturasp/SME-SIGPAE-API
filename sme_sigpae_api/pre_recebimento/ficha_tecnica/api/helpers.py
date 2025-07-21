from sme_sigpae_api.dados_comuns.fluxo_status import (
    FichaTecnicaDoProdutoWorkflow,
)
from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.ficha_tecnica.models import (
    AnaliseFichaTecnica,
    FichaTecnicaDoProduto,
    InformacoesNutricionaisFichaTecnica,
    FabricanteFichaTecnica,
)
from sme_sigpae_api.produto.models import InformacaoNutricional


def _cria_fabricante_ficha_tecnica(fabricante_data):
    if not fabricante_data:
        return None

    return FabricanteFichaTecnica.objects.create(**fabricante_data)


def _atualiza_fabricante_ficha_tecnica(ficha_tecnica, fabricante_data, field_name):
    current = getattr(ficha_tecnica, field_name, None)

    if fabricante_data == {}:
        if current:
            setattr(ficha_tecnica, field_name, None)
            ficha_tecnica.save()
        return

    if current:
        for key, value in fabricante_data.items():
            setattr(current, key, value)
        current.save()
    else:
        fabricante = _cria_fabricante_ficha_tecnica(fabricante_data)
        if fabricante:
            setattr(ficha_tecnica, field_name, fabricante)
            ficha_tecnica.save()


def cria_ficha_tecnica(validated_data):
    dados_informacoes_nutricionais = validated_data.pop("informacoes_nutricionais", [])
    fabricante_data = validated_data.pop("fabricante", None)
    envasador_data = validated_data.pop("envasador_distribuidor", None)

    _converte_arquivo_para_contentfile(validated_data)

    fabricante = (
        _cria_fabricante_ficha_tecnica(fabricante_data) if fabricante_data else None
    )
    envasador = (
        _cria_fabricante_ficha_tecnica(envasador_data) if envasador_data else None
    )

    ficha_tecnica = FichaTecnicaDoProduto.objects.create(
        **validated_data, fabricante=fabricante, envasador_distribuidor=envasador
    )

    if dados_informacoes_nutricionais:
        _cria_informacoes_nutricionais(
            ficha_tecnica,
            dados_informacoes_nutricionais,
        )

    return ficha_tecnica


def atualiza_ficha_tecnica(ficha_tecnica, validated_data):
    dados_informacoes_nutricionais = validated_data.pop("informacoes_nutricionais", [])
    fabricante_data = validated_data.pop("fabricante", None)
    envasador_data = validated_data.pop("envasador_distribuidor", None)

    _converte_arquivo_para_contentfile(validated_data)

    if fabricante_data is not None:
        _atualiza_fabricante_ficha_tecnica(ficha_tecnica, fabricante_data, "fabricante")
    if envasador_data is not None:
        _atualiza_fabricante_ficha_tecnica(
            ficha_tecnica, envasador_data, "envasador_distribuidor"
        )

    if dados_informacoes_nutricionais:
        _cria_informacoes_nutricionais(
            ficha_tecnica,
            dados_informacoes_nutricionais,
            deletar_antigas=True,
        )

    return update_instance_from_dict(ficha_tecnica, validated_data, save=True)


def _converte_arquivo_para_contentfile(validated_data):
    arquivo_base64 = validated_data.pop("arquivo", None)
    if arquivo_base64:
        validated_data["arquivo"] = convert_base64_to_contentfile(arquivo_base64)


def _cria_informacoes_nutricionais(
    ficha_tecnica,
    dados_informacoes_nutricionais,
    deletar_antigas=False,
):
    if deletar_antigas:
        ficha_tecnica.informacoes_nutricionais.all().delete()

    for dados in dados_informacoes_nutricionais:
        informacao_nutricional = InformacaoNutricional.objects.filter(
            uuid=str(dados["informacao_nutricional"])
        ).first()

        InformacoesNutricionaisFichaTecnica.objects.create(
            ficha_tecnica=ficha_tecnica,
            informacao_nutricional=informacao_nutricional,
            quantidade_por_100g=dados["quantidade_por_100g"],
            quantidade_porcao=dados["quantidade_porcao"],
            valor_diario=dados["valor_diario"],
        )


def limpar_campos_dependentes_ficha_tecnica(instance, validated_data):
    if validated_data.get("organico") is False:
        setattr(instance, "mecanismo_controle", "")

    if validated_data.get("alergenicos") is False:
        setattr(instance, "ingredientes_alergenicos", "")

    if validated_data.get("lactose") is False:
        setattr(instance, "lactose_detalhe", "")

    if validated_data.get("produto_eh_liquido") is False:
        setattr(instance, "volume_embalagem_primaria", None)
        setattr(instance, "unidade_medida_volume_primaria", None)

    instance.save()

    return instance


def reseta_analise_atualizacao(analise, payload):
    mapa = {
        "fabricante": "fabricante_envasador_conferido",
        "envasador_distribuidor": "fabricante_envasador_conferido",
        "componentes_produto": "detalhes_produto_conferido",
        "alergenicos": "detalhes_produto_conferido",
        "ingredientes_alergenicos": "detalhes_produto_conferido",
        "gluten": "detalhes_produto_conferido",
        "porcao": "informacoes_nutricionais_conferido",
        "unidade_medida_porcao": "informacoes_nutricionais_conferido",
        "valor_unidade_caseira": "informacoes_nutricionais_conferido",
        "unidade_medida_caseira": "informacoes_nutricionais_conferido",
        "informacoes_nutricionais": "informacoes_nutricionais_conferido",
        "condicoes_de_conservacao": "conservacao_conferido",
        "embalagem_primaria": "armazenamento_conferido",
        "embalagem_secundaria": "armazenamento_conferido",
        "nome_responsavel_tecnico": "responsavel_tecnico_conferido",
        "habilitacao": "responsavel_tecnico_conferido",
        "numero_registro_orgao": "responsavel_tecnico_conferido",
        "arquivo": "responsavel_tecnico_conferido",
        "modo_de_preparo": "modo_preparo_conferido",
        "informacoes_adicionais": "outras_informacoes_conferido",
    }

    for key in mapa.keys():
        if key in payload:
            setattr(analise, mapa[key], False)

    return analise


def gerar_nova_analise_ficha_tecnica(ficha_tecnica, payload=None):
    analise_antiga = ficha_tecnica.analises.last()
    if payload:
        analise_antiga = reseta_analise_atualizacao(analise_antiga, payload)

    campos = AnaliseFichaTecnica._meta.fields
    valores_antigos = {}

    for campo in [c.name for c in campos if c.name.endswith("_conferido")]:
        if getattr(analise_antiga, campo) is True:
            valores_antigos[campo] = True

    for campo in [c.name for c in campos if c.name.endswith("_correcoes")]:
        campo_conferido = campo.replace("_correcoes", "_conferido")
        if getattr(analise_antiga, campo_conferido) is False:
            valores_antigos[campo] = getattr(analise_antiga, campo)

    AnaliseFichaTecnica.objects.create(
        criado_por=analise_antiga.criado_por,
        ficha_tecnica=ficha_tecnica,
        **valores_antigos,
    )


def retorna_status_ficha_tecnica(status):
    nomes_status = FichaTecnicaDoProdutoWorkflow.states

    aprovada = FichaTecnicaDoProdutoWorkflow.APROVADA
    enviada_analise = FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_ANALISE
    enviada_correcao = FichaTecnicaDoProdutoWorkflow.ENVIADA_PARA_CORRECAO

    switcher = {
        aprovada: nomes_status[aprovada],
        enviada_analise: nomes_status[enviada_analise],
        enviada_correcao: nomes_status[enviada_correcao],
    }

    state = switcher.get(status, "Status Inválido")
    if isinstance(state, str):
        return state
    else:
        return state.title


def formata_cnpj_ficha_tecnica(cnpj):
    cnpj = "".join(filter(str.isdigit, str(cnpj)))
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def formata_telefone_ficha_tecnica(telefone):
    telefone = "".join(filter(str.isdigit, str(telefone)))
    if len(telefone) < 10:
        return telefone
    if len(telefone) == 10:
        return f"{telefone[:2]} {telefone[2:6]} {telefone[6:]}"
    elif len(telefone) == 11:
        return f"{telefone[:2]} {telefone[2:7]} {telefone[7:]}"
    return telefone
