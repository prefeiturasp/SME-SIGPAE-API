import uuid as uuid_module
from datetime import date, datetime, timedelta

from django.db.models import Count
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.escola.api.serializers import (
    PeriodoEscolarParaFiltroSerializer,
    TipoUnidadeParaFiltroSerializer,
)
from src.escola.models import Escola, Lote, PeriodoEscolar, TipoUnidadeEscolar
from src.terceirizada.models import Edital

from ..models import DiaLetivoSIGPAE


def parse_date(value: str) -> date:
    """Converte uma string no formato DD/MM/YYYY para um objeto date.

    Args:
        value: String contendo a data no formato DD/MM/YYYY.

    Returns:
        datetime.date correspondente à string informada.

    Raises:
        ValidationError: Se a string não estiver no formato esperado.
    """
    try:
        return datetime.strptime(value, "%d/%m/%Y").date()
    except ValueError:
        raise ValidationError(f"Formato de data inválido: {value}. Use DD/MM/YYYY")


def python_weekday_to_business(weekday: int) -> int:
    """Converte o weekday do Python (0=Monday) para o formato de negócio.

    Atualmente, retorna o mesmo valor sem conversão. Serve como ponto
    de extensão para futuros mapeamentos de dias da semana.

    Args:
        weekday: Inteiro representando o dia da semana (0=Monday).

    Returns:
        Inteiro representando o dia da semana no formato de negócio.
    """
    return weekday


class RecorrenciaSerializer(serializers.Serializer):
    """Serializador para validar os dados de recorrência de dias letivos.

    Define o intervalo de datas, os períodos escolares e os dias da
    semana em que os dias letivos devem ser criados.
    """

    data_inicial = serializers.CharField()
    data_final = serializers.CharField()
    periodos_escolares = serializers.ListField(child=serializers.UUIDField())
    dias_semana = serializers.ListField(child=serializers.CharField())

    def validate_data_inicial(self, value: str) -> date:
        """Valida e converte a data inicial para o formato date."""
        return parse_date(value)

    def validate_data_final(self, value: str) -> date:
        """Valida e converte a data final para o formato date."""
        return parse_date(value)

    def validate(self, attrs: dict) -> dict:
        """Valida regras de negócio da recorrência.

        Verifica se data_inicial não é maior que data_final e se todos
        os valores em dias_semana estão no intervalo válido (0 a 6).

        Raises:
            ValidationError: Se alguma validação falhar.
        """
        if attrs["data_inicial"] > attrs["data_final"]:
            raise ValidationError("data_inicial não pode ser maior que data_final")
        for dia in attrs["dias_semana"]:
            try:
                dia_int = int(dia)
                if dia_int < 0 or dia_int > 6:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValidationError(
                    f"dias_semana deve conter valores entre 0 e 6. "
                    f"Valor inválido: {dia}"
                )
        return attrs


