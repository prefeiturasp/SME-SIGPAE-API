from src.medicao_inicial.models import (
    CategoriaMedicao,
    GrupoMedicao,

    SolicitacaoMedicaoInicial,

)
from src.medicao_inicial.recreio_nas_ferias.models import RecreioNasFeriasUnidadeParticipante
from src.medicao_inicial.recreio_nas_ferias.validators.recreio_common import agrupar_tipos_alimentacao_por_categoria, valida_campo_participantes

GRUPO_CEI = "Recreio nas Férias - de 0 a 3 anos e 11 meses"
GRUPO_EMEI = "Recreio nas Férias - 4 a 14 anos"
GRUPO_COLABORADORES = "Colaboradores"

def cria_valores_medicao_participantes_cemei(instance: SolicitacaoMedicaoInicial) -> None:
    """Cria os valores de medição de participantes do Recreio nas Férias de unidades CEMEI.

    Cria registros de ``ValorMedicao`` para cada dia do período do recreio,
    considerando os grupos participantes disponíveis na unidade escolar.

    Os valores são criados apenas quando ainda não existem para o dia,
    categoria e grupo informados.

    Args:
        instance (SolicitacaoMedicaoInicial): Solicitação de medição inicial vinculada ao recreio.
    """
    recreio = instance.recreio_nas_ferias
    # participantes = recreio.unidades_participantes.filter(
    #     unidade_educacional=instance.escola
    # )
      
    # informacoes_participantes = {}
    # participantes_emei = participantes.filter(cei_ou_emei='EMEI').first()
    # if participantes_emei and participantes_emei.num_inscritos > 0:
    #     informacoes_participantes["Recreio nas Férias - 4 a 14 anos"] = participantes_emei.num_inscritos
            
    # participantes_cei = participantes.filter(cei_ou_emei='CEI').first()
    # if participantes_cei and participantes_cei.num_inscritos > 0:
    #     informacoes_participantes["Recreio nas Férias - de 0 a 3 anos e 11 meses"] = participantes_cei.num_inscritos
    
    participantes = {
        participante.cei_ou_emei: participante
        for participante in recreio.unidades_participantes.filter(
            unidade_educacional=instance.escola
        )
    }
    participantes_cei = participantes.get("CEI")
    participantes_emei = participantes.get("EMEI")
    informacoes_participantes = {}
    grupos = [
        (
            participantes_emei,
            GRUPO_EMEI,
        ),
        (
            participantes_cei,
            GRUPO_CEI,
        ),
    ]

    for participante, descricao in grupos:
        if participante and participante.num_inscritos > 0:
            informacoes_participantes[descricao] = participante.num_inscritos
        
    if existe_colaborador_cemei(participantes_cei, participantes_emei):
        total = sum(
            p.num_colaboradores
            for p in [participantes_cei, participantes_emei]
            if p is not None
        )
        informacoes_participantes[GRUPO_COLABORADORES] = total
              
    valida_campo_participantes(instance, informacoes_participantes)
    

def cria_valores_medicao_participantes_dietas_autorizadas_cemei(
    instance: SolicitacaoMedicaoInicial,
) -> None:
    pass


def existe_colaborador_cemei(participantes_cei: RecreioNasFeriasUnidadeParticipante, participantes_emei: RecreioNasFeriasUnidadeParticipante) -> bool:
    """"Verifica se existem colaboradores ativos no CEMEI.

    Retorna ``True`` quando a soma dos colaboradores participantes dos
    recreios CEI (0 a 3 anos e 11 meses) e EMEI (4 a 14 anos) da unidade
    CEMEI for maior que zero e houver pelo menos um tipo de alimentação
    associado à categoria ``"Colaboradores"`` em qualquer um dos recreios.
    Caso contrário, retorna ``False``.

    Args:
        participantes_cei (RecreioNasFeriasUnidadeParticipante):  Instância participante dos inscritos no Recreio nas Férias – CEI (0 a 3 anos e 11 meses)
            da unidade CEMEI.
        participantes_emei (RecreioNasFeriasUnidadeParticipante): Instância participante dos inscritos no Recreio nas Férias – EMEI (4 a 14 anos)
            da unidade CEMEI

    Returns:
        bool:  ``True`` se houver colaboradores com alimentação configurada dos recreios CEI ou EMEI da unidade CEMEI; caso contrário, ``False``.
    """
    participantes = [
        p for p in [participantes_cei, participantes_emei]
        if p is not None
    ]

    total_colaboradores = sum(
        p.num_colaboradores
        for p in participantes
    )

    if total_colaboradores <= 0:
        return False

    tipos_alimentacao = None

    for participante in participantes:
        tipos = participante.tipos_alimentacao.filter(
            categoria__nome=GRUPO_COLABORADORES
        )

        tipos_alimentacao = (
            tipos
            if tipos_alimentacao is None
            else tipos_alimentacao | tipos
        )

    tipos_alimentacao_map = agrupar_tipos_alimentacao_por_categoria(
        tipos_alimentacao
    )

    return bool(
        tipos_alimentacao_map.get(
            GRUPO_COLABORADORES,
            [],
        )
    )

