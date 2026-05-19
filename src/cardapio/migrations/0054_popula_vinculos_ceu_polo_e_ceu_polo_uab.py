from django.db import migrations

TARGET_TIPOS_UNIDADE_ESCOLAR = ("CEU POLO", "CEU POLO UAB")
TARGET_PERIODOS_ESCOLARES = ("MANHA", "TARDE", "NOITE", "INTEGRAL")


def popula_vinculos_ceu_polo(apps, schema_editor):
    Vinculo = apps.get_model(
        "cardapio",
        "VinculoTipoAlimentacaoComPeriodoEscolarETipoUnidadeEscolar",
    )
    PeriodoEscolar = apps.get_model("escola", "PeriodoEscolar")
    TipoUnidadeEscolar = apps.get_model("escola", "TipoUnidadeEscolar")

    db_alias = schema_editor.connection.alias

    periodos = {
        periodo.nome: periodo
        for periodo in PeriodoEscolar.objects.using(db_alias).filter(
            nome__in=TARGET_PERIODOS_ESCOLARES
        )
    }
    tipos_unidade = {
        tipo_unidade.iniciais: tipo_unidade
        for tipo_unidade in TipoUnidadeEscolar.objects.using(db_alias).filter(
            iniciais__in=TARGET_TIPOS_UNIDADE_ESCOLAR
        )
    }

    for iniciais_tipo_unidade in TARGET_TIPOS_UNIDADE_ESCOLAR:
        tipo_unidade = tipos_unidade.get(iniciais_tipo_unidade)
        if not tipo_unidade:
            continue

        for nome_periodo in TARGET_PERIODOS_ESCOLARES:
            periodo = periodos.get(nome_periodo)
            if not periodo:
                continue

            vinculo, _ = Vinculo.objects.using(db_alias).get_or_create(
                tipo_unidade_escolar=tipo_unidade,
                periodo_escolar=periodo,
            )
            vinculo.ativo = True
            vinculo.save(update_fields=["ativo"])


class Migration(migrations.Migration):
    dependencies = [
        ("cardapio", "0053_remove_combo_models"),
        ("escola", "0081_remove_tipounidadeescolar_cardapios"),
    ]

    operations = [
        migrations.RunPython(
            popula_vinculos_ceu_polo,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
