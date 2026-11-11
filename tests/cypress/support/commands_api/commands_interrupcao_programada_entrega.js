/// <reference types='cypress' />

Cypress.Commands.add('executar_interrupcao_programada_entrega', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/interrupcao-programada-entrega/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
