/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_emails_terceirizadas_modulos',
	(parametros = { limit: 10, offset: 0 }, autenticado = true) => {
		const headers = autenticado
			? { Authorization: 'JWT ' + globalThis.token }
			: undefined

		cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/emails-terceirizadas-modulos/',
			qs: parametros,
			timeout: 60000,
			headers,
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('cadastrar_email_terceirizada_modulo', (dados) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/emails-terceirizadas-modulos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: dados,
		failOnStatusCode: false,
	})
})
