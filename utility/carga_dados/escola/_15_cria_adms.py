from src.perfil.models import Perfil

perfil_diretor_escola, created = Perfil.objects.get_or_create(
    nome="DIRETOR", ativo=True, super_usuario=True
)

perfil_diretor_escola_cei, created = Perfil.objects.get_or_create(
    nome="DIRETOR CEI", ativo=True, super_usuario=True
)

perfil_administrador_escola, created = Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_UE", ativo=True, super_usuario=True
)

perfil_cogestor_dre, created = Perfil.objects.get_or_create(
    nome="COGESTOR_DRE", ativo=True, super_usuario=True
)

perfil_usuario_nutri_codae, created = Perfil.objects.get_or_create(
    nome="COORDENADOR_DIETA_ESPECIAL", ativo=True, super_usuario=True
)

Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_DIETA_ESPECIAL", ativo=True, super_usuario=True
)

perfil_usuario_codae, created = Perfil.objects.get_or_create(
    nome="COORDENADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA", ativo=True, super_usuario=True
)

Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_GESTAO_ALIMENTACAO_TERCEIRIZADA", ativo=True, super_usuario=True
)


Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_EMPRESA", ativo=True, super_usuario=True
)

Perfil.objects.get_or_create(nome="USUARIO_EMPRESA", ativo=True, super_usuario=True)
