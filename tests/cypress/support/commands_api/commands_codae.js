/// <reference types='cypress' />

Cypress.Commands.add('consultar_codae', (parametros = 'limit=10&offset=0') => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/codae/?${parametros}`,
		timeout: 60000,
		headers: {
			Authorization: `JWT ${globalThis.token}`,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('requisitar_codae', (metodo, opcoes = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/codae/${opcoes.uuid ? `${encodeURIComponent(opcoes.uuid)}/` : ''}`,
		qs: opcoes.query,
		body: opcoes.dados,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		timeout: 60000,
		failOnStatusCode: false,
	})
})
