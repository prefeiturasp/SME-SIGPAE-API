/// <reference types='cypress' />

Cypress.Commands.add('executar_guias_da_requisicao', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/guias-da-requisicao/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false })
})
