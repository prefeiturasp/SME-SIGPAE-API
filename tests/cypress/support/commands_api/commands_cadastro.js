/// <reference types='cypress' />

Cypress.Commands.add(
	'atualizar_senha_cadastro',
	(usuario_uuid, token_reset, dados_teste) => {
		cy.request({
			method: 'POST',
			url:
				Cypress.config('baseUrl') +
				`api/cadastro/atualizar-senha/${usuario_uuid}/${token_reset}/`,
			timeout: 60000,
			body: dados_teste,
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('recuperar_senha_cadastro', (registroFuncionalOuCpf) => {
	return cy.request({
		method: 'GET',
		url: `${Cypress.config('baseUrl')}api/cadastro/recuperar-senha/${encodeURIComponent(registroFuncionalOuCpf)}/`,
		timeout: 60000,
		failOnStatusCode: false,
	})
})
