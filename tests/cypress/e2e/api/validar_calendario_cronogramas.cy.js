/// <reference types='cypress' />

describe('Validar rotas de calendario cronogramas da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_cronograma')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/calendario-cronogramas/', () => {
		it('Validar GET de calendario cronogramas com sucesso', () => {
			var parametros = '/?mes=3&ano=2025'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body).to.have.property('detail')
				expect(response.body.detail).to.not.be.empty
			})
		})

		it('Validar GET de calendario cronogramas sem parametros', () => {
			var parametros = ''
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body).to.have.property('detail')
				expect(response.body.detail).to.not.be.empty
			})
		})

		it('Validar GET de calendario cronogramas com ano invalido', () => {
			var parametros = '/?mes=3&ano=202'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body).to.have.property('detail')
				expect(response.body.detail).to.not.be.empty
			})
		})

		it('Validar GET de calendario cronogramas com mes invalido', () => {
			var parametros = '/?mes=13&ano=2025'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(403)
				expect(response.body).to.have.property('detail')
				expect(response.body.detail).to.not.be.empty
			})
		})
	})
})
