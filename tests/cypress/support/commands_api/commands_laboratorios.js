/// <reference types='cypress' />

Cypress.Commands.add('consultar_laboratorios', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_laboratorios_com_filtros', (filtros) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/laboratorios/${filtros}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_laboratorios_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/laboratorios/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_laboratorios', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/laboratorios/lista-laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_laboratorios_credenciados', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/laboratorios/lista-laboratorios-credenciados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_nomes_laboratorios', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/laboratorios/lista-nomes-laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
