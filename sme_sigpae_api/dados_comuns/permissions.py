from rest_framework.permissions import BasePermission

from ..escola.models import Codae, DiretoriaRegional, Escola
from ..medicao_inicial.models import Medicao, SolicitacaoMedicaoInicial
from ..terceirizada.models import Terceirizada
from .constants import (
    ADMINISTRADOR_CODAE_DILOG_CONTABIL,
    ADMINISTRADOR_CODAE_DILOG_JURIDICO,
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_CONTRATOS,
    ADMINISTRADOR_DIETA_ESPECIAL,
    ADMINISTRADOR_EMPRESA,
    ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_MEDICAO,
    ADMINISTRADOR_REPRESENTANTE_CODAE,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    ADMINISTRADOR_UE,
    COGESTOR_DRE,
    COORDENADOR_CODAE_DILOG_LOGISTICA,
    COORDENADOR_DIETA_ESPECIAL,
    COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_LOGISTICA,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    DILOG_ABASTECIMENTO,
    DILOG_CRONOGRAMA,
    DILOG_DIRETORIA,
    DILOG_QUALIDADE,
    DINUTRE_DIRETORIA,
    DIRETA,
    DIRETOR_UE,
    ORGAO_FISCALIZADOR,
    PARCEIRA,
    USUARIO_GTIC_CODAE,
    USUARIO_RELATORIOS,
)


def usuario_eh_nutricodae(user):
    return user.vinculo_atual.perfil.nome in [
        COORDENADOR_DIETA_ESPECIAL,
        ADMINISTRADOR_DIETA_ESPECIAL,
    ]


class UsuarioEscolaTercTotal(BasePermission):
    """Permite acesso a usuários com vinculo a uma Escola."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.instituicao.modulo_gestao == "TERCEIRIZADA"
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE, ADMINISTRADOR_UE]
        )

    """Permite acesso ao objeto se o objeto pertence a essa escola."""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if hasattr(obj, "escola") and hasattr(obj, "rastro_escola"):
            return usuario.vinculo_atual.instituicao in [obj.escola, obj.rastro_escola]
        elif hasattr(obj, "escola"):
            return usuario.vinculo_atual.instituicao == obj.escola
        elif hasattr(obj, "rastro_escola"):
            return usuario.vinculo_atual.instituicao == obj.rastro_escola
        elif isinstance(obj, Medicao):
            return (
                usuario.vinculo_atual.instituicao
                == obj.solicitacao_medicao_inicial.escola
            )
        elif obj.tipo == "Kit Lanche Unificado":
            return (
                usuario.vinculo_atual.instituicao.id
                in obj.escolas_quantidades.all().values_list("escola", flat=True)
            )
        else:
            return False


class UsuarioDiretorEscolaTercTotal(UsuarioEscolaTercTotal):
    """Permite acesso a usuários com vinculo a uma Escola."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.instituicao.modulo_gestao == "TERCEIRIZADA"
            and usuario.vinculo_atual.perfil.nome == DIRETOR_UE
        )


class UsuarioEscolaDiretaParceira(BasePermission):
    """Permite acesso a usuários com vinculo a uma Escola do tipo de gestão Direta ou Parceira."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.instituicao.tipo_gestao.nome in [DIRETA, PARCEIRA]
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE, ADMINISTRADOR_UE]
        )


class UsuarioDiretoriaRegional(BasePermission):
    """Permite acesso a usuários com vinculo a uma Diretoria Regional."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional)
        )

    """Permite acesso ao objeto se o objeto pertence a essa Diretoria Regional."""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        # TODO: ver uma melhor forma de organizar esse try-except
        try:  # solicitacoes normais
            if isinstance(obj, SolicitacaoMedicaoInicial):
                retorno = (
                    usuario.vinculo_atual.instituicao == obj.escola.diretoria_regional
                )
            elif isinstance(obj, Medicao):
                retorno = (
                    usuario.vinculo_atual.instituicao
                    == obj.solicitacao_medicao_inicial.escola.diretoria_regional
                )
            else:
                retorno = usuario.vinculo_atual.instituicao in [
                    obj.escola.diretoria_regional,
                    obj.rastro_dre,
                ]
        except AttributeError:  # solicitacao unificada
            retorno = usuario.vinculo_atual.instituicao in [
                obj.rastro_dre,
                obj.diretoria_regional,
            ]
        return retorno


