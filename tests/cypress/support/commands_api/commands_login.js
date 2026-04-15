/// <reference types='cypress' />

Cypress.Commands.add('autenticar_login', (usuario, senha) => {
	const loginUrl = `${Cypress.config('baseUrl')}api/login/`
	const usuarioResolvido = usuario ?? Cypress.env('usuario_coordenador_logistica')
	const senhaResolvida = senha ?? Cypress.env('senha')

	cy.log(`Autenticando em: ${loginUrl}`)

	if (!usuarioResolvido || !senhaResolvida) {
		throw new Error(
			'Credenciais de login nao foram carregadas. Verifique as variaveis de ambiente do Cypress, como COORDENADOR_LOGISTICA e SENHA.',
		)
	}

	return cy.request({
		method: 'POST',
		url: loginUrl,
		body: {
			login: usuarioResolvido,
			password: senhaResolvida,
		},
	}).then((responseUserToken) => {
		globalThis.token =
			responseUserToken.allRequestResponses[0]['Response Body'].access

		return responseUserToken
	})
})
