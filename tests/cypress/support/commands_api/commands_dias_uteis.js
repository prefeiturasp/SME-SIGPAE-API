/// <reference types='cypress' />

Cypress.Commands.add('consultar_dias_uteis', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/dias-uteis/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
