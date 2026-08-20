/// <reference types='cypress' />

Cypress.Commands.add('consultar_embalagens_produto', (query = {}) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/embalagens-produto/',
		qs: query,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
