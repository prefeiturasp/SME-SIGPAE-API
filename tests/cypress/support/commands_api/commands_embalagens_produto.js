/// <reference types='cypress' />

Cypress.Commands.add('consultar_embalagens_produto', (query = {}) => {
	return cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/embalagens-produto/',
		qs: query,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('executar_embalagens_produto', (metodo, uuid = '', body, autenticado = true) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/embalagens-produto/${uuid ? `${uuid}/` : ''}`,
		body,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
