/// <reference types='cypress' />

Cypress.Commands.add('consultar_perfis_vinculados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/perfis-vinculados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_perfis_vinculados_por_perfil_master',
	(perfil_master) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') + `api/perfis-vinculados/${perfil_master}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_perfis_subordinados_por_perfil_master',
	(perfil_master) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/perfis-vinculados/${perfil_master}/perfis-subordinados/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
