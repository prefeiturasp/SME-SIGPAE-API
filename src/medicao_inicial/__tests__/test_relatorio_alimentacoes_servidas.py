import datetime
from uuid import uuid4

import pytest
from model_bakery import baker
from rest_framework import status

from src.cardapio.base.models import (
    TipoAlimentacao,
    VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
)
from src.dados_comuns.constants import (
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    DIRETOR_UE,
    TIPOS_GESTAO,
    USUARIO_RELATORIOS,
)
from src.escola.models import GrupoUnidadeEscolar
from src.medicao_inicial.services.relatorio_alimentacoes_servidas import (
    validar_filtros_relatorio_alimentacoes_servidas,
)
from src.terceirizada.models import Terceirizada

pytestmark = pytest.mark.django_db


def _eol():
    return f"{uuid4().int % 900000 + 100000:06d}"


def _usuario(django_user_model, instituicao, perfil_nome):
    sufixo = uuid4().hex[:10]
    email = f"{sufixo}@test.com"
    usuario = django_user_model.objects.create_user(
        username=email,
        password="senha-teste",
        email=email,
        registro_funcional=sufixo[:7],
    )
    perfil = baker.make("Perfil", nome=perfil_nome, ativo=True)
    baker.make(
        "Vinculo",
        usuario=usuario,
        instituicao=instituicao,
        perfil=perfil,
        data_inicial=datetime.date.today(),
        ativo=True,
    )
    return usuario


def _dre(nome):
    return baker.make("DiretoriaRegional", nome=nome)


def _lote(dre, terceirizada, nome):
    return baker.make(
        "Lote", nome=nome, diretoria_regional=dre, terceirizada=terceirizada
    )


def _tipo(iniciais):
    return baker.make("TipoUnidadeEscolar", iniciais=iniciais)


def _escola(dre, lote, tipo, gestao, subprefeitura=None):
    return baker.make(
        "Escola",
        codigo_eol=_eol(),
        nome=f"UE {tipo.iniciais}",
        diretoria_regional=dre,
        lote=lote,
        tipo_unidade=tipo,
        tipo_gestao=gestao,
        subprefeitura=subprefeitura,
    )


def _solicitacao(escola, mes, ano, status_medicao="MEDICAO_APROVADA_PELA_CODAE"):
    return baker.make(
        "SolicitacaoMedicaoInicial",
        escola=escola,
        mes=mes,
        ano=ano,
        status=status_medicao,
    )


def _contrato(terceirizada, lote):
    edital = baker.make(
        "Edital",
        numero=f"ED-{uuid4().hex[:8]}",
        tipo_contratacao="PREGAO",
        processo=f"PROC-{uuid4().hex[:8]}",
        objeto="Alimentacao",
    )
    contrato = baker.make(
        "Contrato",
        numero=f"CT-{uuid4().hex[:8]}",
        processo=f"PROC-{uuid4().hex[:8]}",
        terceirizada=terceirizada,
        edital=edital,
        modalidade=baker.make("Modalidade", nome="Pregão Eletrônico"),
        encerrado=False,
    )
    contrato.lotes.add(lote)
    return contrato


