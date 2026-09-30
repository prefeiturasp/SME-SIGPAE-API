/// <reference types='cypress' />

Cypress.Commands.add('executar_dias_calendario', ({ metodo = 'GET', id = '', filtros = {}, body, autenticado = true } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/dias-calendario/${id !== '' ? `${encodeURIComponent(id)}/` : ''}`,
		qs: filtros,
		body,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