class UsuarioCODAEGestaoAlimentacao(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Gestão de Alimentação."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_MEDICAO,
            ]
        )


class UsuarioCODAENutriManifestacao(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Nutri Manifestação."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO]
        )


class UsuarioCODAENutriSupervisao(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Nutri Supervisão."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [COORDENADOR_SUPERVISAO_NUTRICAO]
        )


class PermissaoParaVisualizarRelatorioFiscalizacaoNutri(BasePermission):
    PERFIS_PERMITIDOS = [
        COORDENADOR_SUPERVISAO_NUTRICAO,
        COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
        COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
        ADMINISTRADOR_MEDICAO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class UsuarioCODAEDietaEspecial(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Dieta Especial."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [COORDENADOR_DIETA_ESPECIAL, ADMINISTRADOR_DIETA_ESPECIAL]
        )


class UsuarioCODAERelatorios(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Relatórios."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [USUARIO_RELATORIOS]
        )


class UsuarioCODAEGabinete(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Gabinete."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_CODAE_GABINETE]
        )


class UsuarioGticCODAE(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - GTIC."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [USUARIO_GTIC_CODAE]
        )


class UsuarioNutricionista(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Dieta Especial."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_DIETA_ESPECIAL,
                ADMINISTRADOR_DIETA_ESPECIAL,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                ADMINISTRADOR_MEDICAO,
            ]
        )


class UsuarioMedicao(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - MEDICAO."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_MEDICAO
        )


class UsuarioOrgaoFiscalizador(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Orgao Fiscalizador."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [ORGAO_FISCALIZADOR]
        )


class UsuarioCODAEGestaoProduto(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Gestão de Produto."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [COORDENADOR_GESTAO_PRODUTO, ADMINISTRADOR_GESTAO_PRODUTO]
        )


class UsuarioTerceirizada(BasePermission):
    """Permite acesso a usuários com vinculo a uma Terceirizada."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Terceirizada)
        )

    """Permite acesso ao objeto se o objeto pertence a essa Diretoria Regional"""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        # TODO: ver uma melhor forma de organizar esse try-except
        try:  # solicitacoes normais
            retorno = usuario.vinculo_atual.instituicao in [
                obj.escola.lote.terceirizada,
                obj.rastro_terceirizada,
            ]
        except AttributeError:  # solicitacao unificada
            retorno = usuario.vinculo_atual.instituicao == obj.rastro_terceirizada
        return retorno


class UsuarioTerceirizadaProduto(BasePermission):
    """Permite acesso a usuários com vinculo a uma Terceirizada."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Terceirizada)
        )


