export const rotasCronogramasSemanais = {
	'get /': [
		'GET',
		''
	],
	'post /': [
		'POST',
		''
	],
	'get {uuid}/': [
		'GET',
		'{uuid}/'
	],
	'put {uuid}/': [
		'PUT',
		'{uuid}/'
	],
	'patch {uuid}/': [
		'PATCH',
		'{uuid}/'
	],
	'patch {uuid}/alterar-cronograma/': [
		'PATCH',
		'{uuid}/alterar-cronograma/'
	],
	'patch {uuid}/assinar-e-enviar/': [
		'PATCH',
		'{uuid}/assinar-e-enviar/'
	],
	'patch {uuid}/fornecedor-ciente/': [
		'PATCH',
		'{uuid}/fornecedor-ciente/'
	],
	'get {uuid}/gerar-pdf-cronograma/': [
		'GET',
		'{uuid}/gerar-pdf-cronograma/'
	],
	'get calendario/': [
		'GET',
		'calendario/'
	],
	'get cronogramas-mensal-assinados/': [
		'GET',
		'cronogramas-mensal-assinados/'
	],
	'get gerar-relatorio-xlsx-async/': [
		'GET',
		'gerar-relatorio-xlsx-async/'
	],
	'get listagem-relatorio/': [
		'GET',
		'listagem-relatorio/'
	],
	'post rascunho/': [
		'POST',
		'rascunho/'
	],
	'get rascunhos/': [
		'GET',
		'rascunhos/'
	]
}

Cypress.Commands.add('requisitar_cronogramas_semanais', (operacao, opcoes = {}) => {
	const rota = rotasCronogramasSemanais[operacao]
	if (!rota) throw new Error('Operacao semanal desconhecida: ' + operacao)
	if (rota[1].includes('{uuid}') && !opcoes.uuid) throw new Error('Informe UUID semanal')
	return cy.request({ method: rota[0], url: Cypress.config('baseUrl') + 'api/cronogramas-semanais/' + rota[1].replace('{uuid}', opcoes.uuid), qs: opcoes.query, body: opcoes.dados, headers: opcoes.autenticado === false ? {} : { Authorization: 'JWT ' + globalThis.token }, encoding: rota[1].includes('gerar-pdf-cronograma') ? 'binary' : 'utf8', timeout: 120000, failOnStatusCode: false })
})
