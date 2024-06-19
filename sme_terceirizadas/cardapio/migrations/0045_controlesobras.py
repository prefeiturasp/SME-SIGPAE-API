# Generated by Django 3.2.18 on 2023-09-06 15:53

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('escola', '0060_auto_20230815_1534'),
        ('produto', '0082_tipoalimento'),
        ('cardapio', '0044_dataintervaloalteracaocardapio'),
    ]

    operations = [
        migrations.CreateModel(
            name='ControleSobras',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('peso_alimento', models.DecimalField(decimal_places=2, max_digits=3)),
                ('peso_recipiente', models.DecimalField(decimal_places=2, max_digits=3)),
                ('peso_sobra', models.DecimalField(decimal_places=2, max_digits=3)),
                ('escola', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='escola.escola')),
                ('tipo_alimentacao', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='cardapio.tipoalimentacao')),
                ('tipo_alimento', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='produto.tipoalimento')),
                ('tipo_recipiente', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='produto.tiporecipiente')),
            ],
            options={
                'verbose_name': 'Controle de Sobras',
            },
        ),
    ]