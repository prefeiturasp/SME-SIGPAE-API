/// <reference types='cypress' />

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

Cypress.Commands.add('atualizar_email_terceirizada_modulo', (uuid, dados) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/emails-terceirizadas-modulos/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: dados,
		failOnStatusCode: false,
	})
})