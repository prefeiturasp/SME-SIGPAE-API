/// <reference types='cypress' />

Cypress.Commands.add('consultar_pendentes_autorizacao_dieta', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/codae-solicitacoes/pendentes-autorizacao-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_autorizados_dieta', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/codae-solicitacoes/autorizados-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_inativas_dieta', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/inativas-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_negados_dieta', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/negados-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_cancelados_dieta', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/cancelados-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_autorizadas_temporariamente_dieta', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/codae-solicitacoes/autorizadas-temporariamente-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_autorizados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/autorizados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_cancelados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/cancelados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_inativas_temporariamente_dieta', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/codae-solicitacoes/inativas-temporariamente-dieta/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_negados', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/negados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_pendentes_autorizacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/codae-solicitacoes/pendentes-autorizacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_questionamentos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/codae-solicitacoes/questionamentos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_solicitacoes_detalhadas', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/codae-solicitacoes/solicitacoes-detalhadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_pendentes_autorizacao_filtro_aplicado',
	(filtro) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/codae-solicitacoes/pendentes-autorizacao/${filtro}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao',
	(filtro, visao) => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/codae-solicitacoes/pendentes-autorizacao/${filtro}/${visao}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

export const rotasRelatoriosCodae = {
	filtrar: 'filtrar-solicitacoes-ga/',
	totalizadores: 'filtrar-solicitacoes-cards-totalizadores/',
	graficos: 'filtrar-solicitacoes-graficos/',
	pdf: 'exportar-pdf/',
	xlsx: 'exportar-xlsx/',
}

Cypress.Commands.add('consultar_relatorio_solicitacoes_codae', (operacao, dados, autenticado = true) => {
	if (!rotasRelatoriosCodae[operacao]) throw new Error(`Operacao CODAE desconhecida: ${operacao}`)
	return cy.request({
		method: 'POST',
		url: `${Cypress.config('baseUrl')}api/codae-solicitacoes/${rotasRelatoriosCodae[operacao]}`,
		body: dados,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		timeout: 120000,
		failOnStatusCode: false,
	})
})
