/// <reference types='cypress' />

Cypress.Commands.add('confirmar_email', (uuid, chaveConfirmacao) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/confirmar_email/${encodeURIComponent(uuid)}/${encodeURIComponent(chaveConfirmacao)}/`,
		timeout: 60000,
		failOnStatusCode: false,
	})
})
