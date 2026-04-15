/// <reference types='cypress' />

Cypress.Commands.add('consultar_nome_de_produtos_edital', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/nome-de-produtos-edital/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
