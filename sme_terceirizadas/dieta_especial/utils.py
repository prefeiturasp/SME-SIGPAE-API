from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination

from sme_terceirizadas.eol_servico.utils import EOLException, EOLServicoSGP
from sme_terceirizadas.perfil.models import Perfil, Usuario, Vinculo
from sme_terceirizadas.relatorios.relatorios import relatorio_dieta_especial_conteudo
from sme_terceirizadas.relatorios.utils import html_to_pdf_email_anexo

from ..dados_comuns.constants import TIPO_SOLICITACAO_DIETA
from ..dados_comuns.fluxo_status import DietaEspecialWorkflow
from ..dados_comuns.utils import envia_email_unico, envia_email_unico_com_anexo_inmemory
from ..escola.models import Aluno, Escola
from ..paineis_consolidados.models import SolicitacoesCODAE
from .models import LogDietasAtivasCanceladasAutomaticamente, SolicitacaoDietaEspecial


def dietas_especiais_a_terminar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_termino__lt=date.today(),
        ativo=True,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO
        ]
    )


def termina_dietas_especiais(usuario):
    for solicitacao in dietas_especiais_a_terminar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get('ALTERACAO_UE'):
            solicitacao.dieta_alterada.ativo = True
            solicitacao.dieta_alterada.save()
        solicitacao.termina(usuario)


def dietas_especiais_a_iniciar():
    return SolicitacaoDietaEspecial.objects.filter(
        data_inicio__lte=date.today(),
        ativo=False,
        status__in=[
            DietaEspecialWorkflow.CODAE_AUTORIZADO,
            DietaEspecialWorkflow.TERCEIRIZADA_TOMOU_CIENCIA,
            DietaEspecialWorkflow.ESCOLA_SOLICITOU_INATIVACAO
        ]
    )


def inicia_dietas_temporarias(usuario):
    for solicitacao in dietas_especiais_a_iniciar():
        if solicitacao.tipo_solicitacao == TIPO_SOLICITACAO_DIETA.get('ALTERACAO_UE'):
            solicitacao.dieta_alterada.ativo = False
            solicitacao.dieta_alterada.save()
        solicitacao.ativo = True
        solicitacao.save()


def get_aluno_eol(codigo_eol_aluno):
    try:
        dados_do_aluno = EOLServicoSGP.get_aluno_eol(codigo_eol_aluno)
        return dados_do_aluno
    except EOLException:
        return {}


def lista_valida(dados_do_aluno):
    if(type(dados_do_aluno) == list and len(dados_do_aluno) > 0):
        return True
    else:
        return False


def tem_matricula_ativa(matriculas, codigo_eol):
    resultado = False
    for matricula in matriculas:
        if(matricula['codigoEscola'] == codigo_eol and matricula['situacaoMatricula'] == 'Ativo'):
            resultado = True
            break
    return resultado


def aluno_pertence_a_escola_ou_esta_na_rede(cod_escola_no_eol, cod_escola_no_sigpae) -> bool:
    return cod_escola_no_eol == cod_escola_no_sigpae


def gerar_log_dietas_ativas_canceladas_automaticamente(dieta, dados, fora_da_rede=False):
    data = dict(
        dieta=dieta,
        codigo_eol_aluno=dados['codigo_eol_aluno'],
        nome_aluno=dados['nome_aluno'],
        codigo_eol_escola_destino=dados.get('codigo_eol_escola_origem'),
        nome_escola_destino=dados.get('nome_escola_origem'),
        codigo_eol_escola_origem=dados.get('codigo_eol_escola_destino'),
        nome_escola_origem=dados.get('nome_escola_destino'),
    )
    if fora_da_rede:
        data['codigo_eol_escola_origem'] = dados.get('codigo_eol_escola_origem')
        data['nome_escola_origem'] = dados.get('nome_escola_origem')
        data['codigo_eol_escola_destino'] = ''
        data['nome_escola_destino'] = ''
    LogDietasAtivasCanceladasAutomaticamente.objects.create(**data)


