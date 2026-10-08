/// <reference types='cypress' />
Cypress.Commands.add('executar_grupos_inclusao_alimentacao_normal', ({ caminho = '', method = 'GET', token = globalThis.token, qs, body, encoding = 'utf8' } = {}) => {
	return cy.request({ method, url: Cypress.config('baseUrl') + 'api/grupos-inclusao-alimentacao-normal/' + caminho,
		qs, body, encoding, headers: token ? { Authorization: 'JWT ' + token } : {}, timeout: 60000, failOnStatusCode: false, log: false })
})
