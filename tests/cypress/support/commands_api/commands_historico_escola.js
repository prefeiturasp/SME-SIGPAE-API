/// <reference types='cypress' />

Cypress.Commands.add('executar_historico_escola', ({ uuid, method = 'GET', token = globalThis.token, qs, body } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/historico-escola/' + encodeURIComponent(uuid) + '/',
		qs, body, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false })
})
