/// <reference types='cypress' />

Cypress.Commands.add('consultar_codae', (parametros = 'limit=10&offset=1') => {
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
