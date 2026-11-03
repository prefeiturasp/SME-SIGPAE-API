/// <reference types='cypress' />

Cypress.Commands.add('executar_homologacoes_produtos', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/homologacoes-produtos/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
