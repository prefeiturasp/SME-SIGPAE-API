import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado como CODAE para consultar feriados', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto os feriados por ano', function () {
	cy.consultar_feriados_ano().then((response) => {
		this.response = response
	})
})

When('consulto os feriados do ano atual e do proximo', function () {
	cy.consultar_feriados_ano_atual_e_proximo().then((response) => {
		this.response = response
	})
})

Then('a consulta de feriados deve retornar status 200 e uma lista', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results')
	expect(this.response.body.results).to.be.an('array')
})
