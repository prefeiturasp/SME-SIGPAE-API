/// <reference types='cypress' />

Cypress.Commands.add('dre_consultar_pendentes_autorizacao_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/pendentes-autorizacao-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_autorizados_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/autorizados-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_inativas_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/inativas-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_negados_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/negados-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_cancelados_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/cancelados-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'dre_consultar_autorizadas_temporariamente_dieta',
	(uuid) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/diretoria-regional-solicitacoes/autorizadas-temporariamente-dieta/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('dre_consultar_autorizados', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/autorizados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_cancelados', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/cancelados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_inativas_temporariamente_dieta', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/diretoria-regional-solicitacoes/inativas-temporariamente-dieta/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_negados', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/negados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_pendentes_autorizacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/pendentes-autorizacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('dre_consultar_solicitacoes_detalhadas', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/solicitacoes-detalhadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'dre_consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao',
	(filtro, visao) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/diretoria-regional-solicitacoes/pendentes-validacao/${filtro}/${visao}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('dre_consultar_aguardando_codae', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/diretoria-regional-solicitacoes/aguardando-codae/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
