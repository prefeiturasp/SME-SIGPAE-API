DROP VIEW IF EXISTS solicitacoes_consolidadas;


CREATE OR REPLACE VIEW solicitacoes_consolidadas AS
SELECT cardapio.id,
       cardapio.uuid,
       cardapio.data_inicial      AS data_evento,
       cardapio.criado_em         AS criado_em,
       lote.nome                  AS lote_nome,
       dre.nome                   AS dre_nome,
       escola.nome                AS escola_nome,
       terceirizada.nome_fantasia AS terceirizada_nome,
       lote.uuid                  as lote_uuid,
       dre.uuid                   as dre_uuid,
       escola.uuid                as escola_uuid,
       terceirizada.uuid          as terceirizada_uuid,
       'ALT_CARDAPIO'             AS tipo_doc,
       'Alteração de Cardápio'    AS desc_doc,
       0                          AS numero_alunos,
       cardapio.status            AS status_atual,
       logs.criado_em             AS data_log,
       logs.status_evento
FROM cardapio_alteracaocardapio AS cardapio
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = cardapio.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = cardapio.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = cardapio.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = cardapio.rastro_escola_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada ON terceirizada.id = cardapio.rastro_terceirizada_id
UNION
SELECT inversao_cardapio.id,
       inversao_cardapio.uuid,
       CASE
           WHEN cardapio_de.data <= cardapio_para.data THEN cardapio_de.data
           ELSE cardapio_para.data
           END                       AS data_evento,
       inversao_cardapio.criado_em   AS criado_em,
       lote.nome                     AS lote_nome,
       dre.nome                      AS dre_nome,
       escola.nome                   AS escola_nome,
       terceirizada.nome_fantasia    AS terceirizada_nome,
       lote.uuid                     as lote_uuid,
       dre.uuid                      as dre_uuid,
       escola.uuid                   as escola_uuid,
       terceirizada.uuid             as terceirizada_uuid,
       'INV_CARDAPIO'                AS tipo_doc,
       'Inversão de dia de Cardápio' AS desc_doc,
       0                             AS numero_alunos,
       inversao_cardapio.status      AS status_atual,
       logs.criado_em                AS data_log,
       logs.status_evento
FROM cardapio_inversaocardapio AS inversao_cardapio
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = inversao_cardapio.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = inversao_cardapio.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = inversao_cardapio.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = inversao_cardapio.rastro_escola_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada
                   ON terceirizada.id = inversao_cardapio.rastro_terceirizada_id
         LEFT JOIN cardapio_cardapio AS cardapio_de ON cardapio_de.id = inversao_cardapio.cardapio_de_id
         LEFT JOIN cardapio_cardapio AS cardapio_para ON cardapio_para.id = inversao_cardapio.cardapio_para_id
UNION
SELECT inc_aliment_normal.id,
       inc_aliment_normal.uuid,
       min(inc_alimentacao_item.data)        AS data_evento,
       inc_aliment_normal.criado_em          AS criado_em,
       lote.nome                             AS lote_nome,
       dre.nome                              AS dre_nome,
       escola.nome                           AS escola_nome,
       terceirizada.nome_fantasia            AS terceirizada_nome,
       lote.uuid                             as lote_uuid,
       dre.uuid                              as dre_uuid,
       escola.uuid                           as escola_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA'                        AS tipo_doc,
       'Inclusão de Alimentação'             AS desc_doc,
       sum(quantidade_periodo.numero_alunos) AS numero_alunos,
       inc_aliment_normal.status             AS status_atual,
       logs.criado_em                        AS data_log,
       logs.status_evento
FROM inclusao_alimentacao_grupoinclusaoalimentacaonormal AS inc_aliment_normal
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = inc_aliment_normal.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = inc_aliment_normal.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = inc_aliment_normal.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = inc_aliment_normal.rastro_escola_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada
                   ON terceirizada.id = inc_aliment_normal.rastro_terceirizada_id
         LEFT JOIN inclusao_alimentacao_quantidadeporperiodo as quantidade_periodo
                   ON quantidade_periodo.grupo_inclusao_normal_id = inc_aliment_normal.id
         LEFT JOIN inclusao_alimentacao_inclusaoalimentacaonormal AS inc_alimentacao_item
                   ON inc_alimentacao_item.grupo_inclusao_id = inc_aliment_normal.id
GROUP BY inc_aliment_normal.id,
         lote.nome,
         dre.nome,
         escola.nome,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
UNION
SELECT inc_aliment_continua.id,
       inc_aliment_continua.uuid,
       inc_aliment_continua.data_inicial     AS data_evento,
       inc_aliment_continua.criado_em        AS criado_em,
       lote.nome                             AS lote_nome,
       dre.nome                              AS dre_nome,
       escola.nome                           AS escola_nome,
       terceirizada.nome_fantasia            AS terceirizada_nome,
       lote.uuid                             as lote_uuid,
       dre.uuid                              as dre_uuid,
       escola.uuid                           as escola_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA_CONTINUA'               AS tipo_doc,
       'Inclusão de Alimentação Contínua'    AS desc_doc,
       sum(quantidade_periodo.numero_alunos) AS numero_alunos,
       inc_aliment_continua.status           AS status_atual,
       logs.criado_em                        AS data_log,
       logs.status_evento