class DiaLetivoCreateSerializer(serializers.Serializer):
    """Serializador para criação em lote de dias letivos.

    Recebe uma ou mais recorrências e as entidades relacionadas (lotes,
    tipos de unidades e unidades educacionais) para gerar os registros
    de dias letivos no banco.
    """

    recorrencias = RecorrenciaSerializer(many=True)
    lotes = serializers.ListField(child=serializers.UUIDField())
    tipos_unidades = serializers.ListField(child=serializers.UUIDField())
    unidades_educacionais = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list
    )

    def validate_lotes(self, value: list) -> list:
        """Valida se o campo lotes não está vazio."""
        if not value:
            raise ValidationError("lotes é obrigatório")
        return value

    def validate_tipos_unidades(self, value: list) -> list:
        """Valida se o campo tipos_unidades não está vazio."""
        if not value:
            raise ValidationError("tipos_unidades é obrigatório")
        return value

    def validate_recorrencias(self, value: list) -> list:
        """Valida se o campo recorrencias não está vazio."""
        if not value:
            raise ValidationError("recorrencias é obrigatório")
        return value

    def create(self, validated_data: dict) -> list[DiaLetivoSIGPAE]:
        """Cria os dias letivos em lote com verificações otimizadas."""
        recorrencias = validated_data["recorrencias"]
        lotes_uuids = validated_data["lotes"]
        tipos_unidades_uuids = validated_data["tipos_unidades"]
        unidades_educacionais_uuids = validated_data.get("unidades_educacionais", [])

        lotes, tipos_unidades, escolas = self._resolve_entidades(
            lotes_uuids, tipos_unidades_uuids, unidades_educacionais_uuids
        )
        periodos_map = self._resolve_periodos(recorrencias)
        user = self.context["request"].user

        dias_a_criar, all_dates, all_periodo_ids = self._coletar_datas(
            recorrencias, periodos_map
        )
        if not dias_a_criar:
            return []

        self._checa_duplicacao_consolidada(
            dias_a_criar, all_dates, all_periodo_ids, escolas
        )

        to_create = [
            DiaLetivoSIGPAE(data=d, criado_por=user, uuid=uuid_module.uuid4())
            for d, _ in dias_a_criar
        ]
        created = DiaLetivoSIGPAE.objects.bulk_create(to_create)

        self._bulk_insert_m2m(created, dias_a_criar, lotes, tipos_unidades, escolas)

        return created

    def _resolve_entidades(
        self,
        lotes_uuids: list,
        tipos_unidades_uuids: list,
        unidades_educacionais_uuids: list,
    ) -> tuple[list[Lote], list[TipoUnidadeEscolar], list[Escola]]:
        """Busca e valida lotes, tipos de unidade e escolas pelos UUIDs."""
        lotes = list(Lote.objects.filter(uuid__in=lotes_uuids))
        tipos_unidades = list(
            TipoUnidadeEscolar.objects.filter(uuid__in=tipos_unidades_uuids)
        )
        escolas = (
            list(Escola.objects.filter(uuid__in=unidades_educacionais_uuids))
            if unidades_educacionais_uuids
            else []
        )

        if len(lotes) != len(lotes_uuids):
            raise ValidationError("Um ou mais lotes não foram encontrados")
        if len(tipos_unidades) != len(tipos_unidades_uuids):
            raise ValidationError("Um ou mais tipos de unidade não foram encontrados")
        if unidades_educacionais_uuids and len(escolas) != len(
            unidades_educacionais_uuids
        ):
            raise ValidationError(
                "Uma ou mais unidades educacionais não foram encontradas"
            )

        return lotes, tipos_unidades, escolas

    def _resolve_periodos(
        self, recorrencias: list[dict]
    ) -> dict[uuid_module.UUID, PeriodoEscolar]:
        """Busca e valida todos os períodos referenciados nas recorrências."""
        all_periodo_uuids = set()
        for rec in recorrencias:
            all_periodo_uuids.update(rec["periodos_escolares"])

        periodos_map = {
            p.uuid: p for p in PeriodoEscolar.objects.filter(uuid__in=all_periodo_uuids)
        }
        if len(periodos_map) != len(all_periodo_uuids):
            raise ValidationError("Um ou mais períodos escolares não foram encontrados")

        return periodos_map

    def _coletar_datas(
        self,
        recorrencias: list[dict],
        periodos_map: dict,
    ) -> tuple[list, set, set]:
        """Percorre as recorrências e coleta todas as datas e períodos."""
        dias_a_criar = []
        all_dates = set()
        all_periodo_ids = set()

        for rec in recorrencias:
            data_inicial = rec["data_inicial"]
            data_final = rec["data_final"]
            periodos = [periodos_map[u] for u in rec["periodos_escolares"]]
            dias_semana = {int(d) for d in rec["dias_semana"]}

            current = data_inicial
            while current <= data_final:
                if python_weekday_to_business(current.weekday()) in dias_semana:
                    dias_a_criar.append((current, periodos))
                    all_dates.add(current)
                    for p in periodos:
                        all_periodo_ids.add(p.pk)
                current += timedelta(days=1)

        return dias_a_criar, all_dates, all_periodo_ids

    def _checa_duplicacao_consolidada(
        self,
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        all_dates: set[date],
        all_periodo_ids: set[int],
        escolas: list[Escola],
    ) -> None:
        """Coordena a verificação de duplicatas intra-batch e contra o banco."""
        if not all_dates or not all_periodo_ids:
            return

        self._checa_duplicacao_intra_batch(dias_a_criar, escolas)

        if escolas:
            self._checa_duplicacao_banco_com_escolas(
                dias_a_criar, all_dates, all_periodo_ids, escolas
            )
        else:
            self._checa_duplicacao_banco_sem_escolas(
                dias_a_criar, all_dates, all_periodo_ids
            )

    def _checa_duplicacao_intra_batch(
        self,
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        escolas: list[Escola],
    ) -> None:
        """Verifica se há pares (data, período) duplicados dentro do lote."""
        seen_pairs = set()
        for data_val, periodos in dias_a_criar:
            for periodo in periodos:
                pair = (data_val, periodo.pk)
                if pair in seen_pairs:
                    if escolas:
                        raise ValidationError(
                            f"Já existe um DiaLetivo cadastrado para a data "
                            f"{data_val.strftime('%d/%m/%Y')}, "
                            f"escola {escolas[0].nome} e "
                            f"período escolar {periodo.nome}"
                        )
                    raise ValidationError(
                        f"Já existe um DiaLetivo cadastrado para a data "
                        f"{data_val.strftime('%d/%m/%Y')} e "
                        f"período escolar {periodo.nome}"
                    )
                seen_pairs.add(pair)

    def _checa_duplicacao_banco_com_escolas(
        self,
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        all_dates: set[date],
        all_periodo_ids: set[int],
        escolas: list[Escola],
    ) -> None:
        """Verifica conflitos contra registros existentes com escolas."""
        escola_ids = [e.pk for e in escolas]
        existing = set(
            DiaLetivoSIGPAE.objects.filter(
                data__in=all_dates,
                periodos_escolares__id__in=all_periodo_ids,
                escolas__id__in=escola_ids,
            ).values_list("data", "periodos_escolares__id", "escolas__id")
        )
        if not existing:
            return

        for data_val, periodos in dias_a_criar:
            for periodo in periodos:
                for escola in escolas:
                    if (data_val, periodo.pk, escola.pk) in existing:
                        raise ValidationError(
                            f"Já existe um DiaLetivo cadastrado para a data "
                            f"{data_val.strftime('%d/%m/%Y')}, "
                            f"escola {escola.nome} e "
                            f"período escolar {periodo.nome}"
                        )

    def _checa_duplicacao_banco_sem_escolas(
        self,
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        all_dates: set[date],
        all_periodo_ids: set[int],
    ) -> None:
        """Verifica conflitos contra registros existentes sem escolas."""
        existing = set(
            DiaLetivoSIGPAE.objects.filter(
                data__in=all_dates,
                periodos_escolares__id__in=all_periodo_ids,
            )
            .annotate(escola_count=Count("escolas"))
            .filter(escola_count=0)
            .values_list("data", "periodos_escolares__id")
        )
        if not existing:
            return

        for data_val, periodos in dias_a_criar:
            for periodo in periodos:
                if (data_val, periodo.pk) in existing:
                    raise ValidationError(
                        f"Já existe um DiaLetivo cadastrado para a data "
                        f"{data_val.strftime('%d/%m/%Y')} e "
                        f"período escolar {periodo.nome}"
                    )

    # ------------------------------------------------------------------
    # Inserção em lote dos relacionamentos M2M
    # ------------------------------------------------------------------

    def _bulk_insert_m2m(
        self,
        created: list[DiaLetivoSIGPAE],
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        lotes: list[Lote],
        tipos_unidades: list[TipoUnidadeEscolar],
        escolas: list[Escola],
    ) -> None:
        """Insere em lote todos os registros nas tabelas intermediárias M2M."""
        self._bulk_insert_small_m2m(created, dias_a_criar, lotes, tipos_unidades)
        if escolas:
            self._bulk_insert_escolas(created, escolas)

    def _bulk_insert_small_m2m(
        self,
        created: list[DiaLetivoSIGPAE],
        dias_a_criar: list[tuple[date, list[PeriodoEscolar]]],
        lotes: list[Lote],
        tipos_unidades: list[TipoUnidadeEscolar],
    ) -> None:
        """Insere em lote os relacionamentos com lotes, tipos e períodos."""
        LoteThrough = DiaLetivoSIGPAE.lotes.through
        TipoUEThrough = DiaLetivoSIGPAE.tipos_unidade_escolar.through
        PeriodoThrough = DiaLetivoSIGPAE.periodos_escolares.through

        lote_batch = []
        tipo_batch = []
        periodo_batch = []

        for idx, dia_letivo in enumerate(created):
            _, periodos = dias_a_criar[idx]

            for lote in lotes:
                lote_batch.append(LoteThrough(dialetivosigpae=dia_letivo, lote=lote))
            for tipo in tipos_unidades:
                tipo_batch.append(
                    TipoUEThrough(dialetivosigpae=dia_letivo, tipounidadeescolar=tipo)
                )
            for periodo in periodos:
                periodo_batch.append(
                    PeriodoThrough(dialetivosigpae=dia_letivo, periodoescolar=periodo)
                )

            self._flush_batch(LoteThrough, lote_batch)
            self._flush_batch(TipoUEThrough, tipo_batch)
            self._flush_batch(PeriodoThrough, periodo_batch)

        LoteThrough.objects.bulk_create(lote_batch)
        TipoUEThrough.objects.bulk_create(tipo_batch)
        PeriodoThrough.objects.bulk_create(periodo_batch)

    @staticmethod
    def _flush_batch(through_model, batch: list, batch_size: int = 1000) -> None:
        """Esvazia o batch via bulk_create se atingiu o tamanho limite."""
        if len(batch) >= batch_size:
            through_model.objects.bulk_create(batch)
            batch.clear()

    def _bulk_insert_escolas(
        self,
        created: list[DiaLetivoSIGPAE],
        escolas: list[Escola],
    ) -> None:
        """Insere em lote os relacionamentos com escolas usando batches."""
        BATCH_SIZE = 1000
        EscolaThrough = DiaLetivoSIGPAE.escolas.through
        escola_batch = []

        for dia_letivo in created:
            for escola in escolas:
                escola_batch.append(
                    EscolaThrough(dialetivosigpae=dia_letivo, escola=escola)
                )
                if len(escola_batch) >= BATCH_SIZE:
                    EscolaThrough.objects.bulk_create(escola_batch)
                    escola_batch.clear()

        if escola_batch:
            EscolaThrough.objects.bulk_create(escola_batch)


