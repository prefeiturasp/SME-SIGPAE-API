<<<<<<< HEAD
﻿describe('Validar rotas de Motivo Alteração UE da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
﻿describe('Validar rotas de Motivo AlteraÃ§Ã£o UE da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/motivo-alteracao-ue/', () => {
		it('Validar GET com sucesso de Motivo AlteraÃ§Ã£o UE', () => {
			cy.consultar_motivo_alteracao_ue().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('descricao')
			})
		})
	})
})

