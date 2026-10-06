/// <reference types='cypress' />

Cypress.Commands.add('executar_escola_simplissima_eol', ({ method = 'GET', uuid, qs = { limit: 10 }, token = globalThis.token } = {}) => {
	return cy.request({
		method,
		log: false,
		url: Cypress.config('baseUrl') + 'api/escolas-simplissima-com-eol/' + (uuid ? `${uuid}/` : ''),
		qs,
		timeout: 60000,
		headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false,
	})
})
Cypress.Commands.add('consultar_escola_simplissima_eol', () => cy.executar_escola_simplissima_eol())
Cypress.Commands.add('consultar_escola_simplissima_eol_por_uuid', (uuid) => cy.executar_escola_simplissima_eol({ uuid }))

Cypress.Commands.add('executar_acao_escolas_eol', ({ acao, body = {}, token = globalThis.token, method = 'POST' }) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + `api/escolas-simplissima-com-eol/${acao}/`, body,
		headers: token ? { Authorization: 'JWT ' + token } : {}, timeout: 60000, failOnStatusCode: false, log: false })
})
