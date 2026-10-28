/// <reference types='cypress' />

Cypress.Commands.add('executar_inclusao_alimentacao_cemei', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body, encoding = 'utf8' } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/inclusao-alimentacao-cemei/' + caminho,
		qs, body, encoding, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
