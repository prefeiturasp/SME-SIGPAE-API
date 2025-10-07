/// <reference types='cypress' />

Cypress.Commands.add('consultar_feriados_ano', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/feriados-ano/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_feriados_ano_atual_e_proximo', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/feriados-ano/ano-atual-e-proximo/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
