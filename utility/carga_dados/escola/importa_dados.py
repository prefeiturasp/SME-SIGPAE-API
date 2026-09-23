from secrets import choice, randbelow

import environ
from django.db.models import Q

from src.cardapio.base.models import TipoAlimentacao
from src.dados_comuns.models import Contato
from src.escola.data.diretorias_regionais import (  # noqa
    data_diretorias_regionais,
)
from src.escola.data.lotes import data_lotes
from src.escola.data.periodo_escolar import data_periodo_escolar
from src.escola.data.subprefeituras import data_subprefeituras
from src.escola.data.tipos_gestao import data_tipos_gestao
from src.escola.models import (
    DiretoriaRegional,
    Escola,
    EscolaPeriodoEscolar,
    Lote,
    PeriodoEscolar,
    Subprefeitura,
    TipoGestao,
    TipoUnidadeEscolar,
)
from src.perfil.models import Perfil, Usuario
from src.terceirizada.data.terceirizadas import data_terceirizadas  # noqa
from src.terceirizada.models import Terceirizada
from utility.carga_dados.escola.helper import (
    bcolors,
    email_valido,
    maiuscula,
    normaliza_nome,
)
from utility.carga_dados.helper import (
    adiciona_m2m_items,
    csv_to_list,
    excel_to_list,
    get_modelo,
    ja_existe,
    le_dados,
    progressbar,
    somente_digitos,
)

from .helper import cria_vinculo_de_perfil_usuario

ROOT_DIR = environ.Path(__file__) - 1


def cria_diretorias_regionais():
    for item in progressbar(data_diretorias_regionais, "Diretoria Regional"):
        obj = DiretoriaRegional.objects.filter(
            codigo_eol=item["codigo_eol"]
        ).first()  # noqa
        if not obj:
            DiretoriaRegional.objects.create(
                nome=item["nome"],
                iniciais=item["iniciais"],
                codigo_eol=item["codigo_eol"],
            )
        else:
            nome = item["nome"]
            print(
                f'{bcolors.FAIL}Aviso: DiretoriaRegional: "{nome}" já existe!{bcolors.ENDC}'
            )  # noqa


def cria_lotes():
    # Possui FK.
    # Monta o dicionário direto da lista de items.
    dict_tipo_gestao = le_dados(data_tipos_gestao, "nome")
    dict_dre = le_dados(data_diretorias_regionais, "codigo_eol")
    dict_terceirizada = le_dados(data_terceirizadas, "cnpj")
    for item in progressbar(data_lotes, "Lote"):
        tipo_gestao = get_modelo(
            modelo=TipoGestao,
            modelo_id=item.get("tipo_gestao"),
            dicionario=dict_tipo_gestao,
            campo_unico="nome",
        )
        diretoria_regional = get_modelo(
            modelo=DiretoriaRegional,
            modelo_id=item.get("diretoria_regional"),
            dicionario=dict_dre,
            campo_unico="codigo_eol",
        )
        terceirizada = get_modelo(
            modelo=Terceirizada,
            modelo_id=item.get("terceirizada"),
            dicionario=dict_terceirizada,
            campo_unico="cnpj",
        )

        data = dict(
            nome=item.get("nome"),
            iniciais=item.get("iniciais"),
            tipo_gestao=tipo_gestao,
            diretoria_regional=diretoria_regional,
            terceirizada=terceirizada,
        )
        _, created = Lote.objects.get_or_create(**data)
        if not created:
            ja_existe("Lote", item["nome"])


def cria_subprefeituras():
    # Possui FK e M2M
    dict_lote = le_dados(data_lotes, "iniciais")
    dict_dre = le_dados(data_diretorias_regionais, "codigo_eol")
    for item in progressbar(data_subprefeituras, "Subprefeitura"):
        # Não tem lote nos dados originais.
        lote = get_modelo(
            modelo=Lote,
            modelo_id=item.get("lote"),
            dicionario=dict_lote,
            campo_unico="iniciais",
        )
        subprefeitura, created = Subprefeitura.objects.get_or_create(
            nome=item["nome"], lote=lote
        )
        if not created:
            ja_existe("Subprefeitura", item["nome"])

        adiciona_m2m_items(
            campo_m2m=subprefeitura.diretoria_regional,
            dicionario_m2m=item.get("diretoria_regional"),
            modelo=DiretoriaRegional,
            dicionario=dict_dre,
            campo_unico="codigo_eol",
        )


def cria_tipos_gestao():
    for item in progressbar(data_tipos_gestao, "Tipo Gestao"):
        _, created = TipoGestao.objects.get_or_create(nome=item["nome"])
        if not created:
            ja_existe("TipoGestao", item["nome"])


