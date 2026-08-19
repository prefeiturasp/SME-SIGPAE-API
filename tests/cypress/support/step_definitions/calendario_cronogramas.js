import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado para consultar o calendario de cronogramas', () => {
	cy.autenticar_login(
		Cypress.config('usuario_dilog_cronograma'),
		Cypress.config('senha'),
	)
})
When('consulto o calendario de cronogramas com parametros {string}', function (parametros) {
	cy.validar_calendario_cronogramas(parametros).then((response) => {
		this.response = response
	})
})
Then('o calendario de cronogramas retorna status 403 e detalhe', function () {
	expect(this.response.status).to.eq(403)
	expect(this.response.body.detail).to.exist.and.not.be.empty
})
