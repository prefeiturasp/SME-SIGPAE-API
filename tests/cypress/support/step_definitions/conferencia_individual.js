import { When, Then } from 'cypress-cucumber-preprocessor/steps'
When('consulto a conferencia individual com usuario CODAE', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.consultar_conferencia_individual({ limit: 10, offset: 0 }).then((response) => {
		this.response = response
	})
})
Then('a consulta de conferencia individual retorna status 403 e detalhe', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
