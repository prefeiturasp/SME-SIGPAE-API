/// <reference types='cypress' />
Cypress.Commands.add('executar_dias_suspensao', ({ metodo = 'GET', caminho = '', body, qs = {}, autenticado = true } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/dias-suspensao-atividades/${caminho ? `${caminho}/` : ''}`,
		body, qs,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
