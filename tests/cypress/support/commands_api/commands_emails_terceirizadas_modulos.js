/// <reference types='cypress' />

Cypress.Commands.add('cadastrar_email_terceirizada_modulo', (dados) => {
	return cy.request({
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
	return cy.request({
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

Cypress.Commands.add('executar_email_terceirizada_modulo', ({ metodo, uuid = '', body, autenticado = true }) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/emails-terceirizadas-modulos/${uuid ? `${uuid}/` : ''}`,
		body,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
