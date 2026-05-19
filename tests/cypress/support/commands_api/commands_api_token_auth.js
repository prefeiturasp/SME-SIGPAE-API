/// <reference types='cypress' />

Cypress.Commands.add('autenticar_api_token_auth', (username, password) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/api-token-auth/',
		timeout: 60000,
		body: {
			username,
			password,
		},
		failOnStatusCode: false,
	})
})
