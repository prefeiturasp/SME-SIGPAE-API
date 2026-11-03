/// <reference types='cypress' />

Cypress.Commands.add('executar_horario_combo_unidade_escolar', ({ method = 'GET', caminho = '', token = globalThis.token, qs, body } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/horario-do-combo-tipo-de-alimentacao-por-unidade-escolar/' + caminho,
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})
