/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_email',
	(parametros = { limit: 10, offset: 0 }, autenticado = true) => {
		const headers = autenticado
			? { Authorization: 'JWT ' + globalThis.token }
			: undefined

		return cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/email/',
			qs: parametros,
			timeout: 60000,
			headers,
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'cadastrar_email',
	(dadosEmail, autenticado = true) => {
		const headers = autenticado
			? { Authorization: 'JWT ' + globalThis.token }
			: undefined

		return cy.request({
			method: 'POST',
			url: Cypress.config('baseUrl') + 'api/email/',
			body: dadosEmail,
			timeout: 60000,
			headers,
			failOnStatusCode: false,
		})
	},
)
