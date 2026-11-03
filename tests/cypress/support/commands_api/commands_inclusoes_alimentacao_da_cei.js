/// <reference types='cypress' />

Cypress.Commands.add('executar_inclusoes_alimentacao_da_cei', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body, encoding = 'utf8' } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/inclusoes-alimentacao-da-cei/' + caminho,
		qs, body, encoding, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
