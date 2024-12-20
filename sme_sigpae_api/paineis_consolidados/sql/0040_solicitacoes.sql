DROP VIEW IF EXISTS solicitacoes_consolidadas;

create or replace view solicitacoes_consolidadas as
select dieta.id,
       dieta.uuid,
       dieta.criado_em::date                            as data_evento,
       null                                             as data_evento_fim,
       null::date                                       as data_evento_2,
       dieta.criado_em                                  as criado_em,
       lote.nome                                        AS lote_nome,
       dre.nome                                         AS dre_nome,
       dre.iniciais                                     as dre_iniciais,
       escola.nome                                      AS escola_nome,
       tipo_unidade.uuid                                as escola_tipo_unidade_uuid,
       tipo_gestao.uuid                                 as escola_tipo_gestao_uuid,
       aluno.nome                                       AS nome_aluno,
       aluno.codigo_eol                                 AS codigo_eol_aluno,
       terceirizada.nome_fantasia                       AS terceirizada_nome,
       lote.uuid                                        as lote_uuid,
       lote_escola_destino.uuid                         as lote_escola_destino_uuid,
       dre.uuid                                         as dre_uuid,
       dre_escola_destino.uuid                          as dre_escola_destino_uuid,
       escola.uuid                                      as escola_uuid,
       escola_destino.uuid                              as escola_destino_uuid,
       terceirizada.uuid                                as terceirizada_uuid,
       'DIETA_ESPECIAL'                                 AS tipo_doc,
       'Dieta Especial'                                 AS desc_doc,
       1                                                AS numero_alunos,
       dieta.status                                     as status_atual,
       logs.criado_em                                   AS data_log,
       logs.status_evento,
       null                                             AS motivo,
       aluno.nao_matriculado                            AS aluno_nao_matriculado,
       dieta.tipo_solicitacao                           AS tipo_solicitacao_dieta,
       dieta.dieta_alterada_id,
       dieta.ativo,
       (data_inicio <= (select cast(NOW() as date)) AND data_termino >= (select cast(NOW() as date))) AS em_vigencia,
       dieta.escola_destino_id,
       dieta.classificacao_id,
       tipo_unidade_escola_destino.uuid                 AS escola_destino_tipo_unidade_uuid,
       aluno.serie,
       dieta.conferido,
       null                                             AS terceirizada_conferiu_gestao
from dieta_especial_solicitacaodietaespecial as dieta
         LEFT JOIN dados_comuns_logsolicitacoesusuario AS logs ON logs.uuid_original = dieta.uuid
         LEFT JOIN escola_aluno AS aluno ON aluno.id = dieta.aluno_id
         LEFT JOIN escola_diretoriaregional AS dre ON dre.id = dieta.rastro_dre_id
         LEFT JOIN escola_lote AS lote ON lote.id = dieta.rastro_lote_id
         LEFT JOIN escola_escola AS escola ON escola.id = dieta.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         LEFT JOIN escola_tipogestao AS tipo_gestao ON tipo_gestao.id = escola.tipo_gestao_id
         LEFT JOIN escola_escola AS escola_destino ON dieta.escola_destino_id = escola_destino.id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade_escola_destino ON tipo_unidade_escola_destino.id = escola_destino.tipo_unidade_id
         LEFT JOIN escola_lote AS lote_escola_destino ON lote_escola_destino.id = escola_destino.lote_id
         LEFT JOIN escola_diretoriaregional AS dre_escola_destino ON dre_escola_destino.id = escola_destino.diretoria_regional_id
         LEFT JOIN terceirizada_terceirizada AS terceirizada ON terceirizada.id = dieta.rastro_terceirizada_id
union
select cardapio.id,
       cardapio.uuid,
       min(alt_cardapio_item.data)          as data_evento,
       null::date                           as data_evento_2,
       cardapio.data_final                  as data_evento_fim,
       cardapio.criado_em                   as criado_em,
       lote.nome                            as lote_nome,
       dre.nome                             as dre_nome,
       dre.iniciais                         as dre_iniciais,
       escola.nome                          as escola_nome,
       tipo_unidade.uuid                    as escola_tipo_unidade_uuid,
       null                                 as escola_tipo_gestao_uuid,
       ''                                   as nome_aluno,
       null                                 as codigo_eol_aluno,
       terceirizada.nome_fantasia           as terceirizada_nome,
       lote.uuid                            as lote_uuid,
       null                                 as lote_escola_destino_uuid,
       dre.uuid                             as dre_uuid,
       null                                 as dre_escola_destino_uuid,
       escola.uuid                          as escola_uuid,
       null                                 as escola_destino_uuid,
       terceirizada.uuid                    as terceirizada_uuid,
       'ALT_CARDAPIO'                       as tipo_doc,
       'Alteração do tipo de Alimentação'   as desc_doc,
       0                                    as numero_alunos,
       cardapio.status                      as status_atual,
       logs.criado_em                       as data_log,
       logs.status_evento,
       motivo.nome                          as motivo,
       null                                 as aluno_nao_matriculado,
       null                                 as tipo_solicitacao_dieta,
       null                                 as dieta_alterada_id,
       null                                 as ativo,
       null                                 as em_vigencia,
       null                                 as escola_destino_id,
       null                                 as classificacao_id,
       null                                 as escola_destino_tipo_unidade_uuid,
       null                                 as serie,
       null                                 as conferido,
       cardapio.terceirizada_conferiu_gestao
