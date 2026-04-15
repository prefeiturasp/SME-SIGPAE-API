/// <reference types='cypress' />

<<<<<<< HEAD
describe('Validar rotas de Feriados Ano da aplicaçãoo SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
describe('Validar rotas de Feriados Ano da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

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

		it('Validar GET com sucesso de Feriados Ano Atual e PrÃ³ximo', () => {
			cy.consultar_feriados_ano_atual_e_proximo().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})

