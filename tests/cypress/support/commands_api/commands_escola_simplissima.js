/// <reference types='cypress' />

Cypress.Commands.add('consultar_escola_simplissima', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/escolas-simplissima/?page=2&page_size=0',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_por_dre', (dre_uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima/${dre_uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
