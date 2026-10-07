/// <reference types='cypress' />
Cypress.Commands.add('executar_ficha_tecnica', ({ caminho = '', method = 'GET', token = globalThis.token, qs, body } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/ficha-tecnica/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		timeout: 60000, failOnStatusCode: false, log: false })
})