def _cancelar_dieta(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_mudou_escola(user=usuario_admin)
    dieta.ativo = False
    dieta.save()


def _cancelar_dieta_aluno_fora_da_rede(dieta):
    usuario_admin = Usuario.objects.get(pk=1)
    dieta.cancelar_aluno_nao_pertence_rede(user=usuario_admin)
    dieta.ativo = False
    dieta.save()


def enviar_email_para_diretor_da_escola_origem(solicitacao_dieta, aluno, escola):  # noqa C901
    assunto = f'Cancelamento Automático de Dieta Especial Nº {solicitacao_dieta.id_externo}'
    perfil = Perfil.objects.get(nome='DIRETOR')
    ct = ContentType.objects.get_for_model(escola)
    vinculos = Vinculo.objects.filter(perfil=perfil, content_type=ct, object_id=escola.pk)

    # E-mail do Diretor da Escola.
    # Pode ter mais de um Diretor?
    emails = []
    for vinculo in vinculos:
        email = vinculo.usuario.email
        emails.append(email)

    hoje = date.today().strftime('%d/%m/%Y')

    template = 'email/email_dieta_cancelada_automaticamente_escola_origem.html',
    dados_template = {
        'nome_aluno': aluno.nome,
        'codigo_eol_aluno': aluno.codigo_eol,
        'dieta_numero': solicitacao_dieta.id_externo,
        'nome_escola': escola.nome,
        'hoje': hoje,
    }
    html = render_to_string(template, dados_template)

    # Pega o email da Terceirizada
    vinculos_terc = escola.lote.terceirizada.vinculos.all()
    for vinculo in vinculos_terc:
        if vinculo.usuario:
            emails.append(vinculo.usuario.email)

    # Parece que está previsto ter mais Diretores vinculados a mesma escola.
    for email in emails:
        envia_email_unico(
            assunto=assunto,
            corpo='',
            email=email,
            template=template,
            dados_template=dados_template,
            html=html,
        )


def enviar_email_para_escola_origem_eol(solicitacao_dieta, aluno, escola):
    assunto = 'Alerta para Criar uma Nova Dieta Especial'

    email_escola_origem_eol = escola.escola_destino.contato.email

    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f'dieta_especial_{aluno.codigo_eol}.pdf'
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name='email/email_dieta_cancelada_automaticamente_escola_destino.html',
        context={
            'nome_aluno': aluno.nome,
            'codigo_eol_aluno': aluno.codigo_eol,
            'nome_escola': escola.nome,
        }
    )

    envia_email_unico_com_anexo_inmemory(
        assunto=assunto,
        corpo=corpo,
        email=email_escola_origem_eol,
        anexo_nome=anexo_nome,
        mimetypes='application/pdf',
        anexo=anexo,
    )


def enviar_email_para_escola_destino_eol(solicitacao_dieta, aluno, escola):
    assunto = 'Alerta para Criar uma Nova Dieta Especial'

    email_escola_destino_eol = escola.escola_destino.contato.email

    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f'dieta_especial_{aluno.codigo_eol}.pdf'
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name='email/email_dieta_cancelada_automaticamente_escola_destino.html',
        context={
            'nome_aluno': aluno.nome,
            'codigo_eol_aluno': aluno.codigo_eol,
            'nome_escola': escola.nome,
        }
    )

    envia_email_unico_com_anexo_inmemory(
        assunto=assunto,
        corpo=corpo,
        email=email_escola_destino_eol,
        anexo_nome=anexo_nome,
        mimetypes='application/pdf',
        anexo=anexo,
    )


