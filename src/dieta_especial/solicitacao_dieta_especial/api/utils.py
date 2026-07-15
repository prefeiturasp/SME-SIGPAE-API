from src.escola.models import Lote


def _verifica_se_existe_dieta_valida(aluno, queryset, status_dieta, escola):
    return [
        s
        for s in aluno.dietas_especiais.all()
        if s.rastro_escola == escola and s.status in status_dieta
    ]


def filtrar_alunos_com_dietas_nos_status_e_rastro_escola(
    queryset, status_dieta, escola
):
    uuids_alunos_para_excluir = []
    for aluno in queryset:
        if not _verifica_se_existe_dieta_valida(aluno, queryset, status_dieta, escola):
            uuids_alunos_para_excluir.append(aluno.uuid)
    queryset = queryset.exclude(uuid__in=uuids_alunos_para_excluir)
    return queryset


def trata_lotes_dict_duplicados(lotes_dict):
    lotes_ = []
    for lote_uuid in lotes_dict.values():
        try:
            lotes_.append(
                tuple([Lote.objects.get(uuid=lote_uuid).__str__(), lote_uuid])
            )
        except Lote.DoesNotExist:
            continue
    return dict(lotes_)
