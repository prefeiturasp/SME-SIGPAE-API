/// <reference types='cypress' />

describe('Validar rotas de Escola Solicitações da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_diretor_ue')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/escola-solicitacoes/', () => {
		it('Validar GET com sucesso de Autorizadas Dietas Temporariamente - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_autorizadas_temporariamente_dieta(uuid).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				},
			)
		})

		it('Validar GET com sucesso de Autorizados - ESCOLA', () => {
			cy.ue_consultar_autorizados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return value === 'INFORMADO' || value === 'CODAE_AUTORIZADO'
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Autorizados Dietas - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_autorizados_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return value === 'INFORMADO' || value === 'CODAE_AUTORIZADO'
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Cancelados - ESCOLA', () => {
			cy.ue_consultar_cancelados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado)
					.to.have.property('status_atual')
					.to.eq('ESCOLA_CANCELOU')
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Cancelados Dietas - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_cancelados_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return (
						value === 'CANCELADO_ALUNO_NAO_PERTENCE_REDE' ||
						value === 'CANCELADO_ALUNO_MUDOU_ESCOLA' ||
						value === 'ESCOLA_CANCELOU' ||
						value === 'CANCELADO_ENCERRAMENTO_MATRICULA' ||
						value === 'TERMINADA_AUTOMATICAMENTE_SISTEMA'
					)
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Inativas Dietas - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_inativas_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado).to.have.property('status_atual').that
					.exist
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Inativas Temporariamente Dietas - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_inativas_temporariamente_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
			})
		})

		it('Validar GET com sucesso de Negados - ESCOLA', () => {
			cy.ue_consultar_negados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return (
						value === 'CODAE_NEGOU_PEDIDO' ||
						value === 'DRE_NAO_VALIDOU_PEDIDO_ESCOLA'
					)
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Negados Dietas - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_negados_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return (
						value === 'CODAE_NEGOU_PEDIDO' ||
						value === 'CODAE_NEGOU_CANCELAMENTO' ||
						value === 'CODAE_NEGOU_INATIVACAO'
					)
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Dietas Pendentes de Autorização - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_pendentes_autorizacao_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado)
					.to.have.property('status_atual')
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Pendentes de Autorização - ESCOLA', () => {
			cy.ue_consultar_pendentes_autorizacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).property('numero_alunos')
				expect(primeiroResultado).property('data_log')
				expect(primeiroResultado).to.have.property('id_externo')
				expect(primeiroResultado).to.have.property('escolas_quantidades')
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'iniciais',
				)
				expect(primeiroResultado.tipo_unidade_escolar).to.have.property(
					'uuid',
				)
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('id')
					.that.exist.and.is.greaterThan(0)
				expect(primeiroResultado).to.have.property('descricao').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'descricao_dieta_especial',
				).that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('prioridade').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
					.that.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property('data_evento')
				expect(primeiroResultado).to.have.property('data_evento_2')
				expect(primeiroResultado).to.have.property('data_evento_fim')
				expect(primeiroResultado).to.have.property('lote_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_iniciais')
				expect(primeiroResultado).to.have.property('escola_nome')
				expect(primeiroResultado).to.have.property(
					'tipo_solicitacao_dieta',
				)
				expect(primeiroResultado).to.have.property('terceirizada_nome')
				expect(primeiroResultado).to.have.property('nome_aluno')
				expect(primeiroResultado).to.have.property('serie')
				expect(primeiroResultado).to.have.property('codigo_eol_aluno')
				expect(primeiroResultado).to.have.property(
					'aluno_nao_matriculado',
				)
				expect(primeiroResultado).to.have.property('dieta_alterada_id')
				expect(primeiroResultado).to.have.property('classificacao_id')
				expect(primeiroResultado).to.have.property('ativo')
				expect(primeiroResultado).to.have.property('em_vigencia')
				expect(primeiroResultado).to.have.property('lote_uuid')
				expect(primeiroResultado).to.have.property('escola_uuid')
				expect(primeiroResultado).to.have.property(
					'escola_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'escola_tipo_gestao_uuid',
				)
				expect(primeiroResultado).to.have.property('escola_destino_uuid')
				expect(primeiroResultado).to.have.property('escola_destino_id')
				expect(primeiroResultado).to.have.property(
					'escola_destino_tipo_unidade_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'lote_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property(
					'dre_escola_destino_uuid',
				)
				expect(primeiroResultado).to.have.property('terceirizada_uuid')
				expect(primeiroResultado).to.have.property('tipo_doc')
				expect(primeiroResultado).to.have.property('desc_doc')
				expect(primeiroResultado).to.have.property('status_evento')
				expect(primeiroResultado).to.have.property('motivo')
				expect(primeiroResultado.status_atual).to.satisfy((value) => {
					return (
						value === 'DRE_A_VALIDAR' ||
						value === 'DRE_VALIDADO' ||
						value === 'CODAE_QUESTIONADO' ||
						value === 'CODAE_A_AUTORIZAR'
					)
				})
				expect(primeiroResultado).to.have.property('conferido')
				expect(primeiroResultado).to.have.property(
					'terceirizada_conferiu_gestao',
				)
				expect(primeiroResultado).to.have.property('dre_nome')
				expect(primeiroResultado).to.have.property('dre_nome')
			})
		})

		it('Validar GET com sucesso de Solicitações Detalhadas - ESCOLA', () => {
			cy.ue_consultar_solicitacoes_detalhadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('data')
				expect(response.body.data).to.be.an('array')
				expect(response.body).to.have.property('status')
			})
		})

		it('Validar GET com sucesso de Aguardando Vigência Dieta - ESCOLA', () => {
			var uuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'
			cy.ue_consultar_aguardando_vigencia_dieta(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
			})
		})

		it('Validar GET com sucesso de Kit Lanches Autorizadas - ESCOLA', () => {
			cy.ue_consultar_kit_lanches_autorizadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
			})
		})

		it('Validar GET com sucesso de Suspensões Autorizadas - ESCOLA', () => {
			cy.ue_consultar_suspensoes_autorizadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
			})
		})
	})
})