def _base(django_user_model):
    gestao = baker.make("TipoGestao", nome=TIPOS_GESTAO.TERC_TOTAL.value)
    empresa = baker.make("Terceirizada", tipo_servico=Terceirizada.TERCEIRIZADA)
    dre = _dre("DRE IPIRANGA")
    outra_dre = _dre("DRE PENHA")
    lote = _lote(dre, empresa, "LOTE 1")
    lote_alheio = _lote(outra_dre, baker.make("Terceirizada"), "LOTE ALHEIO")
    _contrato(empresa, lote)
    tipo_a = _tipo("CEMEI")
    tipo_b = _tipo("CEU CEMEI")
    tipo_outro_grupo = _tipo("EMEI")
    baker.make(
        "GrupoUnidadeEscolar",
        nome=GrupoUnidadeEscolar.GRUPO_2,
        tipos_unidades=[tipo_a, tipo_b],
    )
    baker.make(
        "GrupoUnidadeEscolar",
        nome=GrupoUnidadeEscolar.GRUPO_3,
        tipos_unidades=[tipo_outro_grupo],
    )
    subprefeitura = baker.make("Subprefeitura", nome="IPIRANGA")
    subprefeitura.diretoria_regional.add(dre)
    sub_alheia = baker.make("Subprefeitura", nome="PENHA")
    sub_alheia.diretoria_regional.add(outra_dre)
    escola = _escola(dre, lote, tipo_a, gestao, subprefeitura)
    _solicitacao(escola, "12", "2023")
    codae = baker.make("Codae")
    usuario = _usuario(
        django_user_model, codae, ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA
    )
    alimentacao = baker.make(TipoAlimentacao, nome="Refeição")
    vinculo = baker.make(
        VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar,
        tipo_unidade_escolar=tipo_a,
        ativo=True,
    )
    vinculo.tipos_alimentacao.add(alimentacao)
    faixa = baker.make("FaixaEtaria", inicio=0, fim=6, ativo=True)
    return {
        "gestao": gestao,
        "empresa": empresa,
        "dre": dre,
        "outra_dre": outra_dre,
        "lote": lote,
        "lote_alheio": lote_alheio,
        "tipo_a": tipo_a,
        "tipo_b": tipo_b,
        "tipo_outro_grupo": tipo_outro_grupo,
        "subprefeitura": subprefeitura,
        "sub_alheia": sub_alheia,
        "escola": escola,
        "usuario": usuario,
        "alimentacao": alimentacao,
        "faixa": faixa,
    }


def _payload(base, **extras):
    dados = {
        "mes": "12_2023",
        "dres": [str(base["dre"].uuid)],
        "lotes": [],
        "subprefeituras": [],
        "tipos_unidades": [str(base["tipo_a"].uuid)],
        "unidades_educacionais": [],
        "tipos_alimentacao": [],
        "faixas_etarias": [],
        "periodo_lancamento_de": "01/12/2023",
        "periodo_lancamento_ate": "15/12/2023",
    }
    dados.update(extras)
    return dados


def _erros(dados, usuario):
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError) as erro:
        validar_filtros_relatorio_alimentacoes_servidas(dados, usuario)
    return erro.value.detail


def test_validacao_combinacao_valida(django_user_model):
    base = _base(django_user_model)
    dados = _payload(
        base,
        unidades_educacionais=[str(base["escola"].uuid)],
        tipos_alimentacao=[str(base["alimentacao"].uuid)],
        faixas_etarias=[str(base["faixa"].uuid)],
    )

    validado = validar_filtros_relatorio_alimentacoes_servidas(dados, base["usuario"])

    assert validado["mes"] == "12_2023"
    assert validado["dres"] == [base["dre"].uuid]


def test_validacao_terceirizada_respeita_escopo_e_rejeita_fornecedor(django_user_model):
    base = _base(django_user_model)
    usuario = _usuario(django_user_model, base["empresa"], ADMINISTRADOR_EMPRESA)

    erros = _erros(_payload(base, dres=[str(base["outra_dre"].uuid)]), usuario)
    assert "escopo" in str(erros["dres"])

    validado = validar_filtros_relatorio_alimentacoes_servidas(
        _payload(base), usuario
    )
    assert validado["dres"] == [base["dre"].uuid]

    fornecedor = baker.make(
        "Terceirizada", tipo_servico=Terceirizada.FORNECEDOR
    )
    usuario_fornecedor = _usuario(
        django_user_model, fornecedor, ADMINISTRADOR_EMPRESA
    )
    sem_permissao = _erros(_payload(base), usuario_fornecedor)
    assert "permissão" in str(sem_permissao["usuario"])


def test_validacao_rejeita_escola(django_user_model):
    base = _base(django_user_model)
    escola = base["escola"]
    usuario = _usuario(django_user_model, escola, DIRETOR_UE)

    erros = _erros(_payload(base), usuario)

    assert "permissão" in str(erros["usuario"])