class PermissaoParaRecuperarObjeto(BasePermission):
    """Permite acesso ao objeto se o objeto pertence ao usuário."""

    def has_object_permission(self, request, view, obj):  # noqa
        usuario = request.user
        if isinstance(usuario.vinculo_atual.instituicao, Escola):
            return usuario.vinculo_atual.instituicao in [obj.escola, obj.rastro_escola]
        elif isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.diretoria_regional,
                obj.rastro_dre,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Codae):
            return usuario.vinculo_atual.perfil.nome in [
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                ADMINISTRADOR_MEDICAO,
                ADMINISTRADOR_CODAE_GABINETE,
                DINUTRE_DIRETORIA,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
            try:  # solicitacoes normais
                retorno = usuario.vinculo_atual.instituicao in [
                    obj.escola.lote.terceirizada,
                    obj.rastro_terceirizada,
                ]
            except AttributeError:  # solicitacao unificada
                retorno = usuario.vinculo_atual.instituicao == obj.rastro_terceirizada
            return retorno


class PermissaoParaRecuperarSolicitacaoUnificada(BasePermission):
    """Permite acesso ao objeto se a solicitação unificada pertence ao usuário."""

    def has_object_permission(self, request, view, obj):  # noqa
        usuario = request.user
        if isinstance(usuario.vinculo_atual.instituicao, Escola):
            return (
                obj.possui_escola_na_solicitacao(usuario.vinculo_atual.instituicao)
                or usuario.vinculo_atual.instituicao in obj.rastro_escolas.all()
            )
        elif isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional):
            return usuario.vinculo_atual.instituicao in [
                obj.diretoria_regional,
                obj.rastro_dre,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Codae):
            return usuario.vinculo_atual.perfil.nome in [
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                ADMINISTRADOR_MEDICAO,
                ADMINISTRADOR_CODAE_GABINETE,
                DINUTRE_DIRETORIA,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
            return usuario.vinculo_atual.instituicao in [
                obj.lote,
                obj.rastro_terceirizada,
            ]


class PermissaoParaRecuperarDietaEspecial(BasePermission):
    """Permite acesso ao objeto se a dieta especial pertence ao usuário."""

    def has_object_permission(self, request, view, obj):  # noqa
        usuario = request.user
        if isinstance(usuario.vinculo_atual.instituicao, Escola):
            return usuario.vinculo_atual.instituicao in [
                obj.escola,
                obj.rastro_escola,
                obj.escola_destino,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.diretoria_regional,
                obj.rastro_dre,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Codae):
            return usuario.vinculo_atual.perfil.nome in [
                COORDENADOR_DIETA_ESPECIAL,
                ADMINISTRADOR_DIETA_ESPECIAL,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                ADMINISTRADOR_MEDICAO,
                ADMINISTRADOR_CODAE_GABINETE,
                DINUTRE_DIRETORIA,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.lote.terceirizada,
                obj.rastro_terceirizada,
            ]


class PermissaoParaReclamarDeProduto(BasePermission):
    """Permite acesso a usuários com vinculo a uma Escola ou Nutricionistas CODAE."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                isinstance(usuario.vinculo_atual.instituicao, Escola)
                or (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        COORDENADOR_DIETA_ESPECIAL,
                        ADMINISTRADOR_DIETA_ESPECIAL,
                        COORDENADOR_SUPERVISAO_NUTRICAO,
                        ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                    ]
                )
            )
        )


class UsuarioDilog(BasePermission):
    """Permite acesso a usuários DILOG com vinculo a CODAE."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_LOGISTICA,
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                ADMINISTRADOR_CODAE_GABINETE,
            ]
        )


class UsuarioSuperCodae(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Dieta Especial."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
            ]
        )


class UsuarioPodeAlterarVinculo(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
                USUARIO_GTIC_CODAE,
                ADMINISTRADOR_CONTRATOS,
            ]
            or usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_EMPRESA]
        )


class UsuarioPodeFinalizarVinculo(BasePermission):
    """Permite usuário finalizar vínculos e remover outros usuários."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
                COORDENADOR_DIETA_ESPECIAL,
                COORDENADOR_GESTAO_PRODUTO,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                USUARIO_GTIC_CODAE,
                ADMINISTRADOR_CONTRATOS,
            ]
            or isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional)
            and usuario.vinculo_atual.perfil.nome in [COGESTOR_DRE]
            or isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE]
            or isinstance(usuario.vinculo_atual.instituicao, Terceirizada)
            and usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_EMPRESA]
        )


class UsuarioCodaeDilog(BasePermission):
    """Permite acesso a usuários do perfil CODAE DILOG."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [COORDENADOR_CODAE_DILOG_LOGISTICA]
        )


class PermissaoParaCriarUsuarioComCoresso(BasePermission):
    """Permite criar usuários no coresso."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_GESTAO_PRODUTO,
                COORDENADOR_DIETA_ESPECIAL,
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                USUARIO_GTIC_CODAE,
                ADMINISTRADOR_CONTRATOS,
            ]
            or isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE]
            or isinstance(usuario.vinculo_atual.instituicao, Terceirizada)
            and usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_EMPRESA]
        )


class PermissaoParaListarVinculosAtivos(BasePermission):
    """Permite acesso a usuários com vinculo."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome
            in [
                COORDENADOR_GESTAO_PRODUTO,
                COORDENADOR_DIETA_ESPECIAL,
                COORDENADOR_CODAE_DILOG_LOGISTICA,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                ADMINISTRADOR_CODAE_GABINETE,
                DILOG_DIRETORIA,
                USUARIO_GTIC_CODAE,
                ADMINISTRADOR_CONTRATOS,
            ]
            or isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE]
            or isinstance(usuario.vinculo_atual.instituicao, Terceirizada)
            and usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_EMPRESA]
            or isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional)
            and usuario.vinculo_atual.perfil.nome in [COGESTOR_DRE]
        )