from cardapio_alteracaocardapio as cardapio
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = cardapio.uuid
         left join escola_diretoriaregional as dre on dre.id = cardapio.rastro_dre_id
         left join escola_lote as lote on lote.id = cardapio.rastro_lote_id
         left join escola_escola as escola on escola.id = cardapio.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada on terceirizada.id = cardapio.rastro_terceirizada_id
         left join cardapio_motivoalteracaocardapio as motivo on motivo.id = cardapio.motivo_id
         left join cardapio_dataintervaloalteracaocardapio as alt_cardapio_item
                   on alt_cardapio_item.alteracao_cardapio_id = cardapio.id
group by cardapio.id,
         alt_cardapio_item.data,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         terceirizada.nome_fantasia,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         logs.criado_em,
         logs.status_evento,
         motivo.nome

union
select inversao_cardapio.id,
       inversao_cardapio.uuid,
       case
           when inversao_cardapio.data_de_inversao <= inversao_cardapio.data_para_inversao then inversao_cardapio.data_de_inversao
           when inversao_cardapio.data_de_inversao > inversao_cardapio.data_para_inversao then inversao_cardapio.data_para_inversao
           when cardapio_de.data <= cardapio_para.data then cardapio_de.data
           else cardapio_para.data
           end                       as data_evento,
       null                          as data_evento_fim,
       case
           when inversao_cardapio.data_de_inversao_2 <= inversao_cardapio.data_para_inversao_2 then inversao_cardapio.data_de_inversao_2
           when inversao_cardapio.data_de_inversao_2 > inversao_cardapio.data_para_inversao_2 then inversao_cardapio.data_para_inversao_2
           when cardapio_de.data <= cardapio_para.data then cardapio_de.data
           else cardapio_para.data
           end                       as data_evento_2,
       inversao_cardapio.criado_em   as criado_em,
       lote.nome                     as lote_nome,
       dre.nome                      as dre_nome,
       dre.iniciais                  as dre_iniciais,
       escola.nome                   as escola_nome,
       tipo_unidade.uuid             as escola_tipo_unidade_uuid,
       null                          as escola_tipo_gestao_uuid,
       ''                            as nome_aluno,
       null                          as codigo_eol_aluno,
       terceirizada.nome_fantasia    as terceirizada_nome,
       lote.uuid                     as lote_uuid,
       null                          as lote_escola_destino_uuid,
       dre.uuid                      as dre_uuid,
       null                          as dre_escola_destino_uuid,
       escola.uuid                   as escola_uuid,
       null                          as escola_destino_uuid,
       terceirizada.uuid             as terceirizada_uuid,
       'INV_CARDAPIO'                as tipo_doc,
       'Inversão de dia de Cardápio' as desc_doc,
       0                             as numero_alunos,
       inversao_cardapio.status      as status_atual,
       logs.criado_em                as data_log,
       logs.status_evento,
       null                          as motivo,
       null                          as aluno_nao_matriculado,
       null                          AS tipo_solicitacao_dieta,
       null                          AS dieta_alterada_id,
       null                          AS ativo,
       null                          AS em_vigencia,
       null                          AS escola_destino_id,
       null                          AS classificacao_id,
       null                          AS escola_destino_tipo_unidade_uuid,
       null                          AS serie,
       null                          AS conferido,
       inversao_cardapio.terceirizada_conferiu_gestao
from cardapio_inversaocardapio as inversao_cardapio
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = inversao_cardapio.uuid
         left join escola_diretoriaregional as dre on dre.id = inversao_cardapio.rastro_dre_id
         left join escola_lote as lote on lote.id = inversao_cardapio.rastro_lote_id
         left join escola_escola as escola on escola.id = inversao_cardapio.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = inversao_cardapio.rastro_terceirizada_id
         left join cardapio_cardapio as cardapio_de on cardapio_de.id = inversao_cardapio.cardapio_de_id
         left join cardapio_cardapio as cardapio_para on cardapio_para.id = inversao_cardapio.cardapio_para_id
union
select inc_aliment_normal.id,
       inc_aliment_normal.uuid,
       min(inc_alimentacao_item.data)        as data_evento,
       null::date                            as data_evento_2,
       null                                  as data_evento_fim,
       inc_aliment_normal.criado_em          as criado_em,
       lote.nome                             as lote_nome,
       dre.nome                              as dre_nome,
       dre.iniciais                          as dre_iniciais,
       escola.nome                           as escola_nome,
       tipo_unidade.uuid                     as escola_tipo_unidade_uuid,
       null                                  as escola_tipo_gestao_uuid,
       ''                                    as nome_aluno,
       null                                  as codigo_eol_aluno,
       terceirizada.nome_fantasia            as terceirizada_nome,
       lote.uuid                             as lote_uuid,
       null                                  as lote_escola_destino_uuid,
       dre.uuid                              as dre_uuid,
       null                                  as dre_escola_destino_uuid,
       escola.uuid                           as escola_uuid,
       null                                  as escola_destino_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA'                        as tipo_doc,
       'Inclusão de Alimentação'             as desc_doc,
       sum(quantidade_periodo.numero_alunos) as numero_alunos,
       inc_aliment_normal.status             as status_atual,
       logs.criado_em                        as data_log,
       logs.status_evento,
       null                                  as motivo,
       null                                  as aluno_nao_matriculado,
       null                                  AS tipo_solicitacao_dieta,
       null                                  AS dieta_alterada_id,
       null                                  AS ativo,
       null                                  AS em_vigencia,
       null                                  AS escola_destino_id,
       null                                  AS classificacao_id,
       null                                  AS escola_destino_tipo_unidade_uuid,
       null                                  AS serie,
       null                                  AS conferido,
       inc_aliment_normal.terceirizada_conferiu_gestao
