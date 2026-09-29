/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_contratos',
	({ limit = 10, offset = 0, usuario, senha } = {}) => {
		const request = {
			method: 'GET',
			url: Cypress.config('baseUrl') + 'api/contratos/',
			qs: {
				limit,
				offset,
			},
			timeout: 120000,
			failOnStatusCode: false,
		}

		if (usuario && senha) {
			request.auth = {
				username: usuario,
				password: senha,
			}
		}

		cy.request(request)
	},
)

Cypress.Commands.add('consultar_contrato_por_uuid', (uuid, usuario, senha) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/contratos/${uuid}/`,
		timeout: 120000,
		auth: {
			username: usuario,
			password: senha,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'encerrar_contrato_por_uuid',
	(uuid, dadosContrato, usuario, senha) => {
		cy.request({
			method: 'PATCH',
			url:
				Cypress.config('baseUrl') +
				`api/contratos/${uuid}/encerrar-contrato/`,
			timeout: 120000,
			auth: {
				username: usuario,
				password: senha,
			},
			body: dadosContrato,
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_listas_contratos', (operacao, query = {}, autenticado = true) => {
	const rotas = { pos_recebimento: 'lista-contratos-pos-recebimento', numeros: 'numeros-contratos-cadastrados' }
	if (!rotas[operacao]) throw new Error(`Consulta de contratos desconhecida: ${operacao}`)
	return cy.request({
		url: `${Cypress.config('baseUrl')}api/contratos/${rotas[operacao]}/`,
		method: 'GET', qs: query,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		timeout: 60000, failOnStatusCode: false,
	})
})
