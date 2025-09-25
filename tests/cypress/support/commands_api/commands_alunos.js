/// <reference types='cypress' />

Cypress.Commands.add('validar_alunos', (codigo_eol) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alunos/${codigo_eol}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'validar_alunos_e_escola_codigo_eol',
	(codigo_eol, escola_codigo_eol) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/alunos/${codigo_eol}/aluno-pertence-a-escola/${escola_codigo_eol}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'validar_alunos_nao_matriculado_detalhes_dieta',
	(codigo_eol_escola) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/alunos/dados-aluno-nao-matriculado-detalhes-dieta/${codigo_eol_escola}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'validar_alunos_qtde_por_periodo_cei_emei',
	(codigo_eol_escola) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/alunos/quantidade-alunos-por-periodo-cei-emei/${codigo_eol_escola}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'validar_alunos_qtde_cemei_cei_emei',
	(codigo_eol_escola) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/alunos/quantidade-cemei-por-cei-emei/${codigo_eol_escola}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)