def enviar_email_para_diretor_da_escola_destino(solicitacao_dieta, aluno, escola):
    assunto = 'Alerta para Criar uma Nova Dieta Especial'
    perfil = Perfil.objects.get(nome='DIRETOR')
    ct = ContentType.objects.get_for_model(escola)
    vinculos = Vinculo.objects.filter(perfil=perfil, content_type=ct, object_id=escola.pk)

    # E-mail do Diretor da Escola.
    # Pode ter mais de um Diretor?
    emails = []
    for vinculo in vinculos:
        email = vinculo.usuario.email
        emails.append(email)

    html_string = relatorio_dieta_especial_conteudo(solicitacao_dieta)
    anexo = html_to_pdf_email_anexo(html_string)
    anexo_nome = f'dieta_especial_{aluno.codigo_eol}.pdf'
    html_to_pdf_email_anexo(html_string)

    corpo = render_to_string(
        template_name='email/email_dieta_cancelada_automaticamente_escola_destino.html',
        context={
            'nome_aluno': aluno.nome,
            'codigo_eol_aluno': aluno.codigo_eol,
            'nome_escola': escola.nome,
        }
    )

    # Parece que está previsto ter mais Diretores vinculados a mesma escola.
    for email in emails:
        envia_email_unico_com_anexo_inmemory(
            assunto=assunto,
            corpo=corpo,
            email=email,
            anexo_nome=anexo_nome,
            mimetypes='application/pdf',
            anexo=anexo,
        )


def cancela_dietas_ativas_automaticamente():  # noqa C901 D205 D400
    """Se um aluno trocar de escola ou não pertencer a rede
    e se tiver uma Dieta Especial Ativa, essa dieta será cancelada automaticamente.
    """
    dietas_ativas_comuns = SolicitacoesCODAE.get_autorizados_dieta_especial().filter(
        tipo_solicitacao_dieta='COMUM').order_by('pk').distinct('pk')
    for dieta in dietas_ativas_comuns:
        aluno = Aluno.objects.get(codigo_eol=dieta.codigo_eol_aluno)
        dados_do_aluno = get_aluno_eol(dieta.codigo_eol_aluno)
        solicitacao_dieta = SolicitacaoDietaEspecial.objects.filter(pk=dieta.pk).first()

        # Condições:
        # retorno do EOL é uma lista
        # lista não está vazia
        # última matrícula  registrada é do ano atual

        if(lista_valida(dados_do_aluno) and
                tem_matricula_ativa(dados_do_aluno, solicitacao_dieta.escola.codigo_eol)):
            if aluno.escola:
                cod_escola_no_sigpae = aluno.escola.codigo_eol
            else:
                cod_escola_no_sigpae = None
            # Retorna True ou False
            resposta = aluno_pertence_a_escola_ou_esta_na_rede(
                cod_escola_no_eol=solicitacao_dieta.escola.codigo_eol,
                cod_escola_no_sigpae=cod_escola_no_sigpae
            )
            escola_existe_no_sigpae = Escola.objects.filter(codigo_eol=solicitacao_dieta.escola.codigo_eol).first()

            nome_escola_destino = None
            if escola_existe_no_sigpae:
                nome_escola_destino = escola_existe_no_sigpae.nome

            dados = dict(
                codigo_eol_aluno=dieta.codigo_eol_aluno,
                nome_aluno=aluno.nome,
                codigo_eol_escola_destino=solicitacao_dieta.escola.codigo_eol,
                nome_escola_destino=nome_escola_destino,
            )
            if cod_escola_no_sigpae:
                dados['nome_escola_origem'] = aluno.escola.nome
                dados['codigo_eol_escola_origem'] = aluno.escola.codigo_eol

            if not resposta:
                gerar_log_dietas_ativas_canceladas_automaticamente(solicitacao_dieta, dados)
                # Cancelar Dieta
                _cancelar_dieta(solicitacao_dieta)

                if escola_existe_no_sigpae:
                    # Envia email pra escola Origem.
                    escola_origem = escola_existe_no_sigpae
                    enviar_email_para_diretor_da_escola_origem(solicitacao_dieta, aluno, escola=escola_origem)

                    # Envia email pra escola Destino.
                    # Parece que está invertido, mas está certo.
                    escola_destino = aluno.escola
                    enviar_email_para_diretor_da_escola_destino(solicitacao_dieta, aluno, escola=escola_destino)
        else:
            # Aluno não pertence a rede municipal.
            # Inverte escola origem.
            dados = dict(
                codigo_eol_aluno=dieta.codigo_eol_aluno,
                nome_aluno=aluno.nome,
                codigo_eol_escola_origem=aluno.escola.codigo_eol,
                nome_escola_origem=aluno.escola.nome,
            )
            gerar_log_dietas_ativas_canceladas_automaticamente(solicitacao_dieta, dados, fora_da_rede=True)
            _cancelar_dieta_aluno_fora_da_rede(dieta=solicitacao_dieta)


class RelatorioPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProtocoloPadraoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


def log_create(protocolo_padrao, user=None):
    import json
    from datetime import datetime

    historico = {}

    historico['created_at'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    historico['user'] = {'uuid': str(user.uuid), 'email': user.email} if user else user
    historico['action'] = 'CREATE'

    substituicoes = []
    for substituicao in protocolo_padrao.substituicoes.all():
        alimentos_substitutos = [
            {'uuid': str(sub.uuid), 'nome': sub.nome}
            for sub in substituicao.alimentos_substitutos.all()]
        subs = [
            {'uuid': str(sub.uuid), 'nome': sub.nome}
            for sub in substituicao.substitutos.all()]

        substitutos = [*alimentos_substitutos, *subs]
        substituicoes.append({
            'tipo': {'from': None, 'to': substituicao.tipo},
            'alimento': {'from': None, 'to': {'id': substituicao.alimento.id, 'nome': substituicao.alimento.nome}},
            'substitutos': {'from': None, 'to': substitutos}
        })

    historico['changes'] = [
        {'field': 'criado_em', 'from': None, 'to': protocolo_padrao.criado_em.strftime('%Y-%m-%d %H:%M:%S')},
        {'field': 'id', 'from': None, 'to': protocolo_padrao.id},
        {'field': 'nome_protocolo', 'from': None, 'to': protocolo_padrao.nome_protocolo},
        {'field': 'orientacoes_gerais', 'from': None, 'to': protocolo_padrao.orientacoes_gerais},
        {'field': 'status', 'from': None, 'to': protocolo_padrao.status},
        {'field': 'uuid', 'from': None, 'to': str(protocolo_padrao.uuid)},
        {'field': 'substituicoes', 'changes': substituicoes},
    ]

    protocolo_padrao.historico = json.dumps([historico])
    protocolo_padrao.save()


def log_update(instance, validated_data, substituicoes_old, substituicoes_new, user=None):
    import json
    from datetime import datetime
    historico = {}
    changes = diff_protocolo_padrao(instance, validated_data)
    changes_subs = diff_substituicoes(substituicoes_old, substituicoes_new)

    if changes_subs:
        changes.append({'field': 'substituicoes', 'changes': changes_subs})

    if changes:
        historico['updated_at'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        historico['user'] = {'uuid': str(user.uuid), 'email': user.email} if user else user
        historico['action'] = 'UPDATE'
        historico['changes'] = changes

        hist = json.loads(instance.historico) if instance.historico else []
        hist.append(historico)

        instance.historico = json.dumps(hist)


def diff_protocolo_padrao(instance, validated_data):
    changes = []

    if instance.nome_protocolo != validated_data['nome_protocolo']:
        changes.append(
            {'field': 'nome_protocolo', 'from': instance.nome_protocolo, 'to': validated_data['nome_protocolo']})

    if instance.orientacoes_gerais != validated_data['orientacoes_gerais']:
        changes.append(
            {
                'field': 'orientacoes_gerais',
                'from': instance.orientacoes_gerais,
                'to': validated_data['orientacoes_gerais']
            }
        )

    if instance.status != validated_data['status']:
        changes.append(
            {'field': 'status', 'from': instance.status, 'to': validated_data['status']})

    return changes


def diff_substituicoes(substituicoes_old, substituicoes_new): # noqa C901
    substituicoes = []

    # Tratando adição e edição de substituíções
    if substituicoes_old.all().count() <= len(substituicoes_new):

        for index, subs_new in enumerate(substituicoes_new):
            sub = {}

            try:
                subs = substituicoes_old.all().order_by('id')[index]
            except IndexError:
                subs = None

            if not subs or subs.alimento.id != subs_new['alimento'].id:
                sub['alimento'] = {
                    'from': {
                        'id': subs.alimento.id if subs else None,
                        'nome': subs.alimento.nome if subs else None},
                    'to': {
                        'id': subs_new['alimento'].id,
                        'nome': subs_new['alimento'].nome}}

            if not subs or subs.tipo != subs_new['tipo']:
                sub['tipo'] = {'from': subs.tipo if subs else None, 'to': subs_new['tipo'] if subs_new else None}

            al_subs_ids = subs.alimentos_substitutos.all().order_by('id').values_list('id', flat=True) if subs else []
            subs_ids_old = subs.substitutos.all().order_by('id').values_list('id', flat=True) if subs else []

            ids_olds = [*al_subs_ids, *subs_ids_old]
            ids_news = sorted([s.id for s in subs_new['substitutos']])

            from itertools import zip_longest
            if any(map(lambda t: t[0] != t[1], zip_longest(ids_olds, ids_news, fillvalue=False))):
                from_ = None

                if subs:
                    alimentos_substitutos = [
                        {'uuid': str(sub.uuid), 'nome': sub.nome}
                        for sub in subs.alimentos_substitutos.all()]

                    substitutos_ = [
                        {'uuid': str(sub.uuid), 'nome': sub.nome}
                        for sub in subs.substitutos.all()]

                    substitutos = [*alimentos_substitutos, *substitutos_]
                    from_ = [
                        {'uuid': sub['uuid'], 'nome': sub['nome']}
                        for sub in substitutos] if substitutos else None

                sub['substitutos'] = {
                    'from': from_,
                    'to': [
                        {'uuid': str(s.uuid), 'nome': s.nome}
                        for s in subs_new['substitutos']] if subs_new['substitutos'] else None
                }

            if sub:
                substituicoes.append(sub)

    else:
        # trata a remoção de uma substituíção
        for index, subs in enumerate(substituicoes_old.all()):
            sub = {}
            try:
                subs_new = substituicoes_new[index]
            except IndexError:
                subs_new = None

            if not subs_new or subs.alimento.id != subs_new['alimento'].id:
                sub['alimento'] = {
                    'from': {
                        'id': subs.alimento.id,
                        'nome': subs.alimento.nome
                    },
                    'to': {
                        'id': subs_new['alimento'].id if subs_new else None,
                        'nome': subs_new['alimento'].nome if subs_new else None
                    }
                }

            if not subs_new or subs.tipo != subs_new['tipo']:
                sub['tipo'] = {'from': subs.tipo, 'to': subs_new['tipo'] if subs_new else None}

            al_sub_ids = subs.alimentos_substitutos.all().order_by('id').values_list('id', flat=True) if subs else []
            subs_ids_old = subs.substitutos.all().order_by('id').values_list('id', flat=True) if subs else []

            ids_olds = [*al_sub_ids, *subs_ids_old]
            ids_news = sorted([s.id for s in subs_new['substitutos']]) if subs_new else []

            from itertools import zip_longest
            if any(map(lambda t: t[0] != t[1], zip_longest(ids_olds, ids_news, fillvalue=False))):
                to_ = None
                if subs_new:
                    to_ = [
                        {'uuid': str(s.uuid), 'nome': s.nome}
                        for s in subs_new['substitutos']] if subs_new['substitutos'] else None

                alimentos_substitutos = [
                    {'uuid': str(sub.uuid), 'nome': sub.nome}
                    for sub in subs.alimentos_substitutos.all()]

                substitutos_ = [
                    {'uuid': str(sub.uuid), 'nome': sub.nome}
                    for sub in subs.substitutos.all()]

                substitutos = [*alimentos_substitutos, *substitutos_]

                sub['substitutos'] = {
                    'from': [
                        {'uuid': sub['uuid'], 'nome': sub['nome']}
                        for sub in substitutos] if substitutos else None,
                    'to': to_
                }

            if sub:
                substituicoes.append(sub)

    return substituicoes
