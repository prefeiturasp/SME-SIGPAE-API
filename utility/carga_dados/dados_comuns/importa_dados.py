from src.dados_comuns.data.contatos import data_contatos
from src.dados_comuns.models import Contato
from utility.carga_dados.helper import progressbar


def cria_contatos():
    for item in progressbar(data_contatos, "Contato"):
        obj = Contato.objects.filter(email=item["email"]).first()
        if not obj:
            Contato.objects.create(
                telefone=item["telefone"],
                telefone2=item["telefone2"],
                celular=item["celular"],
                email=item["email"],
            )
