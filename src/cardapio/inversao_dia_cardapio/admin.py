from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from src.cardapio.inversao_dia_cardapio.models import InversaoCardapio


@admin.register(InversaoCardapio)
class InversaoCardapioModelAdmin(admin.ModelAdmin):
    """Admin do Django para solicitacoes de inversao de cardapio.

    Configura a listagem administrativa de :class:`InversaoCardapio`,
    exibindo as datas envolvidas na inversao, a escola relacionada, o
    status atual da solicitacao e os tipos de alimentacao vinculados.
    Tambem habilita filtros por intervalo de datas, status, lote e tipo
    de alimentacao, alem da busca textual por nome e codigo EOL da escola.

    Attributes:
            list_display (tuple[str, ...]): Colunas exibidas na listagem do admin.
                    Valores: ``("get_data_de", "get_data_para", "get_data_de_2", "get_data_para_2", "get_escola", "status", "get_tipos_alimentacao")``.
            search_fields (tuple[str, ...]): Campos consultados pela busca textual do admin.
                    Valores: ``("rastro_escola__nome", "rastro_escola__codigo_eol", "escola__nome", "escola__codigo_eol")``.
            search_help_text (str): Texto auxiliar exibido abaixo do campo de busca.
                    Valores: ``"Pesquisa por: nome da escola, codigo eol da escola"``.
            list_filter (tuple[object, ...]): Filtros laterais disponiveis na listagem.
                    Valores: ``(("data_de_inversao", DateRangeFilter), ("data_para_inversao", DateRangeFilter), "status", "rastro_lote", "tipos_alimentacao")``.
            list_select_related (tuple[str, ...]): Relacoes carregadas via join na listagem.
                    Valores: ``("escola", "rastro_escola", "rastro_lote")``.
    """

    list_display = (
        "get_data_de",
        "get_data_para",
        "get_data_de_2",
        "get_data_para_2",
        "get_escola",
        "status",
        "get_tipos_alimentacao",
    )
    search_fields = (
        "rastro_escola__nome",
        "rastro_escola__codigo_eol",
        "escola__nome",
        "escola__codigo_eol",
    )
    search_help_text = "Pesquisa por: nome da escola, codigo eol da escola"
    list_filter = (
        ("data_de_inversao", DateRangeFilter),
        ("data_para_inversao", DateRangeFilter),
        "status",
        "rastro_lote",
        "tipos_alimentacao",
    )
    list_select_related = ("escola", "rastro_escola", "rastro_lote")

    def get_queryset(self, request):
        """Retorna a queryset otimizada para a listagem do admin.

        Args:
                request (HttpRequest): Requisicao atual do Django Admin.

        Returns:
                django.db.models.QuerySet: Queryset com os tipos de alimentacao
                        previamente carregados para evitar consultas extras.
        """
        queryset = super().get_queryset(request)
        return queryset.prefetch_related("tipos_alimentacao")

    @staticmethod
    def _format_date(date_value):
        """Formata datas para exibicao amigavel na listagem.

        Args:
                date_value (datetime.date | None): Data que sera exibida no admin.

        Returns:
                str: Data no formato ``dd/mm/YYYY`` ou ``"-"`` quando ausente.
        """
        return date_value.strftime("%d/%m/%Y") if date_value else "-"

    @admin.display(description="Data de", ordering="data_de_inversao")
    def get_data_de(self, obj):
        """Retorna a primeira data de origem da inversao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Data de origem formatada para exibicao no admin.
        """
        return self._format_date(obj.data_de_inversao)

    @admin.display(description="Data para", ordering="data_para_inversao")
    def get_data_para(self, obj):
        """Retorna a primeira data de destino da inversao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Data de destino formatada para exibicao no admin.
        """
        return self._format_date(obj.data_para_inversao)

    @admin.display(description="Data de 2", ordering="data_de_inversao_2")
    def get_data_de_2(self, obj):
        """Retorna a segunda data de origem da inversao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Segunda data de origem formatada para exibicao no admin.
        """
        return self._format_date(obj.data_de_inversao_2)

    @admin.display(description="Data para 2", ordering="data_para_inversao_2")
    def get_data_para_2(self, obj):
        """Retorna a segunda data de destino da inversao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Segunda data de destino formatada para exibicao no admin.
        """
        return self._format_date(obj.data_para_inversao_2)

    @admin.display(description="Escola", ordering="rastro_escola__nome")
    def get_escola(self, obj):
        """Retorna a escola associada a solicitacao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Nome da escola vinculada, ou ``"-"`` quando indisponivel.
        """
        escola = obj.rastro_escola or obj.escola
        return escola.nome if escola else "-"

    @admin.display(description="Tipos de alimentacao")
    def get_tipos_alimentacao(self, obj):
        """Retorna os tipos de alimentacao vinculados a inversao.

        Args:
                obj (InversaoCardapio): Solicitacao exibida na linha atual.

        Returns:
                str: Nomes dos tipos de alimentacao separados por virgula.
        """
        tipos_alimentacao = [tipo.nome for tipo in obj.tipos_alimentacao.all()]
        return ", ".join(tipos_alimentacao) if tipos_alimentacao else "-"
