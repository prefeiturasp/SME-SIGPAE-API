import datetime

from src.escola.models import Codae, DiretoriaRegional, Escola
from src.perfil.models import Perfil, Usuario, Vinculo

data_atual = datetime.date.today()

# DEV

usuario_escola = Usuario.objects.get(email="escola@admin.com")
usuario_escola.registro_funcional = "0000001"
usuario_escola.nome = "SUPER USUARIO ESCOLA"
usuario_escola.cargo = "Diretor"
usuario_escola.save()

usuario_dre = Usuario.objects.get(email="dre@admin.com")
usuario_dre.registro_funcional = "0000010"
usuario_dre.nome = "SUPER USUARIO DRE"
usuario_dre.cargo = "Coordenador"
usuario_dre.save()

usuario_codae = Usuario.objects.get(email="codae@admin.com")
usuario_codae.registro_funcional = "0000011"
usuario_codae.nome = "Gestão de Terceirizadas"
usuario_codae.cargo = "Coordenador"
usuario_codae.save()

usuario_gestao_produto_codae = Usuario.objects.get(email="gpcodae@admin.com")
usuario_gestao_produto_codae.registro_funcional = "1000011"
usuario_gestao_produto_codae.nome = "SUPER USUARIO GESTAO PRODUTO CODAE"
usuario_gestao_produto_codae.cargo = "Nutricionista"
usuario_gestao_produto_codae.save()

usuario_terceirizada = Usuario.objects.get(email="terceirizada@admin.com")
usuario_terceirizada.registro_funcional = "0000100"
usuario_terceirizada.nome = "SUPER USUARIO TERCEIRIZADA"
usuario_terceirizada.cargo = "Gerente"
usuario_terceirizada.save()

usuario_nutri_codae = Usuario.objects.get(email="nutricodae@admin.com")
usuario_nutri_codae.registro_funcional = "0000101"
usuario_nutri_codae.nome = "SUPER USUARIO NUTRICIONISTA CODAE"
usuario_nutri_codae.crn_numero = "15975364"
usuario_nutri_codae.cargo = "Nutricionista"
usuario_nutri_codae.save()

usuario_nutri_supervisao = Usuario.objects.get(
    email="nutrisupervisao@admin.com"
)  # noqa
usuario_nutri_supervisao.registro_funcional = "0010000"
usuario_nutri_supervisao.nome = "SUPER USUARIO NUTRICIONISTA SUPERVISAO"
usuario_nutri_supervisao.crn_numero = "47135859"
usuario_nutri_supervisao.cargo = "Nutricionista"
usuario_nutri_supervisao.save()

usuario_escola_cei = Usuario.objects.get(email="escolacei@admin.com")
usuario_escola_cei.registro_funcional = "0000110"
usuario_escola_cei.nome = "SUPER USUARIO ESCOLA CEI"
usuario_escola_cei.cargo = "Diretor"
usuario_escola_cei.save()

usuario_escola_cei_ceu = Usuario.objects.get(email="escolaceiceu@admin.com")
usuario_escola_cei_ceu.registro_funcional = "0000111"
usuario_escola_cei_ceu.nome = "SUPER USUARIO ESCOLA CEI CEU"
usuario_escola_cei_ceu.cargo = "Diretor"
usuario_escola_cei_ceu.save()

usuario_escola_cci = Usuario.objects.get(email="escolacci@admin.com")
usuario_escola_cci.registro_funcional = "0001000"
usuario_escola_cci.nome = "SUPER USUARIO ESCOLA CCI"
usuario_escola_cci.cargo = "Diretor"
usuario_escola_cci.save()

usuario_escola_emef = Usuario.objects.get(email="escolaemef@admin.com")
usuario_escola_emef.registro_funcional = "0001001"
usuario_escola_emef.nome = "SUPER USUARIO ESCOLA EMEF"
usuario_escola_emef.cargo = "Diretor"
usuario_escola_emef.save()

usuario_escola_emebs = Usuario.objects.get(email="escolaemebs@admin.com")
usuario_escola_emebs.registro_funcional = "0001010"
usuario_escola_emebs.nome = "SUPER USUARIO ESCOLA EMEBS"
usuario_escola_emebs.cargo = "Diretor"
usuario_escola_emebs.save()

usuario_escola_cieja = Usuario.objects.get(email="escolacieja@admin.com")
usuario_escola_cieja.registro_funcional = "0001011"
usuario_escola_cieja.nome = "SUPER USUARIO ESCOLA CIEJA"
usuario_escola_cieja.cargo = "Diretor"
usuario_escola_cieja.save()

