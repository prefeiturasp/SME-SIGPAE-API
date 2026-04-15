/// <reference types='cypress' />

Cypress.Commands.add('autenticar_login', (usuario, senha) => {
	return cy
		.request({
			method: 'POST',
			url: `${Cypress.config('baseUrl')}api/login/`,
			body: {
				login: usuario,
				password: senha,
			},
		})
		.then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body).to.have.property('access')

			const token = response.body.access

			globalThis.token = token
			Cypress.env('apiToken', token)

			return response
		})
})
