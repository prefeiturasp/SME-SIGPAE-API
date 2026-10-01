/// <reference types='cypress' />

Cypress.Commands.add('consultar_somatorio_faixas_etarias', ({ uuid, data, metodo = 'GET', token }) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/escola-quantidade-alunos-por-periodo-e-faixa-etaria/${encodeURIComponent(uuid)}/somatorio-faixas-etarias/${encodeURIComponent(data)}/`,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})

Cypress.Commands.add('consultar_escola_para_somatorio', () => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/escolas-simplissima/`,
		qs: { page: 1, page_size: 1 },
		headers: { Authorization: `JWT ${globalThis.token}` },
		failOnStatusCode: false,
		timeout: 60000,
	})
})
