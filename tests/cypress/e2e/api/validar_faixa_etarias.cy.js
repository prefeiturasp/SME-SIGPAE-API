/// <reference types='cypress' />

describe('Validar rotas de Faixas Etárias da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/faixas-etarias/', () => {
		it('Validar GET com sucesso de Faixas Etárias', () => {
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
