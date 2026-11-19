/// <reference types='cypress' />

Cypress.Commands.add('executar_lancamento_diario', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/lancamento-diario/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})

Cypress.Commands.add('consultar_referencia_lancamento_diario', () => {
	return cy.request({
		method: 'GET', url: Cypress.config('baseUrl') + 'api/quantidade-alunos-por-periodo/',
		qs: { limit: 1 }, headers: { Authorization: 'JWT ' + globalThis.token },
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
