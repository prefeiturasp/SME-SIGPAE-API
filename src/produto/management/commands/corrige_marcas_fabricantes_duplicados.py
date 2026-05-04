import logging
import unicodedata
from difflib import get_close_matches

from django.core.management import BaseCommand
from django.db.models import F, Func, Value
from django.db.models.functions import Upper

from src.dieta_especial.protocolo_padrao.models import Alimento
from src.produto.models import Fabricante, Marca, Produto

logger = logging.getLogger("sigpae.cmd_corrige_marcas_fabricantes_duplicados")


class Command(BaseCommand):
    """Script para corrigir marcas e produtos duplicados."""

    help = "Corrige marcas e produtos duplicadoss"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("*** Marcas ***"))
        self.corrige_marcas()
        self.normalizar_marcas()
        self.remove_duplicados_marcas()

        self.stdout.write(self.style.SUCCESS("*** Fabricantes ***"))
        self.corrige_fabricantes()
        self.normalizar_fabricantes()
        self.padronizar_SA_LTDA()
        self.remove_duplicados_fabricantes()

    def remove_duplicados_marcas(self):  # noqa C901
        combinacoes_marcas = []
        marcas = [marca.nome for marca in Marca.objects.all()]
        for marca in marcas:
            combinacao = get_close_matches(marca, marcas, cutoff=1)
            combinacao.sort()
            if len(combinacao) > 1 and combinacao not in combinacoes_marcas:
                combinacoes_marcas.append(combinacao)
        for combinacao in combinacoes_marcas:
            try:
                marca_original = Marca.objects.filter(nome=combinacao[0]).first()
                marcas_duplicadas = Marca.objects.filter(nome=combinacao[0]).exclude(
                    id=marca_original.id
                )
                Produto.objects.filter(marca__nome=combinacao[0]).exclude(
                    marca=marca_original
                ).update(marca=marca_original)
                Alimento.objects.filter(marca__nome=combinacao[0]).exclude(
                    marca=marca_original
                ).update(marca=marca_original)
                marcas_duplicadas.delete()
            except Exception:
                self.stdout.write(
                    self.style.ERROR(f"Erro ao atualizar marca {combinacao[0]}")
                )

    def remove_duplicados_fabricantes(self):  # noqa C901
        combinacoes_fabricantes = []
        fabricantes = [fabricante.nome for fabricante in Fabricante.objects.all()]
        for fabricante in fabricantes:
            combinacao = get_close_matches(fabricante, fabricantes, cutoff=1)
            combinacao.sort()
            if len(combinacao) > 1 and combinacao not in combinacoes_fabricantes:
                combinacoes_fabricantes.append(combinacao)
        for combinacao in combinacoes_fabricantes:
            try:
                fabricante_original = Fabricante.objects.filter(
                    nome=combinacao[0]
                ).first()
                fabricantes_duplicados = Fabricante.objects.filter(
                    nome=combinacao[0]
                ).exclude(id=fabricante_original.id)
                Produto.objects.filter(fabricante__nome=combinacao[0]).exclude(
                    fabricante=fabricante_original
                ).update(fabricante=fabricante_original)
                fabricantes_duplicados.delete()
            except Exception:
                self.stdout.write(
                    self.style.ERROR(f"Erro ao atualizar fabricante {combinacao[0]}")
                )

    def remove_acentos(self, text):
        text = (
            unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
        )
        return str(text)

    def normalizar_marcas(self):
        self.stdout.write(self.style.SUCCESS("Convertendo marcas para UPPER"))
        Marca.objects.update(nome=Upper("nome"))
        self.stdout.write(self.style.SUCCESS("Removendo espaços duplos"))
        Marca.objects.filter(nome__icontains="  ").update(
            nome=Func(F("nome"), Value("  "), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo pontos"))
        Marca.objects.filter(nome__icontains=".").update(
            nome=Func(F("nome"), Value("."), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo traços"))
        Marca.objects.filter(nome__icontains=" - ").update(
            nome=Func(F("nome"), Value(" - "), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo aspas"))
        Marca.objects.filter(nome__icontains="'").update(
            nome=Func(F("nome"), Value("'"), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo parênteses"))
        Marca.objects.filter(nome__icontains="(").update(
            nome=Func(F("nome"), Value("("), Value(""), function="replace")
        )
        Marca.objects.filter(nome__icontains=")").update(
            nome=Func(F("nome"), Value(")"), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Trocando & por E"))
        Marca.objects.filter(nome__icontains="&").update(
            nome=Func(F("nome"), Value("&"), Value("E"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo acentos"))
        for marca in Marca.objects.all():
            if self.remove_acentos(marca.nome) != marca.nome:
                marca.nome = self.remove_acentos(marca.nome)
                marca.save()

    def normalizar_fabricantes(self):
        self.stdout.write(self.style.SUCCESS("Convertendo fabricantes para UPPER"))
        Fabricante.objects.update(nome=Upper("nome"))
        self.stdout.write(self.style.SUCCESS("Removendo espaços duplos"))
        Fabricante.objects.filter(nome__icontains="  ").update(
            nome=Func(F("nome"), Value("  "), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo pontos"))
        Fabricante.objects.filter(nome__icontains=".").update(
            nome=Func(F("nome"), Value("."), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo traços"))
        Fabricante.objects.filter(nome__icontains=" - ").update(
            nome=Func(F("nome"), Value(" - "), Value(" "), function="replace")
        )
        Fabricante.objects.filter(nome__icontains="-").update(
            nome=Func(F("nome"), Value("-"), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo aspas"))
        Fabricante.objects.filter(nome__icontains="'").update(
            nome=Func(F("nome"), Value("'"), Value(""), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Trocando & por E"))
        Fabricante.objects.filter(nome__icontains="&").update(
            nome=Func(F("nome"), Value("&"), Value("E"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Trocando / por espaço"))
        Fabricante.objects.filter(nome__icontains="/").update(
            nome=Func(F("nome"), Value("/"), Value(" "), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Removendo acentos"))
        for fabricante in Fabricante.objects.all():
            if self.remove_acentos(fabricante.nome) != fabricante.nome:
                fabricante.nome = self.remove_acentos(fabricante.nome)
                fabricante.save()

    def padronizar_SA_LTDA(self):
        self.stdout.write(self.style.SUCCESS("Substituindo S.A. por SA"))
        Fabricante.objects.filter(nome__icontains="S.A.").update(
            nome=Func(F("nome"), Value("S.A."), Value("SA"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo S.A por SA"))
        Fabricante.objects.filter(nome__icontains="S.A").update(
            nome=Func(F("nome"), Value("S.A"), Value("SA"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo SA. por SA"))
        Fabricante.objects.filter(nome__icontains=" SA.").update(
            nome=Func(F("nome"), Value(" SA."), Value(" SA"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo S/A por SA"))
        Fabricante.objects.filter(nome__icontains="S/A").update(
            nome=Func(F("nome"), Value("S/A"), Value("SA"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo S A por SA"))
        Fabricante.objects.filter(nome__icontains=" S A").update(
            nome=Func(F("nome"), Value(" S A"), Value(" SA"), function="replace")
        )
        self.stdout.write(self.style.SUCCESS("Substituindo LTDA. por LTDA"))
        Fabricante.objects.filter(nome__icontains="LTDA.").update(
            nome=Func(F("nome"), Value("LTDA."), Value("LTDA"), function="replace")
        )

    def corrige_marcas(self):
        self.stdout.write(self.style.SUCCESS("Normalizando marcas para unificação"))
        Marca.objects.filter(nome__in=["AD'0RO", "AD´ORO", "AD'ORO"]).update(
            nome="AD'ORO"
        )  # noqa Q000
        Marca.objects.filter(nome="BAPTISTELLA ALIMENTOS LTDA").update(
            nome="BAPTISTELLA ALIMENTOS"
        )
        Marca.objects.filter(nome="B J P").update(nome="BJP")
        Marca.objects.filter(nome="CHÁ LEÃO - CAMOMILA").update(
            nome="CHÁ LEÃO (CAMOMILA)"
        )
        Marca.objects.filter(nome="CORPO & SABOR").update(nome="CORPO E SABOR")
        Marca.objects.filter(nome="CRI ALIMENTOS").update(nome="CRIALIMENTOS")
        Marca.objects.filter(nome="DA ROLT").update(nome="DAROLT")
        Marca.objects.filter(nome__in=["DA SABOR", "DÁSABOR"]).update(nome="DASABOR")
        Marca.objects.filter(nome="DE LA MARIE").update(nome="DELAMARIE")
        Marca.objects.filter(nome="DE PARMA").update(nome="DEPARMA")
        Marca.objects.filter(nome="FAZENDA NOVA ALINAÇA").update(
            nome="FAZENDA NOVA ALIANÇA"
        )
        Marca.objects.filter(nome="KARAM'S MAR").update(nome="KARAMS MAR")
        Marca.objects.filter(nome="MAIS CERTA").update(nome="MAISCERTA")
        Marca.objects.filter(nome="MILNUTRI PREMIUM+").update(nome="MILNUTRI PREMIUM +")
        Marca.objects.filter(nome="MULTMEAT").update(nome="MULTIMEAT")
        Marca.objects.filter(nome="NESLAC CONFOR ZERO LACTOSE").update(
            nome="NESLAC COMFOR ZERO LACTOSE"
        )
        Marca.objects.filter(nome="NUTRI COOKIE").update(nome="NUTRICOOKIE")
        Marca.objects.filter(nome="SANTA AMÁLIA S.A").update(nome="SANTA AMÁLIA")
        Marca.objects.filter(nome__in=["STELLA D´ORO", "STELLA D ORO"]).update(
            nome="STELLA D'ORO"
        )
        Marca.objects.filter(nome="TUTTI LIFE").update(nome="TUTTY LIFE")
        Marca.objects.filter(nome="VITA SUCO").update(nome="VITASUCO")

    def corrige_fabricantes(self):
        self.stdout.write(
            self.style.SUCCESS("Normalizando fabricantes para unificação")
        )
        Fabricante.objects.filter(nome="ALCA FOODS").update(nome="ALCA FOODS LTDA")
        Fabricante.objects.filter(
            nome="BJP COMÉRCIO E DISTRIBUIÇÃO DE ALIMENTOS EIRELI"
        ).update(nome="B J P COMERCIO E DISTRIBUIÇÃO DE ALIMENTOS LTDA")
        Fabricante.objects.filter(nome="BRASIL CITRUS IND. E COM. LTDA").update(
            nome="BRASIL CITRUS INDÚSTRIA E COMÉRCIO LTDA"
        )
        Fabricante.objects.filter(
            nome__in=[
                "BRYK - IND. DE PANIFICAÇÃO LTDA",
                "BRYK - INDÚSTRIA DE PANIFICAÇÃO LTDA",
                "BRYK IND.DE PANIFICAÇÃO LTDA",
            ],
        ).update(nome="BRYK INDÚSTRIA DE PANIFICAÇÃO LTDA")
        Fabricante.objects.filter(
            nome="BEM NUTRIR INDÚSTRIA E COMÉRCIO DE PRODUTOS ALIMENTÍCIOS"
        ).update(
            nome="BEM NUTRIR INDÚSTRIA E COMÉRCIO DE PRODUTOS ALIMENTÍCIOS SEM GLÚTEN LTDA"
        )
        Fabricante.objects.filter(
            nome="BJP COMÉRCIO E DISTRIBUIÇÃO DE ALIMENTOS EIRELI"
        ).update(nome="B J P COMERCIO E DISTRIBUIÇÃO DE ALIMENTOS LTDA")
        Fabricante.objects.filter(
            nome__in=[
                "CATABY IND. E COMÉRCIO DE CARNES",
                "CATAPY IND. E COMERCIO DE CARNES LTDA",
            ]
        ).update(nome="CATABY IND. E COMÉRCIO DE CARNES LTDA")
        Fabricante.objects.filter(nome="COMPANHIA CACIQUE DE CAFÉ SOLÚVEL").update(
            nome="CIA CACIQUE DE CAFÉ SOLÚVEL"
        )
        Fabricante.objects.filter(nome="COCAM CIA. DE CAFE SOLUVEL E DERIVADOS").update(
            nome="COCAM CIA DE CAFE SOLUVEL E DERIVADOS"
        )
        Fabricante.objects.filter(nome="COMÉRCIO DE ALIMENTOS DASABOR").update(
            nome="COMÉRCIO DE ALIMENTOS DA SABOR LTDA"
        )
        Fabricante.objects.filter(nome="COOPERATIVA VINÍCOLA AURORA").update(
            nome="COOPERATIVA VINÍCOLA AURORA LTDA"
        )
        Fabricante.objects.filter(nome="CRI ALIMENTOS IND. E COMÉRCIO LTDA").update(
            nome="CRIALIMENTOS INDÚSTRIA E COMÉRCIO LTDA"
        )
        Fabricante.objects.filter(nome="DELIFOODS ALIMENTOS").update(
            nome="DELIFOODS ALIMENTOS EIRELI"
        )
        Fabricante.objects.filter(
            nome="DIELAT INDÚSTRIA E COMÉRCIO DE LATICÍNIOS LTDA FÁBRICA DE LATICÍNIOS"
        ).update(nome="DIELAT INDÚSTRIA E COMÉRCIO DE LATICÍNIOS LTDA")
        Fabricante.objects.filter(
            nome__in=[
                "D. B. IND. E COM. DE CARNES E DERIVADOS LTDA",
                "D.B INDÚSTRIA E COMÉRCIO DE CARNES E DERIVADOS LTDA",
            ]
        ).update(nome="DB INDÚSTRIA E COMÉRCIO DE CARNES E DERIVADOS LTDA")
        Fabricante.objects.filter(nome="DR. SHAR AG/SPA").update(
            nome="DR. SCHAR AG/SPA"
        )
        Fabricante.objects.filter(
            nome="EBBA S/A- EMPRESA BRASILEIRA DE BEBIDAS E ALIMENTOS S/A"
        ).update(nome="EBBA S/A - EMPRESA BRASILEIRA DE BEBIDAS E ALIMENTOS S/A")
        Fabricante.objects.filter(
            nome="FABRICA DE LATICÍNIOS LEITE FAZENDA BELA VISTA"
        ).update(nome="FABRICA DE LATICÍNIOS LEITE FAZENDA BELA VISTA LTDA")
        Fabricante.objects.filter(
            nome__in=["F DOTTO & CIA LTDA", "F. DOTTO E CIA LTDA."]
        ).update(nome="F DOTTO E CIA LTDA")
        Fabricante.objects.filter(
            nome="FEA FOODS COM E IND DE PRODUTOS ALIMENTÍCIOS LTDA ME"
        ).update(nome="FEA FOODS COMÉRCIO E INDÚSTRIA DE PRODUTOS ALIMENTÍCIOS LTDA")
        Fabricante.objects.filter(nome="FECULARIA COLI LTDA EPP").update(
            nome="FECULARIA COLI LTDA"
        )
        Fabricante.objects.filter(nome="FRESKITO PRODUTOS ALIMENTÍCIOS").update(
            nome="FRESKITO PRODUTOS ALIMENTÍCIOS LTDA"
        )
        Fabricante.objects.filter(
            nome="Grani Amici Ind. e Com.de Alimentos S.A."
        ).update(nome="Grani Amici Ind. e Com. de Alimentos S.A.")
        Fabricante.objects.filter(
            nome__in=[
                "Grani Amici Ind. e Com. Alimentos Ltda.",
                "Grani Amici Ind. e Com. de Alimentos S.A.",
            ]
        ).update(nome="GRANI AMICI INDÚSTRIA E COMÉRCIO DE ALIMENTOS S A")
        Fabricante.objects.filter(nome="HIBRA COMÉRCIO DE ALIMENTOS LTDA.").update(
            nome="HIBRA COMÉRCIO DE ALIMENTOS LTDA"
        )
        Fabricante.objects.filter(
            nome="IBS - INDUSTRIA BRASILEIRA DE SUCOS LTDA"
        ).update(nome="IBS - INDÚSTRIA BRASILEIRA DE SUCOS LTDA")
        Fabricante.objects.filter(
            nome="INDÚSTRIA E COMÉRCIO DE LATICÍNIOS FLORESCER LTDA."
        ).update(nome="INDÚSTRIA E COMÉRCIO DE LATICÍNIOS FLORESCER LTDA")
        Fabricante.objects.filter(
            nome="Indústria de massas alimentícias Rosane LTDA."
        ).update(nome="Indústria de massas alimentícias Rosane LTDA")
        Fabricante.objects.filter(
            nome="INDÚSTRIA DE TORRONE N.S. DE MONTEVERGINE LTDA"
        ).update(nome="INDÚSTRIA DE TORRONE N S DE MONTEVERGINE LTDA")
        Fabricante.objects.filter(
            nome="J A COMÉRCIO DE GÊNEROS ALIMENTÍCIOS E SERVIÇOS EIRELI"
        ).update(nome="J. A. COMÉRCIO DE GÊNEROS ALIMENTÍCIOS E SERVIÇOS EIRELI")
        Fabricante.objects.filter(nome="J MACÊDO").update(nome="J MACÊDO S A")
        Fabricante.objects.filter(
            nome__in=[
                "JASMINE COM. DE PRODUTOS ALIMENTICIOS LTDA",
                "JASMINE COM. DE PRODUTOS ALIMENTICIOS LTDA.",
            ]
        ).update(nome="JASMINE COMERCIO DE PRODUTOS ALIMENTICIOS LTDA")
        Fabricante.objects.filter(nome="JHB VITA SUCOS NATURAIS LTDA EPP").update(
            nome="JHB VITA SUCOS NATURAIS LTDA"
        )
        Fabricante.objects.filter(
            nome__in=[
                "JOSAPAR - JOAQUIM OLIVEIRA S.A PARTICIPAÇÕES",
                "JOSAPAR - JOAQUIM OLIVEIRA S.A PARTICIPAÇÕES",
                "JOSAPAR-JOAQUIM OLIVEIRA SA PARTICIPAÇÕES",
            ]
        ).update(nome="JOSAPAR JOAQUIM OLIVEIRA SA PARTICIPAÇÕES")
        Fabricante.objects.filter(nome="JOTA ALIMENTOS EIRELI").update(
            nome="JOTA ALIMENTOS LTDA"
        )
        Fabricante.objects.filter(
            nome="KALEFA INDUSTRIA DE COMERCIO DE PESCADOS"
        ).update(nome="KALEFA INDUSTRIA E COMERCIO DE PESCADOS LTDA")
        Fabricante.objects.filter(
            nome__in=[
                "KIM NETO IND. E COM. DE PANIFICAÇÃO LTDA",
                "KIM NETO IND. E COM. DE PANIFICAÇÃO LTDA.",
                "KIM NETOIND. E COM. DE PANIFICAÇÃO LTDA.",
                "KIM NETO IND. E OCM. DE PANIFICACAO LTDA",
                "KIM NETO INDUSTRIA E COMERCIO DE PANIFICAÇÃO LTDA",
            ]
        ).update(nome="KIM NETO INDUSTRIA E COMERCIO DE PANIFICAÇÃO LTDA")
        Fabricante.objects.filter(nome="LATICÍNIOS VERDE CAMPO").update(
            nome="LATICÍNIOS VERDE CAMPO LTDA"
        )
        Fabricante.objects.filter(
            nome__in=[
                "LOUIS DREYFUS COMPANY BRASIL S.A",
                "LOUIS DREYFUS COMPANY BRASIL S.A.",
                "LOUIS DREYFUS COMPANY BRASIL S/A",
            ]
        ).update(nome="LOUIS DREYFUS COMPANY BRASIL SA")
        Fabricante.objects.filter(
            nome__in=["M DIAS BRANCO S A", "M. DIAS BRANCO S.A"]
        ).update(nome="M DIAS BRANCO SA")
        Fabricante.objects.filter(nome="MILKY VITTA COMÉRCIO E INDÚSTRIA LTDA").update(
            nome="MILK VITTA COMÉRCIO E INDÚSTRIA LTDA"
        )
        Fabricante.objects.filter(nome="MOLINOS RIO DE LA PRATA SA URIBURU").update(
            nome="MOLINOS RIO DE LA PLATA S A"
        )
        Fabricante.objects.filter(
            nome__in=["Mult Beef Comercial Eireli", "Mult Beef Comercial LTDA"]
        ).update(nome="MULT BEEF COMERCIAL LTDA")
        Fabricante.objects.filter(nome="NESTLE BRASIL LTDA").update(
            nome="NESTLÉ BRASIL LTDA"
        )
        Fabricante.objects.filter(
            nome="NUTREI INDÚSTRIA E COMÉRCIO DE ALIMENTOS LTDA"
        ).update(nome="NUTREL INDÚSTRIA E COMÉRCIO DE ALIMENTOS LTDA")
        Fabricante.objects.filter(
            nome="ODEBRECHT COMÉRCIO E INDÚSTRIA DE CAFÉ LTDA"
        ).update(nome="ODEBRECHT COMÉRCIO DE INDÚSTRIA DE CAFÉ")
        Fabricante.objects.filter(nome__in=["PARATI S.A", "PARATI S.A."]).update(
            nome="PARATI SA"
        )
        Fabricante.objects.filter(nome="PASTIFÍCIO SANTA AMÁLIA S.A").update(
            nome="PASTIFÍCIO SANTA AMÁLIA SA"
        )
        Fabricante.objects.filter(
            nome__in=[
                "PANIFICADORA E DISTRIBUIDORA RE- ALI JUNIOR",
                "PANIFICADORA E DISTRIBUIDORA RE-ALI JUNIOR",
                "PANIFICADORA E DISTRIBUIDORA RE- ALI JÚNIOR",
                "PANIFICADORA E DISTRIBUIDORA RE-ALI JUNIOR LTDA",
            ]
        ).update(nome="PANIFICADORA E DISTRIBUIDORA RE ALI JUNIOR LTDA")
        Fabricante.objects.filter(
            nome__in=[
                "PASTIFÍCIO SELMI",
                "PASTIFÍCIO SELMI S.A",
                "PASTIFÍCIO SELMI S/A",
                "PASTIFÍCIO SELMI S A",
            ]
        ).update(nome="PASTIFICIO SELMI SA")
        Fabricante.objects.filter(
            nome="VALE FÉRTIL INDÚSTRIAS ALIMENTÍCIAS LTDA"
        ).update(nome="VALE FÉRTIL INDUSTRIAS ALIMENTÍCIAS LTDA")
        Fabricante.objects.filter(
            nome__in=["PRODIET NUTRIÇÃO CLÍNICA LTDA.", "PRODIET NUTRIÇÃO CLÍNICA LTDS"]
        ).update(nome="PRODIET NUTRIÇÃO CLÍNICA LTDA")
        Fabricante.objects.filter(
            nome__in=[
                "PRODUTOS DE MANDIOCA SÃO PAULO",
                "PRODUTOS DE MANDIOCA SÃO PAULO LTDA",
            ]
        ).update(nome="PRODUTOS DE MANDIOCA SAO PAULO LTDA")
        Fabricante.objects.filter(
            nome__in=["Pantera alimentos Ltda.", "pantera alimentos ltda"]
        ).update(nome="PANTERA ALIMENTOS LTDA")
        Fabricante.objects.filter(
            nome="REFINORTE - REF. DE SAL DUNORTE INDUSTRIA E COMÉRCIO LTDA."
        ).update(nome="REFINORTE - REFINARIA DE SAL DUNORTE INDÚSTRIA E COMÉRCIO LTDA")
        Fabricante.objects.filter(nome="RET PRODUTOS ALIMENTÍCIOS EIRELI").update(
            nome="RET PRODUTOS ALIMENTÍCIOS LTDA"
        )
        Fabricante.objects.filter(nome="SEM GLÚTEN MARILIS PROD. ALIM. LTDA").update(
            nome="SEM GLÚTEN MARILIS PRODUTOS ALIMENTÍCIOS LTDA"
        )
        Fabricante.objects.filter(
            nome="TRES FAZENDAS COMERCIAL DE CEREAIS EIRELI - EPP"
        ).update(nome="TRES FAZENDAS COMERCIAL DE CEREAIS EIRELLI - EPP")
        Fabricante.objects.filter(nome="STELLA D ORO ALIMENTOS LTDA").update(
            nome="STELLA D'ORO ALIMENTOS LTDA"
        )
        Fabricante.objects.filter(
            nome="USINA DE BENEFICIAMENTO LATICÍNIOS PORTO ALEGRE INDUSTRIA E COMERCIO LTDA"
        ).update(
            nome="USINA DE BENEFICIAMENTO LATICÍNIOS PORTO ALEGRE INDÚSTRIA E COMÉRCIO S A"
        )
