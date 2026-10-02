/// <reference types='cypress' />

Cypress.Commands.add('executar_escolas_para_filtros', ({ caminho = '', metodo = 'GET', qs = {}, token } = {}) => {
	const parametros = new URLSearchParams()
	Object.entries(qs).forEach(([chave, valor]) => {
		for (const item of Array.isArray(valor) ? valor : [valor]) parametros.append(chave, item)
	})
	return cy.request({
		method: metodo,
		url: `${Cypress.config('baseUrl')}api/escolas-para-filtros/${caminho ? `${caminho}/` : ''}${parametros.toString() ? `?${parametros}` : ''}`,
		headers: token ? { Authorization: `JWT ${token}` } : {},
		failOnStatusCode: false,
		timeout: 60000,
	})
})
