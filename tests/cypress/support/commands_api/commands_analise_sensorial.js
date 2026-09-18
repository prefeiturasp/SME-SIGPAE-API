/// <reference types='cypress' />

Cypress.Commands.add('consultar_analise_sensorial', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/analise-sensorial/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_analise_sensorial_com_filtros', (filtro) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/analise-sensorial/${filtro}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('requisitar_analise_sensorial', (metodo, caminho = '', dados, autenticado = true) => {
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/analise-sensorial/${caminho}`,
		body: dados,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		timeout: 60000,
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_referencia_analise_sensorial', () => {
	return cy.request({
		url: `${Cypress.config('baseUrl')}api/produtos/filtro-relatorio-em-analise-sensorial/`,
		qs: { limit: 1 },
		headers: { Authorization: `JWT ${globalThis.token}` },
		timeout: 60000,
		failOnStatusCode: false,
	}).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		return response.body.results[0].ultima_homologacao
	})
})
