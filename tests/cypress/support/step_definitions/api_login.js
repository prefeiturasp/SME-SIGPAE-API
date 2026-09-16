import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('realizo o login da API com o usuario coordenador de logistica', function () {
	cy.autenticar_login(
		Cypress.config('usuario_coordenador_logistica'),
		Cypress.config('senha'),
	).then((response) => {
		this.response = response
	})
})

Then('o login da API deve retornar status 200 e token de acesso', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.statusText).to.eq('OK')
	expect(this.response.body.access).to.exist
})
