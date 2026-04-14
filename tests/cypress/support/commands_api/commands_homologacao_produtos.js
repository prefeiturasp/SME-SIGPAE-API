/// <reference types='cypress' />

Cypress.Commands.add('validar_homologacao_produtos', (query) => {
	return cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/homologacoes-produtos/${query}`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
		timeout: 60000,
	})
})