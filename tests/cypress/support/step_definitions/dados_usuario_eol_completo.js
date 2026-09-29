import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado para consultar dados completos do usuario EOL', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})

When('consulto dados completos do usuario EOL com RF inexistente', function () {
	cy.consultar_dados_usuario_eol_completo('0000000', globalThis.token).then((response) => {
		this.response = response
	})
})

When('consulto dados completos do usuario EOL sem autenticacao', function () {
	cy.clearCookies()
	cy.consultar_dados_usuario_eol_completo('0000000').then((response) => {
		this.response = response
	})
})

When('consulto dados completos do usuario EOL com token invalido', function () {
	cy.clearCookies()
	cy.consultar_dados_usuario_eol_completo('0000000', 'token-invalido').then((response) => {
		this.response = response
	})
})

Then('a consulta completa do usuario EOL retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('a consulta completa do usuario EOL informa usuario nao encontrado', function () {
	expect(this.response.body.detail).to.eq('Usuário não encontrado')
})
