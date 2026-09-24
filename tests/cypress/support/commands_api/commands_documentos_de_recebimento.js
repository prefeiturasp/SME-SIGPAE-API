/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_documentos_de_recebimento',
	(parametros = { limit: 10, offset: 0 }) => {
		return cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/documentos-de-recebimento/',
			qs: parametros,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('gerar_documentos_de_recebimento', () => {
	return cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/documentos-de-recebimento/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('executar_documentos_recebimento', ({ metodo = 'GET', caminho = '', body, qs = {}, autenticado = true } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/documentos-de-recebimento/${caminho ? `${caminho}/` : ''}`,
		body, qs,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