from inclusao_alimentacao_grupoinclusaoalimentacaonormal as inc_aliment_normal
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = inc_aliment_normal.uuid
         left join escola_diretoriaregional as dre on dre.id = inc_aliment_normal.rastro_dre_id
         left join escola_lote as lote on lote.id = inc_aliment_normal.rastro_lote_id
         left join escola_escola as escola on escola.id = inc_aliment_normal.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = inc_aliment_normal.rastro_terceirizada_id
         left join inclusao_alimentacao_quantidadeporperiodo as quantidade_periodo
                   on quantidade_periodo.grupo_inclusao_normal_id = inc_aliment_normal.id
         left join inclusao_alimentacao_inclusaoalimentacaonormal as inc_alimentacao_item
                   on inc_alimentacao_item.grupo_inclusao_id = inc_aliment_normal.id
group by inc_aliment_normal.id,
         inc_alimentacao_item.data,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
union
select inc_aliment_continua.id,
       inc_aliment_continua.uuid,
       inc_aliment_continua.data_inicial     as data_evento,
       null::date                            as data_evento_2,
       inc_aliment_continua.data_final       as data_evento_fim,
       inc_aliment_continua.criado_em        as criado_em,
       lote.nome                             as lote_nome,
       dre.nome                              as dre_nome,
       dre.iniciais                          as dre_iniciais,
       escola.nome                           as escola_nome,
       tipo_unidade.uuid                     as escola_tipo_unidade_uuid,
       null                                  as escola_tipo_gestao_uuid,
       ''                                    as nome_aluno,
       null                                  as codigo_eol_aluno,
       terceirizada.nome_fantasia            as terceirizada_nome,
       lote.uuid                             as lote_uuid,
       null                                  as lote_escola_destino_uuid,
       dre.uuid                              as dre_uuid,
       null                                  as dre_escola_destino_uuid,
       escola.uuid                           as escola_uuid,
       null                                  as escola_destino_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA_CONTINUA'               as tipo_doc,
       'Inclusão de Alimentação Contínua'    as desc_doc,
       sum(quantidade_periodo.numero_alunos) as numero_alunos,
       inc_aliment_continua.status           as status_atual,
       logs.criado_em                        as data_log,
       logs.status_evento,
       motivo.nome                           as motivo,
       null                                  as aluno_nao_matriculado,
       null                                  AS tipo_solicitacao_dieta,
       null                                  AS dieta_alterada_id,
       null                                  AS ativo,
       null                                  AS em_vigencia,
       null                                  AS escola_destino_id,
       null                                  AS classificacao_id,
       null                                  AS escola_destino_tipo_unidade_uuid,
       null                                  AS serie,
       null                                  AS conferido,
       inc_aliment_continua.terceirizada_conferiu_gestao
from inclusao_alimentacao_inclusaoalimentacaocontinua as inc_aliment_continua
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = inc_aliment_continua.uuid
         left join escola_diretoriaregional as dre on dre.id = inc_aliment_continua.rastro_dre_id
         left join escola_lote as lote on lote.id = inc_aliment_continua.rastro_lote_id
         left join escola_escola as escola on escola.id = inc_aliment_continua.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join inclusao_alimentacao_quantidadeporperiodo as quantidade_periodo
                   on quantidade_periodo.grupo_inclusao_normal_id = inc_aliment_continua.id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = inc_aliment_continua.rastro_terceirizada_id
         left join inclusao_alimentacao_motivoinclusaocontinua as motivo
                   on motivo.id = inc_aliment_continua.motivo_id

group by inc_aliment_continua.id,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento,
         motivo.nome
union
select kit_lanche_avulso.id,
       kit_lanche_avulso.uuid,
       kit_lanche_base.data                as data_evento,
       null::date                          as data_evento_2,
       null                                as data_evento_fim,
       kit_lanche_base.criado_em           as criado_em,
       lote.nome                           as lote_nome,
       dre.nome                            as dre_nome,
       dre.iniciais                        as dre_iniciais,
       escola.nome                         as escola_nome,
       tipo_unidade.uuid                   as escola_tipo_unidade_uuid,
       null                                as escola_tipo_gestao_uuid,
       ''                                  as nome_aluno,
       null                                as codigo_eol_aluno,
       terceirizada.nome_fantasia          as terceirizada_nome,
       lote.uuid                           as lote_uuid,
       null                                as lote_escola_destino_uuid,
       dre.uuid                            as dre_uuid,
       null                                as dre_escola_destino_uuid,
       escola.uuid                         as escola_uuid,
       null                                as escola_destino_uuid,
       terceirizada.uuid                   as terceirizada_uuid,
       'KIT_LANCHE_AVULSA'                 as tipo_doc,
       'Kit Lanche Passeio'                as desc_doc,
       kit_lanche_avulso.quantidade_alunos as numero_alunos,
       kit_lanche_avulso.status            as status_atual,
       logs.criado_em                      as data_log,
       logs.status_evento,
       null                                as motivo,
       null                                as aluno_nao_matriculado,
       null                                AS tipo_solicitacao_dieta,
       null                                AS dieta_alterada_id,
       null                                AS ativo,
       null                                AS em_vigencia,
       null                                AS escola_destino_id,
       null                                AS classificacao_id,
       null                                AS escola_destino_tipo_unidade_uuid,
       null                                AS serie,
       null                                AS conferido,
       kit_lanche_avulso.terceirizada_conferiu_gestao
