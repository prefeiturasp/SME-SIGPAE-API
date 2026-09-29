/// <reference types='cypress' />

function requisitar(method, caminho = '', body, qs, autenticado = true) {
	return cy.request({
		method,
		url: `${Cypress.config('baseUrl')}api/ajuste-saldo-laudo/${caminho}`,
		body,
		qs,
		headers: autenticado ? { Authorization: `JWT ${globalThis.token}` } : {},
		timeout: 120000,
		failOnStatusCode: false,
	})
}

Cypress.Commands.add('consultar_ajuste_saldo_laudo', (query = {}, autenticado = true) =>
	requisitar('GET', '', undefined, query, autenticado))
Cypress.Commands.add('consultar_ajuste_saldo_laudo_por_uuid', (uuid, autenticado = true) =>
	requisitar('GET', `${uuid}/`, undefined, undefined, autenticado))
Cypress.Commands.add('cadastrar_ajuste_saldo_laudo', (dados, autenticado = true) =>
	requisitar('POST', '', dados, undefined, autenticado))
Cypress.Commands.add('atualizar_ajuste_saldo_laudo', (uuid, dados, autenticado = true) =>
	requisitar('PUT', `${uuid}/`, dados, undefined, autenticado))
Cypress.Commands.add('atualizar_ajuste_saldo_laudo_patch', (uuid, dados, autenticado = true) =>
	requisitar('PATCH', `${uuid}/`, dados, undefined, autenticado))
Cypress.Commands.add('excluir_ajuste_saldo_laudo', (uuid, autenticado = true) =>
	requisitar('DELETE', `${uuid}/`, undefined, undefined, autenticado))
Cypress.Commands.add('consultar_cronogramas_ajuste_saldo_laudo', (autenticado = true) =>
	requisitar('GET', 'cronogramas-mensal-com-documentos/', undefined, undefined, autenticado))
Cypress.Commands.add('consultar_documentos_ajuste_saldo_laudo', (query = {}, autenticado = true) =>
	requisitar('GET', 'documentos-do-cronograma/', undefined, query, autenticado))