class UsuarioDistribuidor(BasePermission):
    """Permite acesso a usuários com vinculo a Distribuidoras."""

    def has_permission(self, request, view):
        usuario = request.user
        return not usuario.is_anonymous and usuario.eh_distribuidor


class UsuarioEscolaAbastecimento(BasePermission):
    """Permite acesso a usuários com vinculo a uma Escola de Abastecimento."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Escola)
            and usuario.vinculo_atual.instituicao.modulo_gestao == "ABASTECIMENTO"
            and usuario.vinculo_atual.perfil.nome in [DIRETOR_UE, ADMINISTRADOR_UE]
        )


class UsuarioDilogOuDistribuidor(BasePermission):
    """Permite acesso a usuários com vinculo a dilogCodae e distribuidor."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                isinstance(usuario.vinculo_atual.instituicao, Codae)
                and usuario.vinculo_atual.perfil.nome
                in [
                    COORDENADOR_LOGISTICA,
                    COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ADMINISTRADOR_CODAE_GABINETE,
                    DILOG_DIRETORIA,
                ]
                or usuario.eh_distribuidor
            )
        )


class UsuarioDilogOuDistribuidorOuEscolaAbastecimento(BasePermission):
    """Acesso permitido a usuários vinculados a uma escola abastecimento ou cordenador dilog ou distibuidor."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        COORDENADOR_LOGISTICA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                        ADMINISTRADOR_CODAE_DILOG_JURIDICO,
                        DILOG_QUALIDADE,
                        DILOG_DIRETORIA,
                    ]
                )
                or usuario.eh_distribuidor
                or (
                    isinstance(usuario.vinculo_atual.instituicao, Escola)
                    and usuario.vinculo_atual.perfil.nome == ADMINISTRADOR_UE
                )
            )
        )


class PermissaoParaListarEntregas(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        COORDENADOR_LOGISTICA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                        COORDENADOR_SUPERVISAO_NUTRICAO,
                        ADMINISTRADOR_CODAE_GABINETE,
                        ADMINISTRADOR_CODAE_DILOG_CONTABIL,
                        ADMINISTRADOR_CODAE_DILOG_JURIDICO,
                        ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                        DILOG_DIRETORIA,
                    ]
                )
                or usuario.eh_distribuidor
                or (isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional))
            )
        )


class PermissaoParaVisualizarCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        DILOG_CRONOGRAMA,
                        DILOG_QUALIDADE,
                        DILOG_DIRETORIA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                        ADMINISTRADOR_CODAE_GABINETE,
                        USUARIO_RELATORIOS,
                        USUARIO_GTIC_CODAE,
                        DILOG_ABASTECIMENTO,
                    ]
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaVisualizarRelatorioCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        DILOG_CRONOGRAMA,
                        USUARIO_RELATORIOS,
                        DILOG_DIRETORIA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                        ADMINISTRADOR_CODAE_GABINETE,
                        USUARIO_GTIC_CODAE,
                        DILOG_ABASTECIMENTO,
                    ]
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaCriarCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]
                )
            )
        )


class PermissaoParaAssinarCronogramaUsuarioFornecedor(BasePermission):
    # Apenas empresas do tipo fornecedor com perfil ADMINISTRADOR_FORNECEDOR podem confirmar
    def has_permission(self, request, view):
        usuario = request.user
        return not usuario.is_anonymous and usuario.eh_fornecedor


class PermissaoParaAssinarCronogramaUsuarioCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome == DILOG_CRONOGRAMA
                )
            )
        )


class UsuarioDinutreDiretoria(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome == DINUTRE_DIRETORIA
                )
            )
        )


class UsuarioDilogAbastecimento(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome == DILOG_ABASTECIMENTO
                )
            )
        )


class PermissaoParaAssinarCronogramaUsuarioDilog(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome == DILOG_DIRETORIA
                )
            )
        )


class PermissaoParaDashboardCronograma(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_DIRETORIA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_ABASTECIMENTO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class PermissaoParaVisualizarCalendarioCronograma(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_CRONOGRAMA,
        DILOG_QUALIDADE,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_DIRETORIA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_ABASTECIMENTO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class PermissaoParaDashboardLayoutEmbalagem(BasePermission):
    PERFIS_PERMITIDOS = [
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_QUALIDADE,
        ADMINISTRADOR_GESTAO_PRODUTO,
        COORDENADOR_GESTAO_PRODUTO,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_DIRETORIA,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class PermissaoParaDashboardDocumentosDeRecebimento(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_DIRETORIA,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class PermissaoParaCadastrarLaboratorio(BasePermission):
    # Apenas DILOG_QUALIDADE tem acesso a tela de cadastro de Laboratórios.
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [DILOG_QUALIDADE, COORDENADOR_CODAE_DILOG_LOGISTICA]
                )
            )
        )


class PermissaoParaCadastrarVisualizarEmbalagem(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        DILOG_QUALIDADE,
                        DILOG_CRONOGRAMA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                )
            )
        )


class PermissaoParaCadastrarVisualizarUnidadesMedida(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        DILOG_QUALIDADE,
                        DILOG_CRONOGRAMA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                )
            )
        )


class PermissaoParaVisualizarUnidadesMedida(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        DILOG_QUALIDADE,
                        DILOG_CRONOGRAMA,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                    or usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_EMPRESA]
                )
            )
        )


class PermissaoParaVisualizarSolicitacoesAlteracaoCronograma(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_DIRETORIA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_ABASTECIMENTO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaDarCienciaAlteracaoCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]
                )
            )
        )


class PermissaoParaCriarSolicitacoesAlteracaoCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [DILOG_CRONOGRAMA, COORDENADOR_CODAE_DILOG_LOGISTICA]
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaListarDashboardSolicitacaoAlteracaoCronograma(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_DIRETORIA,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_ABASTECIMENTO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoParaAnalisarDilogAbastecimentoSolicitacaoAlteracaoCronograma(
    BasePermission
):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in [DILOG_ABASTECIMENTO]
        )


class PermissaoParaAnalisarDilogSolicitacaoAlteracaoCronograma(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in [DILOG_DIRETORIA]
        )


class ViewSetActionPermissionMixin:
    def get_permissions(self):
        """Return the permission classes based on action.

        Look for permission classes in a dict mapping action to
        permission classes array, ie.:

        class MyViewSet(ViewSetActionPermissionMixin, ViewSet):
            ...
            permission_classes = [AllowAny]
            permission_action_classes = {
                'list': [IsAuthenticated]
                'create': [IsAdminUser]
                'my_action': [MyCustomPermission]
            }

            @action(...)
            def my_action:
                ...

        If there is no action in the dict mapping, then the default
        permission_classes is returned. If a custom action has its
        permission_classes defined in the action decorator, then that
        supercedes the value defined in the dict mapping.
        """
        try:
            return [
                permission()
                for permission in self.permission_action_classes[self.action]
            ]
        except KeyError:
            if self.action:
                action_func = getattr(self, self.action, {})
                action_func_kwargs = getattr(action_func, "kwargs", {})
                permission_classes = action_func_kwargs.get("permission_classes")
            else:
                permission_classes = None

            return [
                permission()
                for permission in (permission_classes or self.permission_classes)
            ]


class PermissaoRelatorioDietasEspeciais(BasePermission):
    """Permite acesso ao objeto se a dieta especial pertence ao usuário."""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.diretoria_regional,
                obj.rastro_dre,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Codae):
            return usuario.vinculo_atual.perfil.nome in [
                COORDENADOR_DIETA_ESPECIAL,
                ADMINISTRADOR_DIETA_ESPECIAL,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                ADMINISTRADOR_MEDICAO,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.lote.terceirizada,
                obj.rastro_terceirizada,
            ]


class PermissaoParaVisualizarGuiasComOcorrencias(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        ADMINISTRADOR_CODAE_DILOG_JURIDICO,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                        COORDENADOR_LOGISTICA,
                        ADMINISTRADOR_CODAE_GABINETE,
                        DILOG_DIRETORIA,
                    ]
                )
            )
        )


class PermissaoParaCriarNotificacaoDeGuiasComOcorrencias(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome
                    in [
                        ADMINISTRADOR_CODAE_DILOG_JURIDICO,
                        COORDENADOR_CODAE_DILOG_LOGISTICA,
                    ]
                )
            )
        )


class UsuarioEhFornecedor(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return not usuario.is_anonymous and usuario.eh_fornecedor


class PermissaoParaVisualizarLayoutDeEmbalagem(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        ADMINISTRADOR_GESTAO_PRODUTO,
        COORDENADOR_GESTAO_PRODUTO,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_DIRETORIA,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaVisualizarDocumentosDeRecebimento(BasePermission):
    PERFIS_PERMITIDOS = [
        DILOG_QUALIDADE,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        DILOG_CRONOGRAMA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_DIRETORIA,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
                or usuario.eh_fornecedor
            )
        )


class UsuarioEhDilogQualidade(BasePermission):
    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome == DILOG_QUALIDADE
                )
            )
        )


class PermissaoParaDashboardFichaTecnica(BasePermission):
    PERFIS_PERMITIDOS = [
        COORDENADOR_GESTAO_PRODUTO,
        ADMINISTRADOR_GESTAO_PRODUTO,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_DIRETORIA,
        DILOG_QUALIDADE,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
            )
        )


class PermissaoParaVisualizarFichaTecnica(BasePermission):
    PERFIS_PERMITIDOS = [
        ADMINISTRADOR_GESTAO_PRODUTO,
        COORDENADOR_GESTAO_PRODUTO,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        ADMINISTRADOR_CODAE_GABINETE,
        DILOG_CRONOGRAMA,
        DILOG_DIRETORIA,
        DILOG_QUALIDADE,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and (
                (
                    isinstance(usuario.vinculo_atual.instituicao, Codae)
                    and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
                )
                or usuario.eh_fornecedor
            )
        )


class PermissaoParaAnalisarFichaTecnica(BasePermission):
    PERFIS_PERMITIDOS = [
        COORDENADOR_GESTAO_PRODUTO,
        COORDENADOR_CODAE_DILOG_LOGISTICA,
        ADMINISTRADOR_GESTAO_PRODUTO,
    ]

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and usuario.vinculo_atual.perfil.nome in self.PERFIS_PERMITIDOS
        )


class PermissaoObjetoFormularioSupervisao(BasePermission):
    """Permite acesso ao objeto se o objeto pertence ao usuário."""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        return obj.formulario_base.usuario == usuario


class UsuarioAdministradorContratos(BasePermission):
    """Permite acesso a usuários com vinculo a CODAE - Administrador Contratos."""

    def has_permission(self, request, view):
        usuario = request.user
        return (
            not usuario.is_anonymous
            and usuario.vinculo_atual
            and isinstance(usuario.vinculo_atual.instituicao, Codae)
            and usuario.vinculo_atual.perfil.nome in [ADMINISTRADOR_CONTRATOS]
        )


class PermissaoHistoricoDietasEspeciais(BasePermission):
    """Permite acesso ao objeto se a dieta especial pertence ao usuário."""

    def has_object_permission(self, request, view, obj):
        usuario = request.user
        if isinstance(usuario.vinculo_atual.instituicao, DiretoriaRegional):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.diretoria_regional,
                obj.rastro_dre,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Codae):
            return usuario.vinculo_atual.perfil.nome in [
                ADMINISTRADOR_MEDICAO,
                COORDENADOR_DIETA_ESPECIAL,
                ADMINISTRADOR_DIETA_ESPECIAL,
                COORDENADOR_SUPERVISAO_NUTRICAO,
                ADMINISTRADOR_SUPERVISAO_NUTRICAO,
                COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
                USUARIO_RELATORIOS,
                COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA,
                ADMINISTRADOR_CODAE_GABINETE,
                DINUTRE_DIRETORIA,
                ADMINISTRADOR_REPRESENTANTE_CODAE,
            ]
        elif isinstance(usuario.vinculo_atual.instituicao, Terceirizada):
            return usuario.vinculo_atual.instituicao in [
                obj.escola.lote.terceirizada,
                obj.rastro_terceirizada,
            ]
