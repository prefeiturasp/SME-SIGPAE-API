/// <reference types='cypress' />

Cypress.Commands.add('consultar_periodos_escolares', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/periodos-escolares/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_periodos_escolares_por_nome', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/periodos-escolares/?nome=${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_periodos_escolares_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/periodos-escolares/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_alunos_por_faixa_etaria_data_referencia',
	(uuid, data_referencia) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/periodos-escolares/${uuid}/alunos-por-faixa-etaria/${data_referencia}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_inclusao_continua_por_mes', (param) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/periodos-escolares/inclusao-continua-por-mes/${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
