/// <reference types='cypress' />

Cypress.Commands.add('consultar_terceirizadas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_nome', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/?nome=${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_terceirizadas', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_emails_modulos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/emails-por-modulo/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_lista_cnpjs', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-cnpjs/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_empresas_cronogramas', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/terceirizadas/lista-empresas-cronograma/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_terceirizadas_lista_nomes_distribuidores',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/terceirizadas/lista-nomes-distribuidores/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_terceirizadas_lista_simples', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-simples/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_relatorio_quantitativo', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/terceirizadas/relatorio-quantitativo/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
