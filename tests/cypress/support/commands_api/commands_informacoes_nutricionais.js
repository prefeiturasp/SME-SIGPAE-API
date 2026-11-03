/// <reference types='cypress' />

Cypress.Commands.add('executar_informacoes_nutricionais', ({ method = 'GET', caminho = '', token = globalThis.token, qs } = {}) => {
	return cy.request({
		method, url: Cypress.config('baseUrl') + 'api/informacoes-nutricionais/' + caminho,
		qs, headers: token ? { Authorization: 'JWT ' + token } : {},
		failOnStatusCode: false, timeout: 60000, log: false,
	})
})

Cypress.Commands.add('consultar_informacoes_nutricionais', (uuid = '') => {
	return cy.executar_informacoes_nutricionais({ caminho: uuid ? uuid + '/' : '' })
})

Cypress.Commands.add('consultar_informacoes_nutricionais_agrupadas', () => {
	return cy.executar_informacoes_nutricionais({ caminho: 'agrupadas/' })
})

Cypress.Commands.add('consultar_informacoes_nutricionais_ordenadas', () => {
	return cy.executar_informacoes_nutricionais({ caminho: 'ordenadas/' })
})
