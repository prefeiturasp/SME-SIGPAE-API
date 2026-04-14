describe('Validar rotas de Nome de Produtos Edital da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/nome-de-produtos-edital/', () => {
		it('Validar GET com sucesso de Nome de Produtos Edital', () => {
			cy.consultar_nome_de_produtos_edital().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})
	})
})

