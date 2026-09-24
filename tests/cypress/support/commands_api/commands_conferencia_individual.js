/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_conferencia_individual',
	(parametros = { limit: 10, offset: 0 }) => {
		return cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/conferencia-individual/',
			qs: parametros,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('requisitar_conferencia_individual', (metodo, opcoes = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/conferencia-individual/${opcoes.uuid ? `${encodeURIComponent(opcoes.uuid)}/` : ''}`,
		body: opcoes.dados,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		timeout: 60000,
		failOnStatusCode: false,
	})
})
