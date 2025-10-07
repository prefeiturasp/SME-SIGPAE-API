/// <reference types='cypress' />

Cypress.Commands.add('consultar_faixas_etarias', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/faixas-etarias/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
