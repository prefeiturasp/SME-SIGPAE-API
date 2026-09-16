import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar faixas etarias', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto as faixas etarias', function () {
	cy.consultar_faixas_etarias().then((response) => {
		this.response = response
	})
})

Then('a consulta de faixas etarias deve retornar status 200 e dados paginados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.to.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'inicio', 'fim')
})
