/// <reference types='cypress' />

Cypress.Commands.add('consultar_api_version', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/api-version/',
		timeout: 60000,
		failOnStatusCode: false,
	})
})