from kit_lanche_solicitacaokitlancheavulsa as kit_lanche_avulso
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = kit_lanche_avulso.uuid
         left join escola_diretoriaregional as dre on dre.id = kit_lanche_avulso.rastro_dre_id
         left join escola_lote as lote on lote.id = kit_lanche_avulso.rastro_lote_id
         left join escola_escola as escola on escola.id = kit_lanche_avulso.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = kit_lanche_avulso.rastro_terceirizada_id
         left join kit_lanche_solicitacaokitlanche as kit_lanche_base
                   on kit_lanche_base.id = kit_lanche_avulso.solicitacao_kit_lanche_id
union
select grupo_suspensao.id,
       grupo_suspensao.uuid,
       min(susp_alimentacao_item.data) as data_evento,
       null::date                      as data_evento_2,
       null                            as data_evento_fim,
       grupo_suspensao.criado_em       as criado_em,
       lote.nome                       as lote_nome,
       dre.nome                        as dre_nome,
       dre.iniciais                    as dre_iniciais,
       escola.nome                     as escola_nome,
       tipo_unidade.uuid               as escola_tipo_unidade_uuid,
       null                            as escola_tipo_gestao_uuid,
       ''                              as nome_aluno,
       null                            as codigo_eol_aluno,
       terceirizada.nome_fantasia      as terceirizada_nome,
       lote.uuid                       as lote_uuid,
       null                            as lote_escola_destino_uuid,
       dre.uuid                        as dre_uuid,
       null                            as dre_escola_destino_uuid,
       escola.uuid                     as escola_uuid,
       null                            as escola_destino_uuid,
       terceirizada.uuid               as terceirizada_uuid,
       'SUSP_ALIMENTACAO'              as tipo_doc,
       'Suspensão de Alimentação'      as desc_doc,
       0                               as numero_alunos,
       grupo_suspensao.status          as status_atual,
       logs.criado_em                  as data_log,
       logs.status_evento,
       null                            as motivo,
       null                            as aluno_nao_matriculado,
       null                            AS tipo_solicitacao_dieta,
       null                            AS dieta_alterada_id,
       null                            AS ativo,
       null                            AS em_vigencia,
       null                            AS escola_destino_id,
       null                            AS classificacao_id,
       null                            AS escola_destino_tipo_unidade_uuid,
       null                            AS serie,
       null                            AS conferido,
       grupo_suspensao.terceirizada_conferiu_gestao
from cardapio_gruposuspensaoalimentacao as grupo_suspensao
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = grupo_suspensao.uuid
         left join escola_diretoriaregional as dre on dre.id = grupo_suspensao.rastro_dre_id
         left join escola_lote as lote on lote.id = grupo_suspensao.rastro_lote_id
         left join escola_escola as escola on escola.id = grupo_suspensao.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada on terceirizada.id = grupo_suspensao.rastro_terceirizada_id
         left join cardapio_suspensaoalimentacao as susp_alimentacao_item
                   on susp_alimentacao_item.grupo_suspensao_id = grupo_suspensao.id
group by grupo_suspensao.id,
         susp_alimentacao_item.data,
         lote.nome,
         escola.nome,
         tipo_unidade.uuid,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         dre.nome,
         dre.iniciais,
         logs.criado_em,
         logs.status_evento
union
select kit_lanche_unificado.id,
       kit_lanche_unificado.uuid,
       kit_lanche_item.data                               as data_evento,
       null::date                                         as data_evento_2,
       null                                               as data_evento_fim,
       kit_lanche_item.criado_em                          as criado_em,
       lote.nome                                          as lote_nome,
       dre.nome                                           as dre_nome,
       dre.iniciais                                       as dre_iniciais,
       escola.nome                                        as escola_nome,
       tipo_unidade.uuid                                  as escola_tipo_unidade_uuid,
       null                                               as escola_tipo_gestao_uuid,
       ''                                                 as nome_aluno,
       null                                               as codigo_eol_aluno,
       terceirizada.nome_fantasia                         as terceirizada_nome,
       lote.uuid                                          as lote_uuid,
       null                                               as lote_escola_destino_uuid,
       dre.uuid                                           as dre_uuid,
       null                                               as dre_escola_destino_uuid,
       escola.uuid                                        as escola_uuid,
       null                                               as escola_destino_uuid,
       terceirizada.uuid                                  as terceirizada_uuid,
       'KIT_LANCHE_UNIFICADA'                             as tipo_doc,
       'Kit Lanche Unificado'                             as desc_doc,
       sum(escola_quantidade.quantidade_alunos)           as numero_alunos,
       kit_lanche_unificado.status                        as status_atual,
       logs.criado_em                                     as data_log,
       logs.status_evento,
       null                                               as motivo,
       null                                               as aluno_nao_matriculado,
       null                                               AS tipo_solicitacao_dieta,
       null                                               AS dieta_alterada_id,
       null                                               AS ativo,
       null                                               AS em_vigencia,
       null                                               AS escola_destino_id,
       null                                               AS classificacao_id,
       null                                               AS escola_destino_tipo_unidade_uuid,
       null                                               AS serie,
       null                                               AS conferido,
       kit_lanche_unificado.terceirizada_conferiu_gestao
