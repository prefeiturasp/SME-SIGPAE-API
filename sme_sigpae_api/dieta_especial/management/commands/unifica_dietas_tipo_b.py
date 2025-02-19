import logging

import environ
from django.core.management import BaseCommand

from sme_sigpae_api.dieta_especial.models import (
    ClassificacaoDieta,
    LogQuantidadeDietasAutorizadas,
    LogQuantidadeDietasAutorizadasCEI,
    SolicitacaoDietaEspecial,
)

logger = logging.getLogger("sigpae.cmd_unifica_dietas_tipo_b")

env = environ.Env()


class Command(BaseCommand):
    help = (
        "Unifica as dietas `Tipo B - LANCHE e REFEIÇÃO` e `Tipo B - LANCHE` em `Tipo B`"
    )

    def handle(self, *args, **options):
        classificacoes_existem = self.checa_se_classificacoes_exitem()
        if classificacoes_existem:
            classificacao_tipo_b_lanche = ClassificacaoDieta.objects.get(
                nome="Tipo B - LANCHE"
            )
            classificacao_tipo_b_lanche_refeicao = ClassificacaoDieta.objects.get(
                nome="Tipo B - LANCHE e REFEIÇÃO"
            )
            self.unifica_fks_classificacao_tipo_b(
                classificacao_tipo_b_lanche, classificacao_tipo_b_lanche_refeicao
            )
            self.atualizar_quantidades_log_escolas_gerais()
            self.atualizar_quantidades_log_escolas_cei()
            self.renomeia_classificacao_e_remove_extra(
                classificacao_tipo_b_lanche, classificacao_tipo_b_lanche_refeicao
            )

    def checa_se_classificacoes_exitem(self):
        self.stdout.write(self.style.SUCCESS("Checa se classificações existem"))
        classificacoes_existem = True
        if not ClassificacaoDieta.objects.filter(
            nome="Tipo B - LANCHE e REFEIÇÃO"
        ).exists():
            self.stdout.write(
                self.style.ERROR(
                    "Classificação `Tipo B - LANCHE e REFEIÇÃO` não encontrada"
                )
            )
            classificacoes_existem = False
        if not ClassificacaoDieta.objects.filter(nome="Tipo B - LANCHE").exists():
            self.stdout.write(
                self.style.ERROR("Classificação `Tipo B - LANCHE` não encontrada")
            )
            classificacoes_existem = False
        return classificacoes_existem

    def unifica_fks_classificacao_tipo_b(
        self, classificacao_tipo_b_lanche, classificacao_tipo_b_lanche_refeicao
    ):
        self.stdout.write(self.style.SUCCESS("Atualiza FKs"))
        SolicitacaoDietaEspecial.objects.filter(
            classificacao=classificacao_tipo_b_lanche_refeicao
        ).update(classificacao=classificacao_tipo_b_lanche)

    def atualizar_quantidades_log(
        self,
        model_class,
        classificacao_lanche,
        classificacao_lanche_refeicao,
        key_fields,
    ):
        self.stdout.write(
            self.style.SUCCESS("**** Atualizando logs {model_class.__name__} ****")
        )

        objetos_lanche = model_class.objects.filter(classificacao=classificacao_lanche)
        objetos_lanche_refeicao = model_class.objects.filter(
            classificacao=classificacao_lanche_refeicao, quantidade__gt=0
        )

        grupos = {}

        self.stdout.write(self.style.SUCCESS("Configurando chaves nos grupos"))
        for obj in objetos_lanche:
            chave = tuple(getattr(obj, field) for field in key_fields)
            grupos[chave] = {"lanche": obj, "lanche_refeicao": None}

        self.stdout.write(self.style.SUCCESS("Configurando chaves lanche_refeicao"))
        for obj in objetos_lanche_refeicao:
            chave = tuple(getattr(obj, field) for field in key_fields)
            if chave in grupos:
                grupos[chave]["lanche_refeicao"] = obj

        objetos_para_atualizar = []

        self.stdout.write(self.style.SUCCESS("Atualizando quantidades"))

        for grupo in grupos.values():
            if grupo["lanche"] and grupo["lanche_refeicao"]:
                grupo["lanche"].quantidade += grupo["lanche_refeicao"].quantidade
                objetos_para_atualizar.append(grupo["lanche"])

        model_class.objects.bulk_update(objetos_para_atualizar, ["quantidade"])

    def atualizar_quantidades_log_escolas_gerais(self):
        classificacao_lanche = ClassificacaoDieta.objects.get(nome="Tipo B - LANCHE")
        classificacao_lanche_refeicao = ClassificacaoDieta.objects.get(
            nome="Tipo B - LANCHE e REFEIÇÃO"
        )
        key_fields = [
            "escola_id",
            "periodo_escolar_id",
            "cei_ou_emei",
            "infantil_ou_fundamental",
            "data",
        ]
        self.atualizar_quantidades_log(
            LogQuantidadeDietasAutorizadas,
            classificacao_lanche,
            classificacao_lanche_refeicao,
            key_fields,
        )

    def atualizar_quantidades_log_escolas_cei(self):
        classificacao_lanche = ClassificacaoDieta.objects.get(nome="Tipo B - LANCHE")
        classificacao_lanche_refeicao = ClassificacaoDieta.objects.get(
            nome="Tipo B - LANCHE e REFEIÇÃO"
        )
        key_fields = ["escola_id", "periodo_escolar_id", "faixa_etaria_id", "data"]
        self.atualizar_quantidades_log(
            LogQuantidadeDietasAutorizadasCEI,
            classificacao_lanche,
            classificacao_lanche_refeicao,
            key_fields,
        )

    def renomeia_classificacao_e_remove_extra(
        self, classificacao_tipo_b_lanche, classificacao_tipo_b_lanche_refeicao
    ):
        self.stdout.write(
            self.style.SUCCESS(
                "Renomeia classificação para Tipo B e exclui a classificação extra"
            )
        )
        classificacao_tipo_b_lanche.nome = "Tipo B"
        classificacao_tipo_b_lanche.save()
        classificacao_tipo_b_lanche_refeicao.delete()