def test_validacao_mes_invalido_e_fora_do_escopo(django_user_model):
    base = _base(django_user_model)
    formato = _erros(_payload(base, mes="13_2023"), base["usuario"])
    assert "MM_AAAA" in str(formato["mes"])

    inexistente = _erros(_payload(base, mes="01_2020"), base["usuario"])
    assert "não permitido" in str(inexistente["mes"])


def test_validacao_dre_lote_e_subprefeitura(django_user_model):
    base = _base(django_user_model)
    usuario_dre = _usuario(django_user_model, base["dre"], "COGESTOR_DRE")

    dre_fora = _erros(
        _payload(base, dres=[str(base["outra_dre"].uuid)]), usuario_dre
    )
    assert "escopo" in str(dre_fora["dres"])

    lote_outra_dre = _erros(
        _payload(base, lotes=[str(base["lote_alheio"].uuid)]), base["usuario"]
    )
    assert "Lote" in str(lote_outra_dre["lotes"])

    sub_incompativel = _erros(
        _payload(base, subprefeituras=[str(base["sub_alheia"].uuid)]),
        base["usuario"],
    )
    assert "Subprefeitura" in str(sub_incompativel["subprefeituras"])

    junto_com_lote = _erros(
        _payload(
            base,
            lotes=[str(base["lote"].uuid)],
            subprefeituras=[str(base["subprefeitura"].uuid)],
        ),
        base["usuario"],
    )
    assert "junto com lote" in str(junto_com_lote["subprefeituras"])


def test_validacao_tipos_de_grupos_diferentes_e_subconjunto(django_user_model):
    base = _base(django_user_model)
    diferentes = _erros(
        _payload(
            base,
            tipos_unidades=[
                str(base["tipo_a"].uuid),
                str(base["tipo_outro_grupo"].uuid),
            ],
        ),
        base["usuario"],
    )
    assert "mesmo grupo" in str(diferentes["tipos_unidades"])

    validado = validar_filtros_relatorio_alimentacoes_servidas(
        _payload(base, tipos_unidades=[str(base["tipo_b"].uuid)]),
        base["usuario"],
    )
    assert validado["tipos_unidades"] == [base["tipo_b"].uuid]


def test_validacao_unidade_incompativel(django_user_model):
    base = _base(django_user_model)
    gestao_mista = baker.make("TipoGestao", nome=TIPOS_GESTAO.MISTA.value)
    escola_mista = _escola(
        base["dre"], base["lote"], base["tipo_a"], gestao_mista
    )

    erros = _erros(
        _payload(base, unidades_educacionais=[str(escola_mista.uuid)]),
        base["usuario"],
    )

    assert "incompatível" in str(erros["unidades_educacionais"])


def test_validacao_alimentacao_e_faixa_por_grupo(django_user_model):
    base = _base(django_user_model)
    tipo_cei = _tipo("CEI")
    baker.make(
        "GrupoUnidadeEscolar",
        nome=GrupoUnidadeEscolar.GRUPO_1,
        tipos_unidades=[tipo_cei],
    )
    alimentacao_grupo_1 = _erros(
        _payload(
            base,
            tipos_unidades=[str(tipo_cei.uuid)],
            tipos_alimentacao=[str(base["alimentacao"].uuid)],
            faixas_etarias=[str(base["faixa"].uuid)],
        ),
        base["usuario"],
    )
    assert "Grupo 1" in str(alimentacao_grupo_1["tipos_alimentacao"])

    nao_aplicavel = baker.make(TipoAlimentacao, nome="Nao vinculado")
    erros_aplicavel = _erros(
        _payload(base, tipos_alimentacao=[str(nao_aplicavel.uuid)]),
        base["usuario"],
    )
    assert "não aplicável" in str(erros_aplicavel["tipos_alimentacao"])

    faixa_grupo_1 = validar_filtros_relatorio_alimentacoes_servidas(
        _payload(
            base,
            tipos_unidades=[str(tipo_cei.uuid)],
            faixas_etarias=[str(base["faixa"].uuid)],
        ),
        base["usuario"],
    )
    assert faixa_grupo_1["faixas_etarias"] == [base["faixa"].uuid]

    faixa_grupo_2 = validar_filtros_relatorio_alimentacoes_servidas(
        _payload(base, faixas_etarias=[str(base["faixa"].uuid)]),
        base["usuario"],
    )
    assert faixa_grupo_2["faixas_etarias"] == [base["faixa"].uuid]

    faixa_grupo_3 = _erros(
        _payload(
            base,
            tipos_unidades=[str(base["tipo_outro_grupo"].uuid)],
            faixas_etarias=[str(base["faixa"].uuid)],
        ),
        base["usuario"],
    )
    assert "Grupo 1 ou o Grupo 2" in str(faixa_grupo_3["faixas_etarias"])