from kit_lanche_solicitacaokitlancheunificada as kit_lanche_unificado
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = kit_lanche_unificado.uuid
         left join escola_diretoriaregional as dre on dre.id = kit_lanche_unificado.rastro_dre_id
         left join escola_lote as lote on lote.id = kit_lanche_unificado.rastro_lote_id
         left join kit_lanche_escolaquantidade as escola_quantidade
                   on escola_quantidade.solicitacao_unificada_id = kit_lanche_unificado.id
         left join escola_escola as escola
                   on escola.id = escola_quantidade.escola_id
         left join escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join escola_tipogestao AS tipo_gestao ON tipo_gestao.id = escola.tipo_gestao_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = kit_lanche_unificado.rastro_terceirizada_id
         left join kit_lanche_solicitacaokitlanche as kit_lanche_item
                   on kit_lanche_item.id = kit_lanche_unificado.solicitacao_kit_lanche_id
group by kit_lanche_unificado.id,
         escola_quantidade.escola_id,
         escola.nome,
         escola.uuid,
         tipo_unidade.uuid,
         lote.nome,
         lote.uuid,
         dre.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         dre.nome,
         dre.iniciais,
         logs.criado_em,
         logs.status_evento,
         kit_lanche_item.data,
         kit_lanche_item.criado_em
union
select inc_alimentacao_cei.id,
       inc_alimentacao_cei.uuid,
       min(inc_alimentacao_item.data)        as data_evento,
       null::date                            as data_evento_2,
       null                                  as data_evento_fim,
       inc_alimentacao_cei.criado_em         as criado_em,
       lote.nome                             as lote_nome,
       dre.nome                              as dre_nome,
       dre.iniciais                          as dre_iniciais,
       escola.nome                           as escola_nome,
       tipo_unidade.uuid                     as escola_tipo_unidade_uuid,
       null                                  as escola_tipo_gestao_uuid,
       ''                                    as nome_aluno,
       null                                  as codigo_eol_aluno,
       terceirizada.nome_fantasia            as terceirizada_nome,
       lote.uuid                             as lote_uuid,
       null                                  as lote_escola_destino_uuid,
       dre.uuid                              as dre_uuid,
       null                                  as dre_escola_destino_uuid,
       escola.uuid                           as escola_uuid,
       null                                  as escola_destino_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA_CEI'                    as tipo_doc,
       'Inclusão de Alimentacao de CEI'      as desc_doc,
       1                                     as numero_alunos,
       inc_alimentacao_cei.status            as status_atual,
       logs.criado_em                        as data_log,
       logs.status_evento,
       null                                  as motivo,
       null                                  as aluno_nao_matriculado,
       null                                  AS tipo_solicitacao_dieta,
       null                                  AS dieta_alterada_id,
       null                                  AS ativo,
       null                                  AS em_vigencia,
       null                                  AS escola_destino_id,
       null                                  AS classificacao_id,
       null                                  AS escola_destino_tipo_unidade_uuid,
       null                                  AS serie,
       null                                  AS conferido,
       inc_alimentacao_cei.terceirizada_conferiu_gestao
from inclusao_alimentacao_inclusaoalimentacaodacei as inc_alimentacao_cei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = inc_alimentacao_cei.uuid
         left join escola_diretoriaregional as dre on dre.id = inc_alimentacao_cei.rastro_dre_id
         left join escola_lote as lote on lote.id = inc_alimentacao_cei.rastro_lote_id
         left join escola_escola as escola on escola.id = inc_alimentacao_cei.rastro_escola_id
         left join escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join escola_tipogestao AS tipo_gestao ON tipo_gestao.id = escola.tipo_gestao_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = inc_alimentacao_cei.rastro_terceirizada_id
         left join inclusao_alimentacao_diasmotivosinclusaodealimentacaocei as inc_alimentacao_item
                   on inc_alimentacao_item.inclusao_cei_id = inc_alimentacao_cei.id
group by inc_alimentacao_cei.id,
         inc_alimentacao_item.data,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
