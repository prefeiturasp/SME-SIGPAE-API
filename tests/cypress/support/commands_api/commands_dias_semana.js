/// <reference types='cypress' />

Cypress.Commands.add('consultar_dias_semana', (token) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/dias-semana/`,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
	})
})
