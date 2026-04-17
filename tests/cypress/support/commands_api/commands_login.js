/// <reference types='cypress' />

Cypress.Commands.add('autenticar_login', (usuario, senha) => {
	const login = usuario ?? Cypress.env('usuario_coordenador_logistica')
	const password = senha ?? Cypress.env('senha')

	if (!login || !password) {
		throw new Error(
			'Credenciais de login nao foram carregadas. Verifique o arquivo .env e use Cypress.env(...) para acessar usuario e senha.',
		)
	}

	return cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/login/',
		body: {
			login,
			password,
		},
	}).then((responseUserToken) => {
		globalThis.token = responseUserToken.body.access
		return responseUserToken
	})
})
