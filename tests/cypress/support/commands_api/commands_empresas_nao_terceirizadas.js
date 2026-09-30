/// <reference types='cypress' />

Cypress.Commands.add('executar_empresas_nao_terceirizadas', (metodo, uuid = '', body, autenticado = true) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/empresas-nao-terceirizadas/${uuid ? `${uuid}/` : ''}`,
		body,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