def cria_tipo_unidade_escolar(arquivo):
    # Pega somente a coluna 'TIPO DE U.E'
    iniciais = "TIPO DE U.E"
    arquivo = f"{ROOT_DIR}/{arquivo}"
    items = csv_to_list(arquivo)
    items_iniciais = [item[iniciais] for item in items]

    # Procura por todos os itens repetidos no banco,
    # e retorna uma lista de iniciais...
    tipo_unidade_escolares = TipoUnidadeEscolar.objects.filter(
        iniciais__in=items_iniciais
    ).values_list("iniciais", flat=True)

    # E insere somente os itens faltantes.
    itens_faltantes = set(items_iniciais) - set(tipo_unidade_escolares)
    if itens_faltantes:
        for iniciais in progressbar(itens_faltantes, "Tipo Unidade Escolar"):
            TipoUnidadeEscolar.objects.create(iniciais=iniciais)


def cria_contatos_escola(arquivo):
    arquivo = f"{ROOT_DIR}/{arquivo}"
    items = csv_to_list(arquivo)

    for item in progressbar(items, "Contatos Escola"):
        _email = item.get("E-MAIL").strip().lower() or ""
        email = _email if email_valido(_email) else ""

        telefone1 = somente_digitos(item.get("TELEFONE"))
        if 8 < len(telefone1) > 10:
            telefone1 = None
        telefone2 = somente_digitos(item.get("TELEFONE2"))
        if 8 < len(telefone2) > 10:
            telefone2 = None

        if telefone1 or telefone2 or email:
            Contato.objects.get_or_create(
                telefone=telefone1,
                telefone2=telefone2,
                email=email,
            )


def padroniza_dados(items):  # noqa_ C901
    # Tudo Maiusculo + strip
    campos_maiusculos = (
        "EOL",
        "TIPO DE U.E",
        "NOME",
        "DRE",
        "SIGLA/LOTE",
        "ENDEREÇO",
        "Nº",
        "BAIRRO",
        "CEP",
        "EMPRESA",
        "COD. CODAE",
    )
    for item in items:
        for campo in campos_maiusculos:
            item[campo] = maiuscula(item[campo])

    # Tamanho de 6 digitos (zeros a esquerda).
    campos_6_digitos = ("EOL",)
    for item in items:
        for campo in campos_6_digitos:
            item[campo] = item[campo].zfill(6)

    # Normaliza nome.
    campos_normaliza_nomes = (
        "TIPO DE U.E",
        "DRE",
        "ENDEREÇO",
        "BAIRRO",
    )
    for item in items:
        for campo in campos_normaliza_nomes:
            item[campo] = normaliza_nome(item[campo])

    # Somente digitos
    campos_somente_digitos = ("CEP",)
    for item in items:
        for campo in campos_somente_digitos:
            item[campo] = somente_digitos(item[campo])

    return items


def cria_escola(arquivo, legenda):
    lista_auxiliar = []

    arquivo = f"{ROOT_DIR}/{arquivo}"
    items = csv_to_list(arquivo)

    # Padroniza os dados
    items = padroniza_dados(items)

    items_codigo_eol = [item["EOL"] for item in items]

    # Procura por todos os itens repetidos no banco,
    # e retorna uma lista de codigo_eol...
    escolas = Escola.objects.filter(codigo_eol__in=items_codigo_eol).values_list(
        "codigo_eol", flat=True
    )

    # E insere somente os itens faltantes.
    escolas_faltantes = [item for item in items if item["EOL"] not in escolas]
    if escolas_faltantes:
        for item in progressbar(escolas_faltantes, legenda):  # noqa
            # Corrige o nome da DRE
            dre_nome = f"DIRETORIA REGIONAL DE EDUCACAO {item.get('DRE')}"
            tipo_ue_iniciais = item.get("TIPO DE U.E")
            lote_sigla = item.get("SIGLA/LOTE")
            email = item.get("E-MAIL").strip().lower() or ""
            telefone1 = somente_digitos(item.get("TELEFONE"))
            telefone2 = somente_digitos(item.get("TELEFONE2"))

            dre_obj, created_dre = DiretoriaRegional.objects.get_or_create(
                nome=dre_nome
            )  # noqa
            tipo_ue_obj, created_ue = TipoUnidadeEscolar.objects.get_or_create(
                iniciais=tipo_ue_iniciais
            )  # noqa
            tipo_gestao = TipoGestao.objects.get(nome="TERC TOTAL")
            lote_obj = Lote.objects.filter(iniciais=lote_sigla).first() or None
            if telefone1 or telefone2 or email:
                contato_obj = Contato.objects.filter(
                    Q(telefone=telefone1) | Q(telefone2=telefone2) | Q(email=email)
                ).first()

            tipo_ue = item.get("TIPO DE U.E")
            nome = item.get("NOME")
            # Instancia o objeto Escola.
            data = dict(
                nome=f"{tipo_ue} {nome}",
                codigo_eol=item.get("EOL"),
                diretoria_regional=dre_obj,
                tipo_unidade=tipo_ue_obj,
                tipo_gestao=tipo_gestao,
            )
            if lote_obj:
                data["lote"] = lote_obj
            if contato_obj:
                data["contato"] = contato_obj

            escola_obj = Escola(**data)
            lista_auxiliar.append(escola_obj)

        Escola.objects.bulk_create(lista_auxiliar)


