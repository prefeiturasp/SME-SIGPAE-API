/// <reference types='cypress' />

Cypress.Commands.add('consultar_motivo_alteracao_ue', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/motivo-alteracao-ue/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
