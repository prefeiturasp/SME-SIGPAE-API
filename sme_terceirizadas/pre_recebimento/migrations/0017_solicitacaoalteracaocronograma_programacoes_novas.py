# Generated by Django 3.2.18 on 2023-08-24 12:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pre_recebimento', '0016_remove_solicitacaoalteracaocronograma_motivo'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitacaoalteracaocronograma',
            name='programacoes_novas',
            field=models.ManyToManyField(blank=True, related_name='programacoes_novas', to='pre_recebimento.ProgramacaoDoRecebimentoDoCronograma'),
        ),
    ]