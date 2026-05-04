from src.kit_lanche.data.kit_lanche_item import data_kit_lanche_item
from src.kit_lanche.models import ItemKitLanche, KitLanche
from utility.carga_dados.helper import ja_existe, progressbar


def cria_kit_lanche_item():
    for item in progressbar(data_kit_lanche_item, "Item Kit Lanche"):
        _, created = ItemKitLanche.objects.get_or_create(nome=item)
        if not created:
            ja_existe("ItemKitLanche", item)


def cria_kit_lanche():
    # Deleta kits existentes
    KitLanche.objects.all().delete()
    for i in progressbar(range(1, 11), "Kit Lanche"):
        KitLanche.objects.create(nome=f"Kit {i}")
