/// <reference types='cypress' />

Cypress.Commands.add('consultar_motivos_negacao', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/motivos-negacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_motivos_negacao_por_processo', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/motivos-negacao/${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_motivos_negacao_por_id', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/motivos-negacao/${id}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
