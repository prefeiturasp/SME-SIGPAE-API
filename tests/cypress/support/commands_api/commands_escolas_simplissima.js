/// <reference types='cypress' />

Cypress.Commands.add('consultar_escola_simplissima', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/escolas-simplissima/?page=1&page_size=2',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_escola_simplissima_por_dre', (dre_uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/escolas-simplissima/?page=1&page_size=2&diretoria_regional__uuid=${dre_uuid}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('executar_escolas_simplissimas', ({ caminho = '', qs = {}, metodo = 'GET', token } = {}) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/escolas-simplissima/${caminho ? `${encodeURIComponent(caminho)}/` : ''}`,
		qs,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
