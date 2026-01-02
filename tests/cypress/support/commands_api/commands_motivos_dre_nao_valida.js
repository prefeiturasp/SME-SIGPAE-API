/// <reference types='cypress' />

Cypress.Commands.add('consultar_motivos_dre_nao_valida', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/motivos-dre-nao-valida/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_motivos_dre_nao_valida_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/motivos-dre-nao-valida/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
