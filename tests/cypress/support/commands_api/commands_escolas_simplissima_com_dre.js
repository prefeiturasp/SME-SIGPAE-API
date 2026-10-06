/// <reference types='cypress' />

Cypress.Commands.add('executar_escola_simplissima_dre', ({ method = 'GET', uuid, qs = { limit: 10 }, token = globalThis.token } = {}) => {
	return cy.request({
		method,
		log: false,
		url: Cypress.config('baseUrl') + 'api/escolas-simplissima-com-dre/' + (uuid ? `${uuid}/` : ''),
		qs,
		timeout: 60000,
		headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false,
	})
})
Cypress.Commands.add('consultar_escola_simplissima_dre', () => cy.executar_escola_simplissima_dre())
Cypress.Commands.add('consultar_escola_simplissima_dre_por_uuid', (uuid) => cy.executar_escola_simplissima_dre({ uuid }))
