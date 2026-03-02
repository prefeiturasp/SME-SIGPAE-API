/// <reference types='cypress' />

Cypress.Commands.add('consultar_terceirizadas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_nome', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/?nome=${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_terceirizadas', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
