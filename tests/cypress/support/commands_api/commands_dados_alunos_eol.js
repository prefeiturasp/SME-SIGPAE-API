/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_dados_aluno_eol',
	(codigoEol, usuario, senha) => {
		cy.request({
			method: 'GET',
			url: Cypress.config('baseUrl') + `api/dados-alunos-eol/${codigoEol}/`,
			timeout: 120000,
			auth: {
				username: usuario,
				password: senha,
			},
			failOnStatusCode: false,
		})
	},
)
