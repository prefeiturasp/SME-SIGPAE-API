/// <reference types='cypress' />

Cypress.Commands.add('consultar_editais', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/editais/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_editais_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/editais/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_numeros_editais', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/editais/lista-numeros/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
