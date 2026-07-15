import os

from src.recebimento.models import ArquivoFichaRecebimento


def test_behavior_tem_arquivos_deletaveis(
    ficha_de_recebimento_factory,
    arquivo_temporario,
):
    obj = ArquivoFichaRecebimento.objects.create(
        ficha_recebimento=ficha_de_recebimento_factory(),
        arquivo=arquivo_temporario,
        nome="Arquivo Teste",
    )

    obj.delete()

    assert not os.path.isfile(arquivo_temporario)
