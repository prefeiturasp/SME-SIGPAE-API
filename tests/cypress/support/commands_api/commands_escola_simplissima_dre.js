/// <reference types='cypress' />

Cypress.Commands.add('consultar_escola_simplissima_dre', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/escolas-simplissima-com-dre/?limit=10',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_dre_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima-com-dre/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
