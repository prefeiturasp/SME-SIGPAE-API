/// <reference types='cypress' />

describe('Validar rotas de Feriados Ano da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/feriados-ano/', () => {
		it('Validar GET com sucesso de Feriados Ano', () => {
			cy.consultar_feriados_ano().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})

		it('Validar GET com sucesso de Feriados Ano Atual e Próximo', () => {
			cy.consultar_feriados_ano_atual_e_proximo().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})
