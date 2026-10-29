/// <reference types='cypress' />

Cypress.Commands.add('executar_inclusao_alimentacao', ({ method = 'GET', caminho = '', token = globalThis.token, qs } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/inclusao-alimentacao/' + caminho,
		qs, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
