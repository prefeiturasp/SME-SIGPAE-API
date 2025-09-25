/// <reference types='cypress' />

describe('Validar rotas de Diretoria Regional Solicitações da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dre')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context(
		'Casos de teste para a rota api/diretoria-regional-solicitacoes/',
		() => {
			it('Validar GET com sucesso de Aguardando CODAE - DRE', () => {
				cy.dre_consultar_aguardando_codae().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Autorizadas Dietas Temporariamente - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_autorizadas_temporariamente_dieta(uuid).then(
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

			it('Validar GET com sucesso de Autorizados - DRE', () => {
				cy.dre_consultar_autorizados().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Autorizados Dietas - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_autorizados_dieta(uuid).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Cancelados - DRE', () => {
				cy.dre_consultar_cancelados().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Cancelados Dietas - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_cancelados_dieta(uuid).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Inativas Dietas - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_inativas_dieta(uuid).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Inativas Temporariamente Dietas - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_inativas_temporariamente_dieta(uuid).then(
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

			it('Validar GET com sucesso de Negados - DRE', () => {
				cy.dre_consultar_negados().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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
							value === 'CODAE_NEGOU_PEDIDO' ||
							value === 'DRE_NAO_VALIDOU_PEDIDO_ESCOLA'
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

			it('Validar GET com sucesso de Negados Dietas - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_negados_dieta(uuid).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Dietas Pendentes de Autorização - DRE', () => {
				var uuid = '3972e0e9-2d8e-472a-9dfa-30cd219a6d9a'
				cy.dre_consultar_pendentes_autorizacao_dieta(uuid).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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

			it('Validar GET com sucesso de Pendentes de Autorização - DRE', () => {
				cy.dre_consultar_pendentes_autorizacao().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('numero_alunos')
					expect(response.body.results[0]).property('data_log')
					expect(response.body.results[0]).to.have.property('id_externo')
					expect(response.body.results[0]).to.have.property(
						'escolas_quantidades',
					)
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('iniciais')
					expect(
						response.body.results[0].tipo_unidade_escolar,
					).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('uuid').that.exist
						.and.is.not.empty
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
					expect(response.body.results[0]).to.have.property(
						'escola_destino_uuid',
					)
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
						.to.eq('DRE_A_VALIDAR')
					expect(response.body.results[0]).to.have.property('conferido')
					expect(response.body.results[0]).to.have.property(
						'terceirizada_conferiu_gestao',
					)
					expect(response.body.results[0]).to.have.property('dre_nome')
					expect(response.body.results[0]).to.have.property('dre_nome')
				})
			})

			it('Validar GET com sucesso de Solicitações Detalhadas - DRE', () => {
				cy.dre_consultar_solicitacoes_detalhadas().then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('data')
					expect(response.body.data).to.be.an('array')
					expect(response.body).to.have.property('status')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 7 Dias e Tipo Visão DRE - DRE', () => {
				var filtro = 'daqui_a_7_dias'
				var visao = 'dre'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 7 Dias e Tipo Visão LOTE - DRE', () => {
				var filtro = 'daqui_a_7_dias'
				var visao = 'lote'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 7 Dias e Tipo Visão TIPO SOLICITAÇÃO - DRE', () => {
				var filtro = 'daqui_a_7_dias'
				var visao = 'tipo_solicitacao'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação sem Filtro e Tipo Visão DRE - DRE', () => {
				var filtro = 'sem_filtro'
				var visao = 'dre'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação sem Filtro e Tipo Visão LOTE - DRE', () => {
				var filtro = 'sem_filtro'
				var visao = 'lote'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação sem Filtro e Tipo Visão TIPO SOLICITAÇÃO - DRE', () => {
				var filtro = 'sem_filtro'
				var visao = 'tipo_solicitacao'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 30 Dias e Tipo Visão DRE - DRE', () => {
				var filtro = 'daqui_a_30_dias'
				var visao = 'dre'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 30 Dias e Tipo Visão LOTE - DRE', () => {
				var filtro = 'daqui_a_30_dias'
				var visao = 'lote'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})

			it('Validar GET com sucesso de Pendentes Validação com Filtro 30 Dias e Tipo Visão TIPO SOLICITAÇÃO - DRE', () => {
				var filtro = 'daqui_a_30_dias'
				var visao = 'tipo_solicitacao'
				cy.dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(
					filtro,
					visao,
				).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
				})
			})
		},
	)
})