union
select alteracao_cardapio_cei.id,
       alteracao_cardapio_cei.uuid,
       min(alteracao_cardapio_cei.data)             as data_evento,
       null::date                                   as data_evento_2,
       null                                         as data_evento_fim,
       alteracao_cardapio_cei.criado_em             as criado_em,
       lote.nome                                    as lote_nome,
       dre.nome                                     as dre_nome,
       dre.iniciais                                 as dre_iniciais,
       escola.nome                                  as escola_nome,
       tipo_unidade.uuid                            as escola_tipo_unidade_uuid,
       null                                         as escola_tipo_gestao_uuid,
       ''                                           as nome_aluno,
       null                                         as codigo_eol_aluno,
       terceirizada.nome_fantasia                   as terceirizada_nome,
       lote.uuid                                    as lote_uuid,
       null                                         as lote_escola_destino_uuid,
       dre.uuid                                     as dre_uuid,
       null                                         as dre_escola_destino_uuid,
       escola.uuid                                  as escola_uuid,
       null                                         as escola_destino_uuid,
       terceirizada.uuid                            as terceirizada_uuid,
       'ALT_CARDAPIO_CEI'                           as tipo_doc,
       'Alteração do Tipo de Alimentação CEI'       as desc_doc,
       1                                            as numero_alunos,
       alteracao_cardapio_cei.status                as status_atual,
       logs.criado_em                               as data_log,
       logs.status_evento,
       motivo.nome                                  as motivo,
       null                                         as aluno_nao_matriculado,
       null                                         AS tipo_solicitacao_dieta,
       null                                         AS dieta_alterada_id,
       null                                         AS ativo,
       null                                         AS em_vigencia,
       null                                         AS escola_destino_id,
       null                                         AS classificacao_id,
       null                                         AS escola_destino_tipo_unidade_uuid,
       null                                         AS serie,
       null                                         AS conferido,
       alteracao_cardapio_cei.terceirizada_conferiu_gestao
from cardapio_alteracaocardapiocei as alteracao_cardapio_cei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = alteracao_cardapio_cei.uuid
         left join escola_diretoriaregional as dre on dre.id = alteracao_cardapio_cei.rastro_dre_id
         left join escola_lote as lote on lote.id = alteracao_cardapio_cei.rastro_lote_id
         left join escola_escola as escola on escola.id = alteracao_cardapio_cei.rastro_escola_id
         left join cardapio_motivoalteracaocardapio as motivo on motivo.id = alteracao_cardapio_cei.motivo_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = alteracao_cardapio_cei.rastro_terceirizada_id
group by alteracao_cardapio_cei.id,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento,
         motivo.nome
union
select kit_lanche_cei_avulso.id,
       kit_lanche_cei_avulso.uuid,
       kit_lanche_item.data                as data_evento,
       null::date                          as data_evento_2,
       null                                as data_evento_fim,
       kit_lanche_item.criado_em           as criado_em,
       lote.nome                           as lote_nome,
       dre.nome                            as dre_nome,
       dre.iniciais                        as dre_iniciais,
       escola.nome                         as escola_nome,
       tipo_unidade.uuid                   as escola_tipo_unidade_uuid,
       null                                as escola_tipo_gestao_uuid,
       ''                                  as nome_aluno,
       null                                as codigo_eol_aluno,
       terceirizada.nome_fantasia          as terceirizada_nome,
       lote.uuid                           as lote_uuid,
       null                                as lote_escola_destino_uuid,
       dre.uuid                            as dre_uuid,
       null                                as dre_escola_destino_uuid,
       escola.uuid                         as escola_uuid,
       null                                as escola_destino_uuid,
       terceirizada.uuid                   as terceirizada_uuid,
       'KIT_LANCHE_AVULSA_CEI'             as tipo_doc,
       'Kit Lanche Passeio de CEI'         as desc_doc,
       0                                   as numero_alunos,
       kit_lanche_cei_avulso.status        as status_atual,
       logs.criado_em                      as data_log,
       logs.status_evento,
       null                                as motivo,
       null                                as aluno_nao_matriculado,
       null                                AS tipo_solicitacao_dieta,
       null                                AS dieta_alterada_id,
       null                                AS ativo,
       null                                AS em_vigencia,
       null                                AS escola_destino_id,
       null                                AS classificacao_id,
       null                                AS escola_destino_tipo_unidade_uuid,
       null                                AS serie,
       null                                AS conferido,
       kit_lanche_cei_avulso.terceirizada_conferiu_gestao
from kit_lanche_solicitacaokitlancheceiavulsa as kit_lanche_cei_avulso
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = kit_lanche_cei_avulso.uuid
         left join escola_diretoriaregional as dre on dre.id = kit_lanche_cei_avulso.rastro_dre_id
         left join escola_lote as lote on lote.id = kit_lanche_cei_avulso.rastro_lote_id
         left join escola_escola as escola on escola.id = kit_lanche_cei_avulso.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = kit_lanche_cei_avulso.rastro_terceirizada_id
         left join kit_lanche_solicitacaokitlanche as kit_lanche_base
                   on kit_lanche_base.id = kit_lanche_cei_avulso.solicitacao_kit_lanche_id
         left join kit_lanche_solicitacaokitlanche as kit_lanche_item
                   on kit_lanche_item.id = kit_lanche_cei_avulso.solicitacao_kit_lanche_id