def atualiza_tipo_gestao(codigo_eol_escola):
    escola = Escola.objects.get(codigo_eol=codigo_eol_escola)
    tipo_gestao = TipoGestao.objects.get(nome="MISTA")
    escola.tipo_gestao = tipo_gestao
    escola.save()


def cria_periodo_escolar():
    tipos_alimentacao = TipoAlimentacao.objects.all()
    for item in progressbar(data_periodo_escolar, "PeriodoEscolar"):
        periodo_escolar, created = PeriodoEscolar.objects.get_or_create(
            nome=item
        )  # noqa
        for tipo in tipos_alimentacao:
            periodo_escolar.tipos_alimentacao.add(tipo)


def cria_escola_faltante(unidade_escolar, codigo_eol, dre, lote):
    tipo_gestao = TipoGestao.objects.get(nome="TERC TOTAL")
    nome_tipo_unidade = unidade_escolar.split()[0]
    tipo_unidade = TipoUnidadeEscolar.objects.filter(
        iniciais=nome_tipo_unidade
    ).first()  # noqa
    data = Escola.objects.create(
        nome=unidade_escolar,
        codigo_eol=codigo_eol,
        diretoria_regional=dre,
        tipo_unidade=tipo_unidade,
        tipo_gestao=tipo_gestao,
        lote=lote,
    )
    return data


def busca_lote(dre=None, lote=None):
    if lote:
        if lote == "7 A":
            nome = "LOTE 07 A"
        if lote == "7 B":
            nome = "LOTE 07 B"
    if dre:
        dre_obj = DiretoriaRegional.objects.get(iniciais__icontains=dre)
        nome = dre_obj.iniciais.split("-")[-1].strip()
        lote_obj = Lote.objects.filter(iniciais__icontains=nome).first()
    return dre_obj, lote_obj


def _extrai_dados_diretor(item):
    if not item.get("E-MAIL DIRETOR"):
        return None
    email = item.get("E-MAIL DIRETOR").lower().strip()
    if "@" not in email:
        return None
    cpf = somente_digitos(str(item.get("CPF - DIRETOR"))[:11].zfill(11))
    if Usuario.objects.filter(cpf=cpf).first():
        return None
    registro_funcional = somente_digitos(str(item.get("RF - DIRETOR"))[:7])
    if Usuario.objects.filter(registro_funcional=registro_funcional).first():
        return None
    nome = item.get("DIRETOR").strip()
    if nome == "NÃO POSSUI":
        return None
    return {
        "email": email,
        "cpf": cpf,
        "registro_funcional": registro_funcional,
        "nome": nome,
        "codigo_eol": str(item.get("EOL DA U.E")).strip(".0").zfill(6),
        "telefone": somente_digitos(str(item.get("TELEFONE DIRETOR"))[:13]),
    }


def _cria_usuario_diretor_item(dados, perfil_diretor, item):
    email = dados["email"]
    if Usuario.objects.filter(email=email).first():
        print(
            f'{bcolors.FAIL}Aviso: Usuario: "{dados["nome"]}" já existe!{bcolors.ENDC}'
        )
        return
    diretor = Usuario.objects.create_user(
        email=email,
        cpf=dados["cpf"],
        registro_funcional=dados["registro_funcional"],
        nome=dados["nome"],
        cargo="Diretor",
        is_active=False,
        is_staff=False,
        is_superuser=False,
    )
    contato_obj, contato_created = Contato.objects.get_or_create(
        telefone=dados["telefone"],
        telefone2="",
        celular="",
        email=email,
    )

    escola = Escola.objects.filter(codigo_eol=dados["codigo_eol"]).first()
    if escola:
        escola.contato = contato_obj
        escola.save()
    else:
        unidade_escolar = item.get("UNIDADE ESCOLAR")
        dre = item.get("DRE").strip()
        lote = None
        if dre:
            dre, lote = busca_lote(dre=dre)
        escola = cria_escola_faltante(unidade_escolar, dados["codigo_eol"], dre, lote)
        escola.contato = contato_obj
        escola.save()

    cria_vinculo_de_perfil_usuario(
        perfil=perfil_diretor, usuario=diretor, instituicao=escola
    )


