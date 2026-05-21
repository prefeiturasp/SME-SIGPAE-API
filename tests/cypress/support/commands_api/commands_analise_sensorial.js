/// <reference types='cypress' />

Cypress.Commands.add('consultar_analise_sensorial', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/analise-sensorial/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_analise_sensorial_com_filtros', (filtro) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/analise-sensorial/${filtro}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