def test_validacao_periodo(django_user_model):
    base = _base(django_user_model)
    fora = _erros(
        _payload(
            base,
            periodo_lancamento_de="01/11/2023",
            periodo_lancamento_ate="02/11/2023",
        ),
        base["usuario"],
    )
    assert "não coincide" in str(fora["periodo_lancamento_de"])

    invertido = _erros(
        _payload(
            base,
            periodo_lancamento_de="20/12/2023",
            periodo_lancamento_ate="01/12/2023",
        ),
        base["usuario"],
    )
    assert "anterior" in str(invertido["periodo_lancamento_de"])

    so_de = _erros(
        _payload(base, periodo_lancamento_de="01/12/2023", periodo_lancamento_ate=""),
        base["usuario"],
    )
    assert "juntos" in str(so_de["periodo_lancamento_de"])


def test_meses_anos_escopo_e_parametros_antigos(
    client, django_user_model
):
    base = _base(django_user_model)
    escola_outra = _escola(
        base["outra_dre"],
        base["lote_alheio"],
        base["tipo_a"],
        base["gestao"],
    )
    _solicitacao(escola_outra, "11", "2023")
    _solicitacao(base["escola"], "10", "2023", "MEDICAO_EM_ABERTO_PARA_PREENCHIMENTO_UE")
    recreio = baker.make(
        "RecreioNasFerias",
        titulo="Recreio",
        data_inicio=datetime.date(2023, 1, 1),
        data_fim=datetime.date(2023, 1, 31),
    )
    baker.make(
        "SolicitacaoMedicaoInicial",
        escola=base["escola"],
        mes="01",
        ano="2023",
        status="MEDICAO_APROVADA_PELA_CODAE",
        recreio_nas_ferias=recreio,
    )
    usuario_dre = _usuario(django_user_model, base["dre"], "COGESTOR_DRE")
    client.force_login(usuario_dre)

    resposta = client.get(
        "/medicao-inicial/solicitacao-medicao-inicial/meses-anos/",
        {"eh_relatorio_alimentacoes_servidas": "true"},
    )

    assert resposta.status_code == status.HTTP_200_OK
    pares = {(item["mes"], item["ano"]) for item in resposta.data["results"]}
    assert ("12", "2023") in pares
    assert ("01", "2023") in pares
    assert ("11", "2023") not in pares
    assert ("10", "2023") not in pares

    legado = client.get(
        "/medicao-inicial/solicitacao-medicao-inicial/meses-anos/",
        {"status": "MEDICAO_APROVADA_PELA_CODAE"},
    )
    assert legado.status_code == status.HTTP_200_OK
    pares_legado = {(item["mes"], item["ano"]) for item in legado.data["results"]}
    assert ("10", "2023") not in pares_legado

    adesao = client.get(
        "/medicao-inicial/solicitacao-medicao-inicial/meses-anos/",
        {"eh_relatorio_adesao": "true"},
    )
    assert adesao.status_code == status.HTTP_200_OK
    pares_adesao = {
        (item["mes"], item["ano"], item["recreio_nas_ferias"])
        for item in adesao.data["results"]
    }
    assert all(item[2] is None for item in pares_adesao)


