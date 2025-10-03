/// <reference types='cypress' />

Cypress.Commands.add('consultar_fabricantes', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/fabricantes/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_fabricantes_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/fabricantes/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_fabricantes_lista_nomes_avaliar_reclamacao',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/fabricantes/lista-nomes-avaliar-reclamacao/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_fabricantes_lista_nomes_nova_reclamacao',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/fabricantes/lista-nomes-nova-reclamacao/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_nomes_responder_reclamacao_nutrisupervisao',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/fabricantes/lista-nomes-responder-reclamacao-nutrisupervisor/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_lista_nomes_unicos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/fabricantes/lista-nomes-unicos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
