/// <reference types='cypress' />

Cypress.Commands.add('consultar_modalidades', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/modalidades/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_modalidades_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/modalidades/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
