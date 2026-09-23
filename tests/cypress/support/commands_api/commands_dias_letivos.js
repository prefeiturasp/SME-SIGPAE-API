/// <reference types='cypress' />

Cypress.Commands.add('consultar_dias_letivos', ({ ano, mes, usuario, senha }) => {
	return cy.autenticar_login(usuario, senha).then(() => {
		return cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/dias-letivos/',
			qs: {
				ano,
				mes,
			},
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	})
})

Cypress.Commands.add('executar_dias_letivos', (metodo, caminho = '', body, qs = {}, autenticado = true) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/dias-letivos/${caminho ? `${caminho}/` : ''}`,
		body, qs,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
