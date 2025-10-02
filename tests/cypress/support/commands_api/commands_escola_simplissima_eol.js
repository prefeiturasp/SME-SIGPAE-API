/// <reference types='cypress' />

Cypress.Commands.add('consultar_escola_simplissima_eol', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/escolas-simplissima-com-eol/?limit=10&offset=2',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_eol_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima-com-eol/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