union
select grupo_suspensao_cei.id,
       grupo_suspensao_cei.uuid,
       min(grupo_suspensao_cei.data)          as data_evento,
       null::date                             as data_evento_2,
       null                                   as data_evento_fim,
       grupo_suspensao_cei.criado_em          as criado_em,
       lote.nome                              as lote_nome,
       dre.nome                               as dre_nome,
       dre.iniciais                           as dre_iniciais,
       escola.nome                            as escola_nome,
       tipo_unidade.uuid                      as escola_tipo_unidade_uuid,
       null                                   as escola_tipo_gestao_uuid,
       ''                                     as nome_aluno,
       null                                   as codigo_eol_aluno,
       terceirizada.nome_fantasia             as terceirizada_nome,
       lote.uuid                              as lote_uuid,
       null                                   as lote_escola_destino_uuid,
       dre.uuid                               as dre_uuid,
       null                                   as dre_escola_destino_uuid,
       escola.uuid                            as escola_uuid,
       null                                   as escola_destino_uuid,
       terceirizada.uuid                      as terceirizada_uuid,
       'SUSP_ALIMENTACAO_CEI'                 as tipo_doc,
       'Suspensão de Alimentação de CEI'      as desc_doc,
       0                                      as numero_alunos,
       grupo_suspensao_cei.status             as status_atual,
       logs.criado_em                         as data_log,
       logs.status_evento,
       null                                   as motivo,
       null                                   as aluno_nao_matriculado,
       null                                   AS tipo_solicitacao_dieta,
       null                                   AS dieta_alterada_id,
       null                                   AS ativo,
       null                                   AS em_vigencia,
       null                                   AS escola_destino_id,
       null                                   AS classificacao_id,
       null                                   AS escola_destino_tipo_unidade_uuid,
       null                                   AS serie,
       null                                   AS conferido,
       grupo_suspensao_cei.terceirizada_conferiu_gestao
from cardapio_suspensaoalimentacaodacei as grupo_suspensao_cei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = grupo_suspensao_cei.uuid
         left join escola_diretoriaregional as dre on dre.id = grupo_suspensao_cei.rastro_dre_id
         left join escola_lote as lote on lote.id = grupo_suspensao_cei.rastro_lote_id
         left join escola_escola as escola on escola.id = grupo_suspensao_cei.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada on terceirizada.id = grupo_suspensao_cei.rastro_terceirizada_id
group by grupo_suspensao_cei.id,
         lote.nome,
         escola.nome,
         tipo_unidade.uuid,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         dre.nome,
         dre.iniciais,
         logs.criado_em,
         logs.status_evento
union
select kit_lanche_cemei.id,
       kit_lanche_cemei.uuid,
       min(kit_lanche_cemei.data)            as data_evento,
       null::date                            as data_evento_2,
       null                                  as data_evento_fim,
       kit_lanche_cemei.criado_em            as criado_em,
       lote.nome                             as lote_nome,
       dre.nome                              as dre_nome,
       dre.iniciais                          as dre_iniciais,
       escola.nome                           as escola_nome,
       tipo_unidade.uuid                     as escola_tipo_unidade_uuid,
       null                                  as escola_tipo_gestao_uuid,
       ''                                    as nome_aluno,
       null                                  as codigo_eol_aluno,
       terceirizada.nome_fantasia            as terceirizada_nome,
       lote.uuid                             as lote_uuid,
       null                                  as lote_escola_destino_uuid,
       dre.uuid                              as dre_uuid,
       null                                  as dre_escola_destino_uuid,
       escola.uuid                           as escola_uuid,
       null                                  as escola_destino_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'KIT_LANCHE_CEMEI'                    as tipo_doc,
       'Kit Lanche Passeio de CEMEI'         as desc_doc,
       1                                     as numero_alunos,
       kit_lanche_cemei.status               as status_atual,
       logs.criado_em                        as data_log,
       logs.status_evento,
       null                                  as motivo,
       null                                  as aluno_nao_matriculado,
       null                                  AS tipo_solicitacao_dieta,
       null                                  AS dieta_alterada_id,
       null                                  AS ativo,
       null                                  AS em_vigencia,
       null                                  AS escola_destino_id,
       null                                  AS classificacao_id,
       null                                  AS escola_destino_tipo_unidade_uuid,
       null                                  AS serie,
       null                                  AS conferido,
       kit_lanche_cemei.terceirizada_conferiu_gestao
from kit_lanche_solicitacaokitlanchecemei as kit_lanche_cemei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = kit_lanche_cemei.uuid
         left join escola_diretoriaregional as dre on dre.id = kit_lanche_cemei.rastro_dre_id
         left join escola_lote as lote on lote.id = kit_lanche_cemei.rastro_lote_id
         left join escola_escola as escola on escola.id = kit_lanche_cemei.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = kit_lanche_cemei.rastro_terceirizada_id
group by kit_lanche_cemei.id,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
union
select inc_aliment_cemei.id,
       inc_aliment_cemei.uuid,
       min(inc_alimentacao_item.data)        as data_evento,
       null::date                            as data_evento_2,
       null                                  as data_evento_fim,
       inc_aliment_cemei.criado_em           as criado_em,
       lote.nome                             as lote_nome,
       dre.nome                              as dre_nome,
       dre.iniciais                          as dre_iniciais,
       escola.nome                           as escola_nome,
       tipo_unidade.uuid                     as escola_tipo_unidade_uuid,
       null                                  as escola_tipo_gestao_uuid,
       ''                                    as nome_aluno,
       null                                  as codigo_eol_aluno,
       terceirizada.nome_fantasia            as terceirizada_nome,
       lote.uuid                             as lote_uuid,
       null                                  as lote_escola_destino_uuid,
       dre.uuid                              as dre_uuid,
       null                                  as dre_escola_destino_uuid,
       escola.uuid                           as escola_uuid,
       null                                  as escola_destino_uuid,
       terceirizada.uuid                     as terceirizada_uuid,
       'INC_ALIMENTA_CEMEI'                  as tipo_doc,
       'Inclusão de Alimentação CEMEI'       as desc_doc,
       1                                     as numero_alunos,
       inc_aliment_cemei.status              as status_atual,
       logs.criado_em                        as data_log,
       logs.status_evento,
       null                                  as motivo,
       null                                  as aluno_nao_matriculado,
       null                                  AS tipo_solicitacao_dieta,
       null                                  AS dieta_alterada_id,
       null                                  AS ativo,
       null                                  AS em_vigencia,
       null                                  AS escola_destino_id,
       null                                  AS classificacao_id,
       null                                  AS escola_destino_tipo_unidade_uuid,
       null                                  AS serie,
       null                                  AS conferido,
       inc_aliment_cemei.terceirizada_conferiu_gestao