class LoteNomeIniciaisSerializer(serializers.ModelSerializer):
    """Serializador reduzido de Lote com uuid, nome e iniciais."""

    class Meta:
        model = Lote
        fields = ("uuid", "nome", "iniciais")


class DiaLetivoSerializer(serializers.ModelSerializer):
    """Serializador de leitura para dias letivos.

    Expõe os dados do dia letivo com as entidades relacionadas
    (lotes, tipos de unidade escolar, períodos escolares), além
    da contagem de unidades escolares e a lista de números dos
    editais associados às escolas do registro.
    """

    lotes = LoteNomeIniciaisSerializer(many=True)
    tipos_unidade_escolar = TipoUnidadeParaFiltroSerializer(many=True)
    periodos_escolares = PeriodoEscolarParaFiltroSerializer(many=True)
    unidades_escolares = serializers.SerializerMethodField()
    editais_numeros = serializers.SerializerMethodField()

    def get_unidades_escolares(self, obj: DiaLetivoSIGPAE):
        """Retorna os nomes das escolas vinculadas (até 3) ou o total."""
        count = obj.escolas.count()
        if count == 0:
            return None
        if 1 <= count <= 3:
            nomes = obj.escolas.values_list("nome", flat=True)
            return ", ".join(nomes)
        return count

    def get_editais_numeros(self, obj: DiaLetivoSIGPAE):
        """Retorna os números dos editais das escolas vinculadas.

        Utiliza a property ``editais`` do model Escola para obter os
        UUIDs dos editais e, em seguida, consulta os números desses
        editais no banco. Retorna ``None`` quando não há escolas ou
        nenhum edital associado.
        """
        escolas = obj.escolas.filter(
            lote__isnull=False,
            lote__contratos_do_lote__edital__isnull=False,
            lote__contratos_do_lote__encerrado=False,
        )
        if not escolas.exists():
            return None

        edital_uuids = set()
        for escola in escolas:
            edital_uuids.update(escola.editais)

        if not edital_uuids:
            return None

        return list(
            Edital.objects.filter(uuid__in=edital_uuids)
            .values_list("numero", flat=True)
            .distinct()
        )

    class Meta:
        model = DiaLetivoSIGPAE
        fields = (
            "uuid",
            "data",
            "lotes",
            "tipos_unidade_escolar",
            "periodos_escolares",
            "unidades_escolares",
            "editais_numeros",
        )
