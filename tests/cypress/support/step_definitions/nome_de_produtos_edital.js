import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar nomes de produtos', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto os nomes de produtos do edital', function () {
	cy.consultar_nome_de_produtos_edital().then((response) => {
		this.response = response
	})
})

Then('a consulta de nomes de produtos deve retornar status 200 e uma lista valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results')
	expect(this.response.body.results).to.be.an('array').and.not.to.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('nome', 'uuid')
})
