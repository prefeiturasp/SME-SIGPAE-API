/// <reference types='cypress' />

Cypress.Commands.add('consultar_dre_simplissima', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/diretorias-regionais-simplissima/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_dre_simplissima_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretorias-regionais-simplissima/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_completa_dre_simplissima', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretorias-regionais-simplissima/lista-completa/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
