/// <reference types='cypress' />

<<<<<<< HEAD
describe('Validar rotas de Faixas Etárias da aplicaçãoo SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
describe('Validar rotas de Faixas EtÃ¡rias da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/faixas-etarias/', () => {
		it('Validar GET com sucesso de Faixas EtÃ¡rias', () => {
			cy.consultar_faixas_etarias().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('uuid')
				expect(response.body.results[0]).property('inicio')
				expect(response.body.results[0]).property('fim')
			})
		})
	})
})

