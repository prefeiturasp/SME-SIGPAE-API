/// <reference types='cypress' />

Cypress.Commands.add('consultar_motivos_alteracao_cardapio', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/motivos-alteracao-cardapio/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_motivos_alteracao_cardapio_por_uuid',
	(uuid) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') + `api/motivos-alteracao-cardapio/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
