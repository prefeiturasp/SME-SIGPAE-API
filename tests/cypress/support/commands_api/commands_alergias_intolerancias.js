/// <reference types='cypress' />

Cypress.Commands.add('validar_alergias_intolerancias', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alergias-intolerancias/${id}`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
