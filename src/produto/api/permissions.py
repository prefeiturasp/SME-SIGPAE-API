from rest_framework.permissions import BasePermission

from src.dados_comuns.constants import (
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_MEDICAO,
    ADMINISTRADOR_REPRESENTANTE_CODAE,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COGESTOR_DRE,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    DINUTRE_DIRETORIA,
    ORGAO_FISCALIZADOR,
)
from src.escola.models import Codae, DiretoriaRegional, Escola
from src.terceirizada.models import Terceirizada


PERFIS_CODAE_COM_ACESSO_A_RECLAMACAO = {
    ADMINISTRADOR_CODAE_GABINETE,
    ADMINISTRADOR_GESTAO_PRODUTO,
    ADMINISTRADOR_MEDICAO,
    ADMINISTRADOR_REPRESENTANTE_CODAE,
    ADMINISTRADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_GESTAO_PRODUTO,
    COORDENADOR_SUPERVISAO_NUTRICAO,
    COORDENADOR_SUPERVISAO_NUTRICAO_MANIFESTACAO,
    DINUTRE_DIRETORIA,
    ORGAO_FISCALIZADOR,
}


class PermissaoArquivosHistoricoReclamacao(BasePermission):
    def has_object_permission(self, request, view, obj):
        vinculo = request.user.vinculo_atual
        if not vinculo:
            return False

        instituicao = vinculo.instituicao
        if isinstance(instituicao, Codae):
            return vinculo.perfil.nome in PERFIS_CODAE_COM_ACESSO_A_RECLAMACAO

        if isinstance(instituicao, Escola):
            return obj.escola_id == instituicao.id

        if isinstance(instituicao, DiretoriaRegional):
            return bool(
                vinculo.perfil.nome == COGESTOR_DRE
                and obj.escola_id
                and obj.escola.diretoria_regional_id == instituicao.id
            )

        if isinstance(instituicao, Terceirizada):
            return bool(
                obj.homologacao_produto_id
                and obj.homologacao_produto.rastro_terceirizada_id == instituicao.id
            )

        return False
