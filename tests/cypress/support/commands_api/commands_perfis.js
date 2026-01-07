/// <reference types='cypress' />

Cypress.Commands.add('consultar_perfis', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/perfis/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_perfis_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/perfis/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_perfis_visoes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/perfis/visoes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
