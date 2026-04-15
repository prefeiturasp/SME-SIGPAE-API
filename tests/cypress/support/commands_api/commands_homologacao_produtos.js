/// <reference types='cypress' />

Cypress.Commands.add('validar_homologacao_produtos', (query = {}) => {
	const parametros =
		typeof query === 'string'
			? Object.fromEntries(new URLSearchParams(query.replace(/^\?/, '')))
			: query

	return cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/homologacoes-produtos/',
		qs: parametros,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