usuario_escola_emei = Usuario.objects.get(email="escolaemei@admin.com")
usuario_escola_emei.registro_funcional = "0001100"
usuario_escola_emei.nome = "SUPER USUARIO ESCOLA EMEI"
usuario_escola_emei.cargo = "Diretor"
usuario_escola_emei.save()

usuario_escola_ceu_emei = Usuario.objects.get(email="escolaceuemei@admin.com")
usuario_escola_ceu_emei.registro_funcional = "0001101"
usuario_escola_ceu_emei.nome = "SUPER USUARIO ESCOLA CEU EMEI"
usuario_escola_ceu_emei.cargo = "Diretor"
usuario_escola_ceu_emei.save()

usuario_escola_ceu_emef = Usuario.objects.get(email="escolaceuemef@admin.com")
usuario_escola_ceu_emef.registro_funcional = "0001111"
usuario_escola_ceu_emef.nome = "SUPER USUARIO ESCOLA CEU EMEF"
usuario_escola_ceu_emef.cargo = "Diretor"
usuario_escola_ceu_emef.save()

# PROD

perfil_diretor_escola, created = Perfil.objects.get_or_create(
    nome="DIRETOR_UE", ativo=True, super_usuario=True
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

perfil_usuario_nutri_supervisao, created = Perfil.objects.get_or_create(
    nome="COORDENADOR_SUPERVISAO_NUTRICAO", ativo=True, super_usuario=True
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

perfil_usuario_terceirizada, created = Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_EMPRESA", ativo=True, super_usuario=True
)

perfil_coordenador_gestao_produto, created = Perfil.objects.get_or_create(
    nome="COORDENADOR_GESTAO_PRODUTO", ativo=True, super_usuario=True
)

perfil_administrador_gestao_produto, created = Perfil.objects.get_or_create(
    nome="ADMINISTRADOR_GESTAO_PRODUTO", ativo=True, super_usuario=True
)

# FIM PROD

# DEV

escola = Escola.objects.get(nome="EMEF JOSE ERMIRIO DE MORAIS, SEN.")
escola_cei = Escola.objects.get(nome="CEI DIRET ENEDINA DE SOUSA CARVALHO")
escola_cei_ceu = Escola.objects.get(nome="CEU CEI MENINOS")
escola_cci = Escola.objects.get(nome="CCI/CIPS CAMARA MUNICIPAL DE SAO PAULO")
escola_emef = Escola.objects.get(nome="EMEF PERICLES EUGENIO DA SILVA RAMOS")
escola_emebs = Escola.objects.get(nome="EMEBS HELEN KELLER")
escola_cieja = Escola.objects.get(nome="CIEJA CLOVIS CAITANO MIQUELAZZO - IPIRANGA")
escola_emei = Escola.objects.get(nome="EMEI SENA MADUREIRA")
escola_ceu_emei = Escola.objects.get(nome="CEU EMEI BENNO HUBERT STOLLENWERK, PE.")
escola_ceu_emef = Escola.objects.get(
    nome="CEU EMEF MARA CRISTINA TARTAGLIA SENA, PROFA."
)
diretoria_regional = DiretoriaRegional.objects.get(
    nome="DIRETORIA REGIONAL DE EDUCACAO IPIRANGA"
)
codae, created = Codae.objects.get_or_create(nome="CODAE")
terceirizada = escola.lote.terceirizada

Vinculo.objects.create(
    instituicao=escola,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_cei,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_cei,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_cei_ceu,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_cei_ceu,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_cci,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_cci,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_emef,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_emef,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_emebs,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_emebs,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_cieja,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_cieja,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_emei,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_emei,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_ceu_emei,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_ceu_emei,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=escola_ceu_emef,
    perfil=perfil_diretor_escola,
    usuario=usuario_escola_ceu_emef,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=diretoria_regional,
    perfil=perfil_cogestor_dre,
    usuario=usuario_dre,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=codae,
    perfil=perfil_usuario_codae,
    usuario=usuario_codae,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=codae,
    perfil=perfil_usuario_nutri_codae,
    usuario=usuario_nutri_codae,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=codae,
    perfil=perfil_usuario_nutri_supervisao,
    usuario=usuario_nutri_supervisao,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=codae,
    perfil=perfil_coordenador_gestao_produto,
    usuario=usuario_gestao_produto_codae,
    data_inicial=data_atual,
)

Vinculo.objects.create(
    instituicao=terceirizada,
    perfil=perfil_usuario_terceirizada,
    usuario=usuario_terceirizada,
    data_inicial=data_atual,
)