from inclusao_alimentacao_inclusaodealimentacaocemei as inc_aliment_cemei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = inc_aliment_cemei.uuid
         left join escola_diretoriaregional as dre on dre.id = inc_aliment_cemei.rastro_dre_id
         left join escola_lote as lote on lote.id = inc_aliment_cemei.rastro_lote_id
         left join escola_escola as escola on escola.id = inc_aliment_cemei.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada
                   on terceirizada.id = inc_aliment_cemei.rastro_terceirizada_id
         left join inclusao_alimentacao_diasmotivosinclusaodealimentacaocemei as inc_alimentacao_item
                   on inc_alimentacao_item.inclusao_alimentacao_cemei_id = inc_aliment_cemei.id
group by inc_aliment_cemei.id,
         inc_alimentacao_item.data,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         logs.criado_em,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         terceirizada.nome_fantasia,
         logs.status_evento
union
select cardapio_cemei.id,
       cardapio_cemei.uuid,
       min(alt_cardapio_item.data)                                                as data_evento,
        null::date                                                                as data_evento_2,
       cardapio_cemei.data_final                                                  as data_evento_fim,
       cardapio_cemei.criado_em                                                   as criado_em,
       lote.nome                                                                  as lote_nome,
       dre.nome                                                                   as dre_nome,
       dre.iniciais                                                               as dre_iniciais,
       escola.nome                                                                as escola_nome,
       tipo_unidade.uuid                                                          as escola_tipo_unidade_uuid,
       null                                                                       as escola_tipo_gestao_uuid,
       ''                                                                         as nome_aluno,
       null                                                                       as codigo_eol_aluno,
       terceirizada.nome_fantasia                                                 as terceirizada_nome,
       lote.uuid                                                                  as lote_uuid,
       null                                                                       as lote_escola_destino_uuid,
       dre.uuid                                                                   as dre_uuid,
       null                                                                       as dre_escola_destino_uuid,
       escola.uuid                                                                as escola_uuid,
       null                                                                       as escola_destino_uuid,
       terceirizada.uuid                                                          as terceirizada_uuid,
       'ALT_CARDAPIO_CEMEI'                                                       as tipo_doc,
       'Alteração do tipo de Alimentação CEMEI'                                   as desc_doc,
       0                                                                          as numero_alunos,
       cardapio_cemei.status                                                      as status_atual,
       logs.criado_em                                                             as data_log,
       logs.status_evento,
       motivo.nome                                                                as motivo,
       null                                                                       as aluno_nao_matriculado,
       null                                                                       as tipo_solicitacao_dieta,
       null                                                                       as dieta_alterada_id,
       null                                                                       as ativo,
       null                                                                       as em_vigencia,
       null                                                                       as escola_destino_id,
       null                                                                       as classificacao_id,
       null                                                                       as escola_destino_tipo_unidade_uuid,
       null                                                                       as serie,
       null                                                                       as conferido,
       cardapio_cemei.terceirizada_conferiu_gestao
from cardapio_alteracaocardapiocemei as cardapio_cemei
         left join dados_comuns_logsolicitacoesusuario as logs on logs.uuid_original = cardapio_cemei.uuid
         left join escola_diretoriaregional as dre on dre.id = cardapio_cemei.rastro_dre_id
         left join escola_lote as lote on lote.id = cardapio_cemei.rastro_lote_id
         left join escola_escola as escola on escola.id = cardapio_cemei.rastro_escola_id
         LEFT JOIN escola_tipounidadeescolar AS tipo_unidade ON tipo_unidade.id = escola.tipo_unidade_id
         left join terceirizada_terceirizada as terceirizada on terceirizada.id = cardapio_cemei.rastro_terceirizada_id
         left join cardapio_motivoalteracaocardapio as motivo on motivo.id = cardapio_cemei.motivo_id
         left join cardapio_dataintervaloalteracaocardapiocemei as alt_cardapio_item
                   on alt_cardapio_item.alteracao_cardapio_cemei_id = cardapio_cemei.id
group by cardapio_cemei.id,
         alt_cardapio_item.data,
         lote.nome,
         dre.nome,
         dre.iniciais,
         escola.nome,
         tipo_unidade.uuid,
         terceirizada.nome_fantasia,
         lote.uuid,
         dre.uuid,
         escola.uuid,
         terceirizada.uuid,
         logs.criado_em,
         logs.status_evento,
         motivo.nome
