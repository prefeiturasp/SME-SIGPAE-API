/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_escola_simplissima_dre_unpaginated_por_uuid',
	(uuid) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/escolas-simplissima-com-dre-unpaginated/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
