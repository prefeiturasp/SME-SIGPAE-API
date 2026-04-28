/// <reference types='cypress' />

describe('Validar rotas de alunos da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_diretor_ue')
	var senha = Cypress.config('senha')
	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/alunos/', () => {
		var codigo_eol = ''
		it('Validar GET de alunos com sucesso', () => {
			cy.validar_alunos(codigo_eol).then((response) => {
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').that.exist
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				const primeiro_resultado = response.body.results[0]
				expect(primeiro_resultado).to.have.property('uuid').that.exist
				expect(primeiro_resultado).to.have.property('nome').that.exist
				expect(primeiro_resultado).to.have.property('data_nascimento').that
					.exist
				expect(primeiro_resultado).to.have.property('codigo_eol').that.exist
				expect(primeiro_resultado).to.have.property('escola').that.null
			})
		})

		it('Validar GET de alunos com codigo EOL com sucesso', () => {
			var codigo_eol = '6577549/'
			cy.validar_alunos(codigo_eol).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.body).to.have.property('uuid').that.exist
				expect(response.body).to.have.property('nome').that.exist
				expect(response.body).to.have.property('data_nascimento').that.exist
				expect(response.body).to.have.property('codigo_eol').that.exist
			})
		})

		it('Validar GET de alunos com codigo EOL inválido', () => {
			var codigo_eol = '0/'
			cy.validar_alunos(codigo_eol).then((response) => {
				expect(response.status).to.eq(404)
				expect(response.body).to.exist
			})
		})

		it('Validar GET aluno pertence a escola retornando verdadeiro', () => {
			var codigo_eol = 6577549
			var escola_codigo_eol = 123456
			cy.validar_alunos_e_escola_codigo_eol(codigo_eol, escola_codigo_eol).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.exist
					expect(response.body).to.have.property('pertence_a_escola').that.true
				},
			)
		})

		it('Validar GET aluno pertence a escola retornando falso', () => {
			var codigo_eol = 6577549
			var escola_codigo_eol = '017981'
			cy.validar_alunos_e_escola_codigo_eol(codigo_eol, escola_codigo_eol).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.exist
					expect(response.body).to.have.property('pertence_a_escola').that.false
				},
			)
		})

		it('Validar GET para aluno nao matriculado detalhes dieta com sucesso', () => {
			var parametros = '?codigo_eol_escola=200018&nome_aluno=Teste'
			cy.validar_alunos_nao_matriculado_detalhes_dieta(parametros).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.exist
				},
			)
		})

		it('Validar GET sem codigo_eol_escola para aluno nao matriculado detalhes dieta', () => {
			var codigo_eol_escola = ''
			cy.validar_alunos_nao_matriculado_detalhes_dieta(codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.exist
					expect(response.body).to.contain(
						'`codigo_eol_escola` como query_param é obrigatório',
					)
				},
			)
		})

		it('Validar GET sem nome_aluno para aluno nao matriculado detalhes dieta', () => {
			var param_codigo_eol_escola = '?codigo_eol_escola=200018'
			cy.validar_alunos_nao_matriculado_detalhes_dieta(
				param_codigo_eol_escola,
			).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.exist
				expect(response.body).to.contain(
					'`nome_aluno` como query_param é obrigatório',
				)
			})
		})

		it('Validar GET sem query_param qtde aluno por periodo Cei Emei', () => {
			var codigo_eol_escola = '/'
			cy.validar_alunos_qtde_por_periodo_cei_emei(codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.exist
					expect(response.body).to.contain(
						'`codigo_eol_escola` como query_param é obrigatório',
					)
				},
			)
		})

		it('Validar GET qtde aluno por periodo Cei Emei para escola que não é CEMEI', () => {
			var param_codigo_eol_escola = '?codigo_eol_escola=000566'
			cy.validar_alunos_qtde_por_periodo_cei_emei(param_codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.exist
					expect(response.body).to.contain('escola não é CEMEI')
				},
			)
		})

		it('Validar GET qtde aluno por periodo Cei Emei com sucesso', () => {
			var param_codigo_eol_escola = '?codigo_eol_escola=019432'
			cy.validar_alunos_qtde_por_periodo_cei_emei(param_codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.exist
					response.body.forEach((item) => {
						expect(item).to.have.property('CEI').that.exist
						expect(item).to.have.property('EMEI').that.exist
						expect(item).to.have.property('nome').that.exist
					})
				},
			)
		})

		it('Validar GET qtde Cemei por Cei Emei com sucesso', () => {
			var param_codigo_eol_escola = '?codigo_eol_escola=019432'
			cy.validar_alunos_qtde_cemei_cei_emei(param_codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.exist
					response.body.forEach((item) => {
						expect(item).to.have.property('CEI').that.exist
						expect(item).to.have.property('EMEI').that.exist
					})
				},
			)
		})

		it('Validar GET qtde Cemei por Cei Emei para escola que não é CEMEI', () => {
			var param_codigo_eol_escola = '?codigo_eol_escola=000566'
			cy.validar_alunos_qtde_cemei_cei_emei(param_codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.exist
					expect(response.body).to.contain('escola não é CEMEI')
				},
			)
		})

		it('Validar GET sem query_param qtde Cemei por Cei Emei', () => {
			var codigo_eol_escola = ''
			cy.validar_alunos_qtde_cemei_cei_emei(codigo_eol_escola).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.exist
					expect(response.body).to.contain(
						'`codigo_eol_escola` como query_param é obrigatório',
					)
				},
			)
		})
	})
})
