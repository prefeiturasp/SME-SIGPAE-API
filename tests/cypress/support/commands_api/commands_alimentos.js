/// <reference types='cypress' />

Cypress.Commands.add('validar_alimentos', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alimentos/${id}`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
