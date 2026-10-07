/// <reference types='cypress' />
Cypress.Commands.add('executar_fichas_de_recebimento', ({ caminho = '', method = 'GET', token = globalThis.token, qs, body, encoding = 'utf8' } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/fichas-de-recebimento/' + caminho,
		qs, body, encoding, headers: token ? { Authorization: 'JWT ' + token } : {},
		timeout: 60000, failOnStatusCode: false, log: false })
})
