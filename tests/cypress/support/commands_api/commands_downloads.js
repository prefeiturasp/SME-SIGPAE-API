/// <reference types='cypress' />

Cypress.Commands.add('executar_downloads', ({ metodo = 'GET', caminho = '', body, qs = {}, autenticado = true } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/downloads/${caminho ? `${caminho}/` : ''}`,
		body,
		qs,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
