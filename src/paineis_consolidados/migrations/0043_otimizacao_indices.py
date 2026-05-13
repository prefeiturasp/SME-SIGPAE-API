from django.db import migrations


class Migration(migrations.Migration):
    """Adiciona índices nas tabelas-fonte da view solicitacoes_consolidadas
    para otimizar os endpoints do painel de gestão alimentação.

    Inclui:
    - Extensão pg_trgm para busca textual com índices GIN
    - Índices B-tree compostos nos campos mais filtrados/ordenados
    - Índices GIN trigram nos campos de texto da busca
    """

    atomic = False

    dependencies = [
        ("paineis_consolidados", "0042_solicitacoes"),
    ]

    operations = [
        # ==========================================
        # 1. Extensão pg_trgm (busca textual difusa)
        # ==========================================
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="",
        ),
        # ==========================================
        # 2. Índices na tabela de logs
        # Usada para filtrar por status_evento e ordenar por data_log
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_logs_status_evento_criado_em "
            "ON dados_comuns_logsolicitacoesusuario (status_evento, criado_em DESC);",
            reverse_sql="DROP INDEX IF EXISTS idx_logs_status_evento_criado_em;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_logs_uuid_original "
            "ON dados_comuns_logsolicitacoesusuario (uuid_original);",
            reverse_sql="DROP INDEX IF EXISTS idx_logs_uuid_original;",
        ),
        # ==========================================
        # 3. Índices nas tabelas de escola/lote
        # Usados para filtros por lote e busca textual
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_escola_nome_trgm "
            "ON escola_escola USING GIN (nome gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS idx_escola_nome_trgm;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_lote_nome_trgm "
            "ON escola_lote USING GIN (nome gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS idx_lote_nome_trgm;",
        ),
        # ==========================================
        # 4. Índices nas principais tabelas de solicitação
        # Otimizam a filtragem por status_atual em cada tipo de solicitação
        # ==========================================
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dieta_especial_status "
            "ON dieta_especial_solicitacaodietaespecial (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_dieta_especial_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alteracao_cardapio_status "
            "ON cardapio_alteracaocardapio (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_alteracao_cardapio_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inversao_cardapio_status "
            "ON cardapio_inversaocardapio (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_inversao_cardapio_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_grupo_inclusao_alimentacao_status "
            "ON inclusao_alimentacao_grupoinclusaoalimentacaonormal (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_grupo_inclusao_alimentacao_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_inclusao_alimentacao_continua_status "
            "ON inclusao_alimentacao_inclusaoalimentacaocontinua (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_inclusao_alimentacao_continua_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kit_lanche_avulsa_status "
            "ON kit_lanche_solicitacaokitlancheavulsa (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_kit_lanche_avulsa_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_suspensao_alimentacao_status "
            "ON cardapio_gruposuspensaoalimentacao (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_suspensao_alimentacao_status;",
        ),
        migrations.RunSQL(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_kit_lanche_unificada_status "
            "ON kit_lanche_solicitacaokitlancheunificada (status);",
            reverse_sql="DROP INDEX IF EXISTS idx_kit_lanche_unificada_status;",
        ),
    ]
