/// <reference types='cypress' />

Cypress.Commands.add('validar_calendario_cronogramas', (parametros = '', opcoes = {}) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/calendario-cronogramas/${opcoes.id === undefined ? '' : `${encodeURIComponent(opcoes.id)}/`}${parametros.replace(/^\//, '')}`,
		timeout: 60000,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		failOnStatusCode: false,
	})
})
