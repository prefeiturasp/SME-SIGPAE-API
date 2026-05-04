CREATE VIEW dietas_ativas_inativas_por_aluno AS
SELECT
	aluno_id,
	sum(case when ativo then 1 else 0 end) ativas,
	sum(case when ativo then 0 else 1 end) inativas
  FROM dieta_especial_solicitacaodietaespecial
  GROUP BY aluno_id;