FROM inclusao_alimentacao_inclusaoalimentacaocontinua AS inc_aliment_continua
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = inc_aliment_continua.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = inc_aliment_continua.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = inc_aliment_continua.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = inc_aliment_continua.rastro_escola_id
         LEFT JOIN inclusao_alimentacao_quantidadeporperiodo as quantidade_periodo
                   ON quantidade_periodo.grupo_inclusao_normal_id = inc_aliment_continua.id
         LEFT JOIN terceirizada_terceirizada AS terceirizada
                   ON terceirizada.id = inc_aliment_continua.rastro_terceirizada_id

GROUP BY inc_aliment_continua.id,
         lote.nome,
         dre.nome,
         escola.nome,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
UNION
SELECT kit_lanche_avulso.id,
       kit_lanche_avulso.uuid,
       kit_lanche_base.data                AS data_evento,
       kit_lanche_base.criado_em           AS criado_em,
       lote.nome                           AS lote_nome,
       dre.nome                            AS dre_nome,
       escola.nome                         AS escola_nome,
       terceirizada.nome_fantasia          AS terceirizada_nome,
       lote.uuid                           as lote_uuid,
       dre.uuid                            as dre_uuid,
       escola.uuid                         as escola_uuid,
       terceirizada.uuid                   as terceirizada_uuid,
       'KIT_LANCHE_AVULSA'                 AS tipo_doc,
       'Kit Lanche Passeio'                AS desc_doc,
       kit_lanche_avulso.quantidade_alunos AS numero_alunos,
       kit_lanche_avulso.status            AS status_atual,
       logs.criado_em                      AS data_log,
       logs.status_evento
FROM kit_lanche_solicitacaokitlancheavulsa AS kit_lanche_avulso
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = kit_lanche_avulso.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = kit_lanche_avulso.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = kit_lanche_avulso.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = kit_lanche_avulso.rastro_escola_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada
                   ON terceirizada.id = kit_lanche_avulso.rastro_terceirizada_id
         LEFT JOIN kit_lanche_solicitacaokitlanche AS kit_lanche_base
                   ON kit_lanche_base.id = kit_lanche_avulso.solicitacao_kit_lanche_id
UNION
SELECT grupo_suspensao.id,
       grupo_suspensao.uuid,
       min(susp_alimentacao_item.data) AS data_evento,
       grupo_suspensao.criado_em       AS criado_em,
       lote.nome                       AS lote_nome,
       dre.nome                        AS dre_nome,
       escola.nome                     AS escola_nome,
       terceirizada.nome_fantasia      AS terceirizada_nome,
       lote.uuid                       as lote_uuid,
       dre.uuid                        as dre_uuid,
       escola.uuid                     as escola_uuid,
       terceirizada.uuid               as terceirizada_uuid,
       'SUSP_ALIMENTACAO'              AS tipo_doc,
       'Suspensão de Alimentação'      AS desc_doc,
       0                               AS numero_alunos,
       grupo_suspensao.status          AS status_atual,
       logs.criado_em                  AS data_log,
       logs.status_evento
FROM cardapio_gruposuspensaoalimentacao AS grupo_suspensao
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = grupo_suspensao.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = grupo_suspensao.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = grupo_suspensao.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = grupo_suspensao.rastro_escola_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada ON terceirizada.id = grupo_suspensao.rastro_terceirizada_id
         LEFT JOIN cardapio_suspensaoalimentacao AS susp_alimentacao_item
                   ON susp_alimentacao_item.grupo_suspensao_id = grupo_suspensao.id
GROUP BY grupo_suspensao.id,
         lote.nome,
         escola.nome,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         dre.nome,
         logs.criado_em,
         logs.status_evento
UNION

SELECT kit_lanche_unificado.id,
       kit_lanche_unificado.uuid,
       kit_lanche_item.data                               AS data_evento,
       kit_lanche_item.criado_em                          AS criado_em,
       lote.nome                                          AS lote_nome,
       dre.nome                                           AS dre_nome,
       'VARIAS_ESCOLAS'                                   AS escola_nome,
       terceirizada.nome_fantasia                         AS terceirizada_nome,
       lote.uuid                                          as lote_uuid,
       dre.uuid                                           as dre_uuid,
       '6b0462a8-f739-11e9-8f0b-362b9e155667'             as escola_uuid, -- para compatibilidade, esse uuid é pra passar somente
       terceirizada.uuid                                  as terceirizada_uuid,
       'KIT_LANCHE_UNIFICADA'                             AS tipo_doc,
       'Kit Lanche Passeio Unificado'                     AS desc_doc,
       sum(kit_lanche_escolaquantidade.quantidade_alunos) AS numero_alunos,
       kit_lanche_unificado.status                        AS status_atual,
       logs.criado_em                                     AS data_log,
       logs.status_evento
FROM kit_lanche_solicitacaokitlancheunificada AS kit_lanche_unificado
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = kit_lanche_unificado.uuid
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = kit_lanche_unificado.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = kit_lanche_unificado.rastro_lote_id
         LEFT JOIN kit_lanche_escolaquantidade
                   ON kit_lanche_escolaquantidade.solicitacao_unificada_id = kit_lanche_unificado.id
         LEFT JOIN terceirizada_terceirizada AS terceirizada
                   ON terceirizada.id = kit_lanche_unificado.rastro_terceirizada_id
         LEFT JOIN kit_lanche_solicitacaokitlanche AS kit_lanche_item
                   ON kit_lanche_item.id = kit_lanche_unificado.solicitacao_kit_lanche_id
GROUP BY kit_lanche_unificado.id,
         lote.nome,
         lote.uuid,
         dre.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         dre.nome,
         logs.criado_em,
         logs.status_evento,
         kit_lanche_item.data,
         kit_lanche_item.criado_em
