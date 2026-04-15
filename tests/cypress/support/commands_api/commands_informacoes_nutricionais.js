/// <reference types='cypress' />

Cypress.Commands.add('consultar_informacoes_nutricionais', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/informacoes-nutricionais/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_informacoes_nutricionais_agrupadas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/informacoes-nutricionais/agrupadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_informacoes_nutricionais_ordenadas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/informacoes-nutricionais/ordenadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
