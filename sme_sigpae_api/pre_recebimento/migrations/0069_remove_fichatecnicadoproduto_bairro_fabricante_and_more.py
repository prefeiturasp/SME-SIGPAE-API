# Generated by Django 5.2.1 on 2025-06-16 14:58

import uuid

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def migrar_dados_fabricante(apps, schema_editor):
    """Migra os dados de FichaTecnicaDoProduto para FabricanteFichaTecnica."""
    FichaTecnicaDoProduto = apps.get_model("pre_recebimento", "FichaTecnicaDoProduto")
    FabricanteFichaTecnica = apps.get_model("pre_recebimento", "FabricanteFichaTecnica")

    # Lista de campos relacionados ao fabricante
    campos_fabricante = [
        "bairro_fabricante",
        "cep_fabricante",
        "cidade_fabricante",
        "cnpj_fabricante",
        "complemento_fabricante",
        "email_fabricante",
        "endereco_fabricante",
        "estado_fabricante",
        "numero_fabricante",
        "telefone_fabricante",
    ]

    # Cria condição para verificar se algum campo do fabricante não é nulo
    tem_dados_fabricante = models.Q(
        **{f"{campo}__isnull": False for campo in campos_fabricante},
        _connector="OR",  # Usa OR para verificar qualquer um dos campos
    )

    # Inclui registros que tenham relação com fabricante
    tem_fabricante = models.Q(fabricante__isnull=False)

    # Busca todos os registros que tenham dados de fabricante OU relação com fabricante
    for ficha in FichaTecnicaDoProduto.objects.filter(
        tem_dados_fabricante | tem_fabricante
    ).distinct():
        # Prepara os dados para criar o FabricanteFichaTecnica
        fabricante_tecnica = FabricanteFichaTecnica.objects.create(
            cnpj=ficha.cnpj_fabricante,
            cep=ficha.cep_fabricante,
            endereco=ficha.endereco_fabricante,
            numero=ficha.numero_fabricante,
            complemento=ficha.complemento_fabricante,
            bairro=ficha.bairro_fabricante,
            cidade=ficha.cidade_fabricante,
            estado=ficha.estado_fabricante,
            email=ficha.email_fabricante,
            telefone=ficha.telefone_fabricante,
            fabricante=ficha.fabricante if hasattr(ficha, "fabricante") else None,
        )

        # Define o novo campo fabricante_ficha_tecnica
        ficha.fabricante_ficha_tecnica = fabricante_tecnica
        ficha.save(update_fields=["fabricante_ficha_tecnica"])


def reverter_migracao_dados_fabricante(apps, schema_editor):
    """Reverte a migração de dados."""
    FichaTecnicaDoProduto = apps.get_model("pre_recebimento", "FichaTecnicaDoProduto")

    # Para cada ficha que tenha um fabricante_ficha_tecnica
    for ficha in FichaTecnicaDoProduto.objects.filter(
        fabricante_ficha_tecnica__isnull=False
    ):
        fabricante = ficha.fabricante_ficha_tecnica

        # Atualiza os campos antigos com os dados do FabricanteFichaTecnica
        ficha.bairro_fabricante = fabricante.bairro
        ficha.cep_fabricante = fabricante.cep
        ficha.cidade_fabricante = fabricante.cidade
        ficha.cnpj_fabricante = fabricante.cnpj
        ficha.complemento_fabricante = fabricante.complemento
        ficha.email_fabricante = fabricante.email
        ficha.endereco_fabricante = fabricante.endereco
        ficha.estado_fabricante = fabricante.estado
        ficha.numero_fabricante = fabricante.numero
        ficha.telefone_fabricante = fabricante.telefone

        # Salva apenas os campos alterados
        ficha.save(
            update_fields=[
                "bairro_fabricante",
                "cep_fabricante",
                "cidade_fabricante",
                "cnpj_fabricante",
                "complemento_fabricante",
                "email_fabricante",
                "endereco_fabricante",
                "estado_fabricante",
                "numero_fabricante",
                "telefone_fabricante",
            ]
        )


class Migration(migrations.Migration):
    dependencies = [
        ("pre_recebimento", "0068_alter_etapasdocronograma_options"),
        ("produto", "0083_alter_produtoedital_suspenso_justificativa"),
    ]

    operations = [
        # First, create the new model
        migrations.CreateModel(
            name="FabricanteFichaTecnica",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "alterado_em",
                    models.DateTimeField(auto_now=True, verbose_name="Alterado em"),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "cnpj",
                    models.CharField(
                        blank=True,
                        max_length=14,
                        validators=[django.core.validators.MinLengthValidator(14)],
                        verbose_name="CNPJ",
                    ),
                ),
                ("cep", models.CharField(blank=True, max_length=8, verbose_name="CEP")),
                (
                    "endereco",
                    models.CharField(
                        blank=True, max_length=160, verbose_name="Endereço"
                    ),
                ),
                (
                    "numero",
                    models.CharField(blank=True, max_length=10, verbose_name="Número"),
                ),
                (
                    "complemento",
                    models.CharField(
                        blank=True, max_length=250, verbose_name="Complemento"
                    ),
                ),
                (
                    "bairro",
                    models.CharField(blank=True, max_length=150, verbose_name="Bairro"),
                ),
                (
                    "cidade",
                    models.CharField(blank=True, max_length=150, verbose_name="Cidade"),
                ),
                (
                    "estado",
                    models.CharField(blank=True, max_length=150, verbose_name="Estado"),
                ),
                (
                    "email",
                    models.EmailField(
                        blank=True, max_length=254, verbose_name="E-mail"
                    ),
                ),
                (
                    "telefone",
                    models.CharField(
                        blank=True,
                        max_length=13,
                        validators=[django.core.validators.MinLengthValidator(8)],
                        verbose_name="Telefone",
                    ),
                ),
                (
                    "fabricante",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="fichas_tecnicas_detalhes",
                        to="produto.fabricante",
                    ),
                ),
            ],
            options={
                "verbose_name": "Fabricante da Ficha Técnica",
                "verbose_name_plural": "Fabricantes das Fichas Técnicas",
            },
        ),
        # Adiciona o novo campo fabricante_ficha_tecnica, permitindo nulo inicialmente
        migrations.AddField(
            model_name="fichatecnicadoproduto",
            name="fabricante_ficha_tecnica",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fichas_tecnicas",
                to="pre_recebimento.fabricantefichatecnica",
            ),
        ),
        # Executa a migração de dados
        migrations.RunPython(
            code=migrar_dados_fabricante,
            reverse_code=reverter_migracao_dados_fabricante,
        ),
        # Agora torna o campo obrigatório (não nulo)
        migrations.AlterField(
            model_name="fichatecnicadoproduto",
            name="fabricante_ficha_tecnica",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="fichas_tecnicas",
                to="pre_recebimento.fabricantefichatecnica",
            ),
        ),
        # Finalmente, remove os campos antigos
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="bairro_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="cep_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="cidade_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="cnpj_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="complemento_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="email_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="endereco_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="estado_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="numero_fabricante",
        ),
        migrations.RemoveField(
            model_name="fichatecnicadoproduto",
            name="telefone_fabricante",
        ),
    ]
