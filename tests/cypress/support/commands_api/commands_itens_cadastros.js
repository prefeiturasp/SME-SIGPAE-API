/// <reference types='cypress' />

Cypress.Commands.add('consultar_itens_cadastros', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/itens-cadastros/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_itens_cadastros_com_filtros', (filtros) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/itens-cadastros/${filtros}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_itens_cadastros_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/itens-cadastros/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_itens_cadastros_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/itens-cadastros/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_itens_cadastros_tipos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/itens-cadastros/tipos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
