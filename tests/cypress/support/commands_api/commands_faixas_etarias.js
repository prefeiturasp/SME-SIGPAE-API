/// <reference types='cypress' />

Cypress.Commands.add('executar_faixas_etarias', ({ method = 'GET', body, qs, token = globalThis.token } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/faixas-etarias/', body, qs,
		headers: token ? { Authorization: 'JWT ' + token } : {}, timeout: 60000, failOnStatusCode: false })
})
Cypress.Commands.add('consultar_faixas_etarias', () => cy.executar_faixas_etarias())
