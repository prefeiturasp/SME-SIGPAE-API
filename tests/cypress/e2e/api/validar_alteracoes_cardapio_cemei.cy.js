/// <reference types='cypress' />

describe('Validar rota de alterações de cardápio CEMEI da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_diretor_ue')
	const senha = Cypress.env('senha')
	const baseUrl =
		Cypress.env('base_url_alteracoes_cardapio_cemei') ||
		'https://hom-sigpae.sme.prefeitura.sp.gov.br/'

	context('Casos de teste para a rota /api/alteracoes-cardapio-cemei/', () => {
		it('Validar GET de alterações de cardápio CEMEI com sucesso', () => {
			cy.request({
				method: 'GET',
				url: baseUrl + 'api/alteracoes-cardapio-cemei/',
				timeout: 120000,
				auth: {
					username: usuario,
					password: senha,
				},
				failOnStatusCode: false,
			}).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.have.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})
