/// <reference types='cypress' />

describe('Validar rotas de Codae solicitações da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/codae-solicitacoes/', () => {
		it('Validar GET com sucesso de Dietas Pendentes de Autorização', () => {
			cy.consultar_pendentes_autorizacao_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('CODAE_A_AUTORIZAR')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Autorizadas', () => {
			cy.consultar_autorizados_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('CODAE_AUTORIZADO')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Inativas', () => {
			cy.consultar_inativas_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0]).to.have.property('status_atual').that
					.exist
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Negadas', () => {
			cy.consultar_negados_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('CODAE_NEGOU_PEDIDO')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Canceladas', () => {
			cy.consultar_cancelados_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0].status_atual).to.satisfy((value) => {
					return (
						value === 'CANCELADO_ALUNO_NAO_PERTENCE_REDE' ||
						value === 'CANCELADO_ALUNO_MUDOU_ESCOLA' ||
						value === 'ESCOLA_CANCELOU' ||
						value === 'TERMINADA_AUTOMATICAMENTE_SISTEMA'
					)
				})
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Autorizadas Temporariamente', () => {
			cy.consultar_autorizadas_temporariamente_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})

		it('Validar GET com sucesso de Autorizados', () => {
			cy.consultar_autorizados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0].status_atual).to.satisfy((value) => {
					return value === 'INFORMADO' || value === 'CODAE_AUTORIZADO'
				})
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Cancelados', () => {
			cy.consultar_cancelados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('ESCOLA_CANCELOU')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Inativas Temporariamente', () => {
			cy.consultar_inativas_temporariamente_dieta().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})

		it('Validar GET com sucesso de Negados', () => {
			cy.consultar_negados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('CODAE_NEGOU_PEDIDO')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Pendentes de Autorização', () => {
			cy.consultar_pendentes_autorizacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0].status_atual).to.satisfy((value) => {
					return (
						value === 'TERCEIRIZADA_RESPONDEU_QUESTIONAMENTO' ||
						value === 'DRE_VALIDADO'
					)
				})
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Questionamentos', () => {
			cy.consultar_questionamentos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('numero_alunos')
				expect(response.body.results[0]).property('data_log')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0]).to.have.property('escolas_quantidades')
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(response.body.results[0].tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(response.body.results[0])
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(response.body.results[0]).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property('data_evento')
				expect(response.body.results[0]).to.have.property('data_evento_2')
				expect(response.body.results[0]).to.have.property('data_evento_fim')
				expect(response.body.results[0]).to.have.property('lote_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_iniciais')
				expect(response.body.results[0]).to.have.property('escola_nome')
				expect(response.body.results[0]).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_nome')
				expect(response.body.results[0]).to.have.property('nome_aluno')
				expect(response.body.results[0]).to.have.property('serie')
				expect(response.body.results[0]).to.have.property('codigo_eol_aluno')
				expect(response.body.results[0]).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(response.body.results[0]).to.have.property('dieta_alterada_id')
				expect(response.body.results[0]).to.have.property('classificacao_id')
				expect(response.body.results[0]).to.have.property('ativo')
				expect(response.body.results[0]).to.have.property('em_vigencia')
				expect(response.body.results[0]).to.have.property('lote_uuid')
				expect(response.body.results[0]).to.have.property('escola_uuid')
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(response.body.results[0]).to.have.property('escola_destino_uuid')
				expect(response.body.results[0]).to.have.property('escola_destino_id')
				expect(response.body.results[0]).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(response.body.results[0]).to.have.property('terceirizada_uuid')
				expect(response.body.results[0]).to.have.property('tipo_doc')
				expect(response.body.results[0]).to.have.property('desc_doc')
				expect(response.body.results[0]).to.have.property('status_evento')
				expect(response.body.results[0]).to.have.property('motivo')
				expect(response.body.results[0])
					.to.have.property('status_atual')
					.to.eq('CODAE_QUESTIONADO')
				expect(response.body.results[0]).to.have.property('conferido')
				expect(response.body.results[0]).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(response.body.results[0]).to.have.property('dre_nome')
				expect(response.body.results[0]).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Solicitações Detalhadas', () => {
			cy.consultar_solicitacoes_detalhadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('data')
				expect(response.body.data).to.be.an('array')
				expect(response.body).to.have.property('status')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 7 Dias', () => {
			var filtro = 'daqui_a_7_dias'
			cy.consultar_pendentes_autorizacao_filtro_aplicado(filtro).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de Pendentes Autorização sem Filtro', () => {
			var filtro = 'sem_filtro'
			cy.consultar_pendentes_autorizacao_filtro_aplicado(filtro).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 30 Dias', () => {
			var filtro = 'daqui_a_30_dias'
			cy.consultar_pendentes_autorizacao_filtro_aplicado(filtro).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET de Pendentes Autorização com Filtro Inválido', () => {
			var filtro = 'outro_filtro'
			cy.consultar_pendentes_autorizacao_filtro_aplicado(filtro).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 7 Dias e Tipo Visão DRE', () => {
			var filtro = 'daqui_a_7_dias'
			var visao = 'dre'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 7 Dias e Tipo Visão LOTE', () => {
			var filtro = 'daqui_a_7_dias'
			var visao = 'lote'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 7 Dias e Tipo Visão TIPO SOLICITAÇÃO', () => {
			var filtro = 'daqui_a_7_dias'
			var visao = 'tipo_solicitacao'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização sem Filtro e Tipo Visão DRE', () => {
			var filtro = 'sem_filtro'
			var visao = 'dre'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização sem Filtro e Tipo Visão LOTE', () => {
			var filtro = 'sem_filtro'
			var visao = 'lote'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização sem Filtro e Tipo Visão TIPO SOLICITAÇÃO', () => {
			var filtro = 'sem_filtro'
			var visao = 'tipo_solicitacao'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 30 Dias e Tipo Visão DRE', () => {
			var filtro = 'daqui_a_30_dias'
			var visao = 'dre'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 30 Dias e Tipo Visão LOTE', () => {
			var filtro = 'daqui_a_30_dias'
			var visao = 'lote'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})

		it('Validar GET com sucesso de Pendentes Autorização com Filtro 30 Dias e Tipo Visão TIPO SOLICITAÇÃO', () => {
			var filtro = 'daqui_a_30_dias'
			var visao = 'tipo_solicitacao'
			cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
				filtro,
				visao,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
			})
		})
	})
})
