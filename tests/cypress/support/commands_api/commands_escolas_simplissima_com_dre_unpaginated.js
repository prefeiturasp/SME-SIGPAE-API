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

Cypress.Commands.add('executar_escolas_dre_sem_paginacao', ({ caminho = '', method = 'GET', token = globalThis.token, qs = {} } = {}) => {
	return cy.request({
		method,
		log: false,
		url: Cypress.config('baseUrl') + 'api/escolas-simplissima-com-dre-unpaginated/' + caminho,
		qs,
		headers: token ? { Authorization: 'JWT ' + token } : {},
		timeout: 60000,
		failOnStatusCode: false,
	})
})
