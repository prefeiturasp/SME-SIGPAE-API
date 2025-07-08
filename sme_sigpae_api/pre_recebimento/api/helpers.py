from sme_sigpae_api.dados_comuns.fluxo_status import (
    CronogramaWorkflow,
    FichaTecnicaDoProdutoWorkflow,
)
from sme_sigpae_api.dados_comuns.utils import (
    convert_base64_to_contentfile,
    update_instance_from_dict,
)
from sme_sigpae_api.pre_recebimento.models import (
    AnaliseFichaTecnica,
    ArquivoDoTipoDeDocumento,
    DataDeFabricaoEPrazo,
    EtapasDoCronograma,
    FichaTecnicaDoProduto,
    ImagemDoTipoDeEmbalagem,
    InformacoesNutricionaisFichaTecnica,
    ProgramacaoDoRecebimentoDoCronograma,
    TipoDeDocumentoDeRecebimento,
    TipoDeEmbalagemDeLayout,
)
from sme_sigpae_api.pre_recebimento.models.cronograma import FabricanteFichaTecnica
from sme_sigpae_api.produto.models import InformacaoNutricional


def cria_etapas_de_cronograma(etapas, cronograma=None):
    etapas_criadas = []
    for etapa in etapas:
        etapas_criadas.append(
            EtapasDoCronograma.objects.create(cronograma=cronograma, **etapa)
        )
    return etapas_criadas


def cria_programacao_de_cronograma(programacoes, cronograma=None):
    programacoes_criadas = []
    for programacao in programacoes:
        programacoes_criadas.append(
            ProgramacaoDoRecebimentoDoCronograma.objects.create(
                cronograma=cronograma, **programacao
            )
        )
    return programacoes_criadas


def cria_tipos_de_embalagens(tipos_de_embalagens, layout_de_embalagem=None):
    for embalagem in tipos_de_embalagens:
        imagens = embalagem.pop("imagens_do_tipo_de_embalagem", [])
        tipo_de_embalagem = TipoDeEmbalagemDeLayout.objects.create(
            layout_de_embalagem=layout_de_embalagem, **embalagem
        )
        for img in imagens:
            data = convert_base64_to_contentfile(img.get("arquivo"))
            ImagemDoTipoDeEmbalagem.objects.create(
                tipo_de_embalagem=tipo_de_embalagem,
                arquivo=data,
                nome=img.get("nome", ""),
            )


def cria_tipos_de_documentos(tipos_de_documentos, documento_de_recebimento=None):
    for documento in tipos_de_documentos:
        arquivos = documento.pop("arquivos_do_tipo_de_documento", [])
        tipo_de_documento = TipoDeDocumentoDeRecebimento.objects.create(
            documento_recebimento=documento_de_recebimento, **documento
        )
        for arq in arquivos:
            data = convert_base64_to_contentfile(arq.get("arquivo"))
            ArquivoDoTipoDeDocumento.objects.create(
                tipo_de_documento=tipo_de_documento,
                arquivo=data,
                nome=arq.get("nome", ""),
            )


def cria_datas_e_prazos_doc_recebimento(datas_e_prazos, doc_recebimento):
    datas_criadas = []
    for data in datas_e_prazos:
        datas_criadas.append(
            DataDeFabricaoEPrazo.objects.create(
                documento_recebimento=doc_recebimento, **data
            )
        )
    return datas_criadas


def _cria_fabricante_ficha_tecnica(fabricante_data):
    if not fabricante_data:
        return None

    return FabricanteFichaTecnica.objects.create(**fabricante_data)


def _atualiza_fabricante_ficha_tecnica(ficha_tecnica, fabricante_data, field_name):
    current = getattr(ficha_tecnica, field_name, None)

    if fabricante_data:
        if current:
            for key, value in fabricante_data.items():
                setattr(current, key, value)
            current.save()
        else:
            fabricante = _cria_fabricante_ficha_tecnica(fabricante_data)
            setattr(ficha_tecnica, field_name, fabricante)
            ficha_tecnica.save()
    elif current:
        setattr(ficha_tecnica, field_name, None)
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

    _atualiza_fabricante_ficha_tecnica(ficha_tecnica, fabricante_data, "fabricante")
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


def totalizador_relatorio_cronograma(queryset):
    status_count = {
        CronogramaWorkflow.states[s].title: queryset.filter(status=s).count()
        for s in CronogramaWorkflow.states
    }
    ordered_status_count = dict(
        sorted(status_count.items(), key=lambda e: e[1], reverse=True)
    )
    return ordered_status_count


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
