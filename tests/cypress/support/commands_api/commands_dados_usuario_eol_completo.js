/// <reference types='cypress' />

Cypress.Commands.add('consultar_dados_usuario_eol_completo', (registroFuncional, token) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/dados-usuario-eol-completo/${encodeURIComponent(registroFuncional)}/`,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
