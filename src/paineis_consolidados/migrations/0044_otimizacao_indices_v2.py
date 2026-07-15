from django.db import migrations


class Migration(migrations.Migration):
    """Adiciona índices adicionais nas tabelas-fonte da view solicitacoes_consolidadas
    para otimizar os endpoints do painel de gestão alimentação.

    Inclui:
    - Índice composto para LATERAL JOIN em escola_historicoescola
    - Índice covering para join+filtro de logs
    - Índices de status nas tabelas CEI/CEMEI faltantes
    """

    atomic = False

    dependencies = [
        ("paineis_consolidados", "0043_otimizacao_indices"),
    ]

    operations = [
        # ==========================================
        # 1. Índice composto para LATERAL JOIN
        # usado na subquery de histórico da escola
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_hist_escola_lateral "
            "ON escola_historicoescola (escola_id, data_final DESC, data_inicial);",
            reverse_sql="DROP INDEX IF EXISTS idx_hist_escola_lateral;",
        ),
        # ==========================================
        # 2. Índice covering para logs join + filtro
        # Otimiza join por uuid_original + filtro status_evento + ordenação
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_logs_uuid_status_criado "
            "ON dados_comuns_logsolicitacoesusuario (uuid_original, status_evento, criado_em DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_logs_uuid_status_criado;",
        ),
        # ==========================================
        # 3. Índices de status nas tabelas CEI/CEMEI
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inclusao_da_cei_status "
            "ON inclusao_alimentacao_inclusaoalimentacaodacei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_inclusao_da_cei_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_alt_cardapio_cei_status "
            "ON cardapio_alteracaocardapiocei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_alt_cardapio_cei_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_kit_lanche_cei_avulsa_status "
            "ON kit_lanche_solicitacaokitlancheceiavulsa (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_kit_lanche_cei_avulsa_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_susp_alimentacao_cei_status "
            "ON cardapio_suspensaoalimentacaodacei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_susp_alimentacao_cei_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_kit_lanche_cemei_status "
            "ON kit_lanche_solicitacaokitlanchecemei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_kit_lanche_cemei_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inclusao_cemei_status "
            "ON inclusao_alimentacao_inclusaodealimentacaocemei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_inclusao_cemei_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_alt_cardapio_cemei_status "
            "ON cardapio_alteracaocardapiocemei (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_alt_cardapio_cemei_status;",
        ),
    ]
