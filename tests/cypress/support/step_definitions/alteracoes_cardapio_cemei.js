import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto as alteracoes de cardapio CEMEI', function () {
	const baseUrl =
		Cypress.env('base_url_alteracoes_cardapio_cemei') ||
		'https://hom-sigpae.sme.prefeitura.sp.gov.br/'

	cy.request({
		method: 'GET',
		url: baseUrl + 'api/alteracoes-cardapio-cemei/',
		timeout: 120000,
		auth: {
			username: Cypress.env('usuario_diretor_ue'),
			password: Cypress.env('senha'),
		},
		failOnStatusCode: false,
	}).then((response) => {
		this.response = response
	})
})

Then('deve retornar a listagem paginada de alteracoes CEMEI', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.have.all.keys(
		'count',
		'next',
		'previous',
		'results',
	)
	expect(this.response.body.count).to.be.a('number')
	expect(this.response.body.results).to.be.an('array')
})
