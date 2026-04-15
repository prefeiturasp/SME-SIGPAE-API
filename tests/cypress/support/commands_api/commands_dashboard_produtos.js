/// <reference types='cypress' />

Cypress.Commands.add('consultar_aguardando_analise_reclamacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/dashboard-produtos/aguardando-analise-reclamacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_homologados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/dashboard-produtos/homologados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_nao_homologados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/dashboard-produtos/nao-homologados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_questionamento_codae', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/dashboard-produtos/questionamento-da-codae/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_suspensos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/dashboard-produtos/suspensos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_correcao_produtos', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/dashboard-produtos/correcao-de-produtos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_aguardando_amostra_analise_sensorial', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/dashboard-produtos/aguardando-amostra-analise-sensorial/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_pendente_homologacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/dashboard-produtos/pendente-homologacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
