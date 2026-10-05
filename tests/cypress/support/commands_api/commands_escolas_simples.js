/// <reference types='cypress' />

Cypress.Commands.add('executar_escolas_simples', ({ metodo = 'GET', uuid = '', qs = {}, body, token } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/escolas-simples/${uuid ? `${encodeURIComponent(uuid)}/` : ''}`,
		qs, body,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
