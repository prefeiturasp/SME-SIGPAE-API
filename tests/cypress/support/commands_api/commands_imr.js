/// <reference types='cypress' />

Cypress.Commands.add('consultar_imr_equipamentos', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/equipamentos/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_insumos', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/insumos/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_mobiliarios', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/mobiliarios/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_periodos_visita', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/periodos-de-visita/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_reparos_adaptacoes', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/reparos-e-adaptacoes/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_utensilios_cozinha', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/utensilios-cozinha/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_imr_utensilios_mesa', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/utensilios-mesa/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_imr_formulario_supervisao_por_status',
	(status) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/imr/formulario-supervisao/?status=${status}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_imr_formulario_supervisao_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/imr/formulario-supervisao/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_imr_formulario_supervisao_respostas',
	(uuid) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/imr/formulario-supervisao/${uuid}/respostas/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_imr_formulario_supervisao_respostas_nao_aplica',
	(uuid) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/imr/formulario-supervisao/${uuid}/respostas_nao_se_aplica/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_imr_formulario_supervisao_dashboard',
	(status) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') + 'api/imr/formulario-supervisao/dashboard/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_imr_formulario_supervisao_lista_nomes_nutricionistas',
	(status) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/imr/formulario-supervisao/lista_nomes_nutricionistas/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