def cria_usuario_diretor(arquivo, in_memory=False):
    items = excel_to_list(arquivo, in_memory=in_memory)
    perfil_diretor, created = Perfil.objects.get_or_create(
        nome="DIRETOR_UE", ativo=True, super_usuario=True
    )

    for item in progressbar(items, "Diretores DRE"):
        dados = _extrai_dados_diretor(item)
        if not dados:
            continue
        _cria_usuario_diretor_item(dados, perfil_diretor, item)

    return items


def _extrai_dados_cogestor(item):
    email = item.get("E-MAIL - ASSISTENTE DE DIRETOR").lower().strip()
    if "@" not in email:
        return None
    cpf = None
    if item.get("CPF - ASSISTENTE DE DIRETOR"):
        cpf = somente_digitos(
            str(item.get("CPF - ASSISTENTE DE DIRETOR"))[:11].zfill(11)
        )
    registro_funcional = None
    if item.get("RF - ASSISTENTE DE DIRETOR"):
        registro_funcional = somente_digitos(item.get("RF - ASSISTENTE DE DIRETOR")[:7])
        if Usuario.objects.filter(registro_funcional=registro_funcional).first():
            return None
    nome = item.get("ASSISTENTE DE DIRETOR").strip()
    if nome == "SEM ASSISTENTE":
        return None
    codigo_eol = str(item.get("CÓDIGO EOL DA U.E")).strip(".0").zfill(6)
    return {
        "email": email,
        "cpf": cpf,
        "registro_funcional": registro_funcional,
        "nome": nome,
        "codigo_eol": codigo_eol,
    }


def _cria_usuario_cogestor_item(dados, perfil_diretor, item):
    email = dados["email"]
    if Usuario.objects.filter(email=email).first():
        print(
            f'{bcolors.FAIL}Aviso: Usuario: "{dados["nome"]}" já existe!{bcolors.ENDC}'
        )
        return
    if not dados["cpf"]:
        return
    diretor = Usuario.objects.create_user(
        email=email,
        cpf=dados["cpf"],
        registro_funcional=dados["registro_funcional"],
        nome=dados["nome"],
        cargo="Cogestor",
        is_active=False,
        is_staff=False,
        is_superuser=False,
    )
    escola = Escola.objects.filter(codigo_eol=dados["codigo_eol"]).first()
    if not escola:
        unidade_escolar = item.get("UNIDADE ESCOLAR")
        dre = DiretoriaRegional.objects.filter(nome__icontains="IPIRANGA").first()
        if item.get("LOTE") == "7 B":
            lote = Lote.objects.get(nome="LOTE 07 B")
        else:
            lote = Lote.objects.get(nome="LOTE 07 A")
        cria_escola_faltante(unidade_escolar, dados["codigo_eol"], dre, lote)
    cria_vinculo_de_perfil_usuario(
        perfil=perfil_diretor, usuario=diretor, instituicao=escola
    )


def cria_usuario_cogestor(items):
    """
    Específico: depende dos items de cria_usuario_diretor,
    porque o InMemoryUploadedFile não deu certo aqui.
    """
    perfil_diretor, created = Perfil.objects.get_or_create(
        nome="COGESTOR_DRE", ativo=True, super_usuario=True
    )

    for item in progressbar(items, "Cogestores DRE"):
        dados = _extrai_dados_cogestor(item)
        if not dados:
            continue
        _cria_usuario_cogestor_item(dados, perfil_diretor, item)


def cria_escola_com_periodo_escolar():
    # Percorre todas as escolas e todos os períodos.
    # Deleta tudo antes
    EscolaPeriodoEscolar.objects.all().delete()
    escolas = Escola.objects.all()
    periodos_escolares = PeriodoEscolar.objects.all()
    aux = []
    for escola in progressbar(escolas, "Escola Periodo Escolar"):
        for periodo_escolar in periodos_escolares:
            obj = EscolaPeriodoEscolar(
                escola=escola,
                periodo_escolar=periodo_escolar,
                quantidade_alunos=randbelow(401) + 100,
                horas_atendimento=choice([4, 8, 12]),
            )
            aux.append(obj)
    EscolaPeriodoEscolar.objects.bulk_create(aux)
