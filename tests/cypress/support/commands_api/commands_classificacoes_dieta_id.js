/// <reference types='cypress' />

Cypress.Commands.add('consultar_classificacao_dieta_por_id', (id) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/classificacoes-dieta/${id}/`,
		timeout: 60000,
		headers: {
			Authorization: `JWT ${globalThis.token}`,
		},
		failOnStatusCode: false,
	})
})
