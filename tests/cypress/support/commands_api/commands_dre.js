/// <reference types='cypress' />

Cypress.Commands.add('consultar_dre_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/diretorias-regionais/${uuid}/`,
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
