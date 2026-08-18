/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_conferencia_individual',
	(parametros = { limit: 10, offset: 0 }) => {
		return cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/conferencia-individual/',
			qs: parametros,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
