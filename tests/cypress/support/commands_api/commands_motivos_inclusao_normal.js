/// <reference types='cypress' />

Cypress.Commands.add('consultar_motivos_inclusao_normal', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/motivos-inclusao-normal/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_motivos_inclusao_normal_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/motivos-inclusao-normal/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
