/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_conferencia_da_guia_com_ocorrencia',
	(parametros = 'limit=10&offset=1') => {
		return cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/conferencia-da-guia-com-ocorrencia/?${parametros}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