def test_perfil_relatorios_acessa_endpoints_de_filtro(client, django_user_model):
    codae = baker.make("Codae")
    usuario = _usuario(django_user_model, codae, USUARIO_RELATORIOS)
    client.force_login(usuario)
    urls = [
        "/medicao-inicial/solicitacao-medicao-inicial/meses-anos/",
        "/diretorias-regionais-simplissima/",
        "/lotes-simples/",
        "/subprefeituras/",
        "/grupos-unidade-escolar/",
        "/escolas-para-filtros/",
        "/tipos-alimentacao/",
        "/faixas-etarias/",
    ]

    for url in urls:
        resposta = client.get(url)
        assert resposta.status_code == status.HTTP_200_OK, url


def test_escopo_de_dre_e_terceirizada_nos_endpoints(client, django_user_model):
    base = _base(django_user_model)
    usuario_dre = _usuario(django_user_model, base["dre"], "COGESTOR_DRE")
    client.force_login(usuario_dre)

    lotes = client.get(
        "/lotes-simples/",
        {"diretoria_regional__uuid": str(base["outra_dre"].uuid)},
    )
    assert lotes.status_code == status.HTTP_200_OK
    assert lotes.data["results"] == []

    escolas = client.get(
        "/escolas-para-filtros/",
        {"diretoria_regional__uuid": str(base["outra_dre"].uuid)},
    )
    assert escolas.status_code == status.HTTP_200_OK
    assert escolas.data == []

    usuario_empresa = _usuario(
        django_user_model, base["empresa"], ADMINISTRADOR_EMPRESA
    )
    client.force_login(usuario_empresa)
    lotes_empresa = client.get("/lotes-simples/")
    uuids = {item["uuid"] for item in lotes_empresa.data["results"]}
    assert str(base["lote"].uuid) in uuids
    assert str(base["lote_alheio"].uuid) not in uuids


def test_subprefeituras_e_escolas_para_filtros_na_api(client, django_user_model):
    base = _base(django_user_model)
    client.force_login(base["usuario"])

    subprefeituras = client.get(
        "/subprefeituras/",
        {
            "diretoria_regional__uuid[]": [
                str(base["dre"].uuid),
                str(base["outra_dre"].uuid),
            ]
        },
    )
    assert subprefeituras.status_code == status.HTTP_200_OK
    nomes = {item["nome"] for item in subprefeituras.data["results"]}
    assert nomes == {"IPIRANGA", "PENHA"}

    escolas = client.get(
        "/escolas-para-filtros/",
        {
            "tipo_gestao__nome": TIPOS_GESTAO.TERC_TOTAL.value,
            "diretoria_regional__uuid[]": [str(base["dre"].uuid)],
            "lote__uuid[]": [str(base["lote"].uuid)],
            "subprefeitura__uuid[]": [str(base["subprefeitura"].uuid)],
            "tipo_unidade__uuid[]": [str(base["tipo_a"].uuid)],
        },
    )
    assert escolas.status_code == status.HTTP_200_OK
    assert [item["uuid"] for item in escolas.data] == [str(base["escola"].uuid)]
    escola = escolas.data[0]
    assert escola["codigo_eol"] == base["escola"].codigo_eol
    assert escola["diretoria_regional"]["uuid"] == str(base["dre"].uuid)
    assert escola["tipo_unidade"]["iniciais"] == "CEMEI"
    assert escola["lote"]["uuid"] == str(base["lote"].uuid)


def test_tipos_alimentacao_filtra_por_tipo_de_unidade(client, django_user_model):
    base = _base(django_user_model)
    outro = baker.make(TipoAlimentacao, nome="Lanche exclusivo")
    client.force_login(base["usuario"])

    resposta = client.get(
        "/tipos-alimentacao/",
        {"tipo_unidade__uuid[]": [str(base["tipo_a"].uuid)]},
    )

    assert resposta.status_code == status.HTTP_200_OK
    nomes = {item["nome"] for item in resposta.data["results"]}
    assert "Refeição" in nomes
    assert outro.nome not in nomes

    completa = client.get("/tipos-alimentacao/")
    nomes_completos = {item["nome"] for item in completa.data["results"]}
    assert outro.nome in nomes_completos
