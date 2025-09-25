/// <reference types='cypress' />

Cypress.Commands.add('validar_solicitacoes_dieta', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/classificacoes-dieta/${id}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
