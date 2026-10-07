/// <reference types='cypress' />

Cypress.Commands.add('executar_feriados_ano', ({ proximo = false, method = 'GET', token = globalThis.token } = {}) => {
	return cy.request({ method,
		url: Cypress.config('baseUrl') + 'api/feriados-ano/' + (proximo ? 'ano-atual-e-proximo/' : ''),
		headers: token ? { Authorization: 'JWT ' + token } : {}, timeout: 60000, failOnStatusCode: false })
})
Cypress.Commands.add('consultar_feriados_ano', () => cy.executar_feriados_ano())
Cypress.Commands.add('consultar_feriados_ano_atual_e_proximo', () => cy.executar_feriados_ano({ proximo: true }))
