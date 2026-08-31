import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('solicito um token para o perfil {string}', function (perfil) {
	const usuario = Cypress.env(`usuario_${perfil}`)
	expect(usuario, `Usuario nao configurado para o perfil ${perfil}`).to.exist

	cy.autenticar_api_token_auth(usuario, Cypress.env('senha')).then((response) => {
		this.response = response
	})
})

When('solicito um token com credenciais invalidas', function () {
	cy.autenticar_api_token_auth('usuario_invalido', 'senha_invalida').then(
		(response) => {
			this.response = response
		},
	)
})

Then('deve retornar os tokens de acesso e renovacao', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('refresh').that.is.not.empty
	expect(this.response.body).to.have.property('access').that.is.not.empty
})

Then('a API Token Auth deve retornar status 401', function () {
	expect(this.response.status).to.eq(401)
	expect(this.response.body).to.have.property('detail').that.is.not.empty
})
