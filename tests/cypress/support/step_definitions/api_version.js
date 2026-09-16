import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto a versao da API', function () {
	cy.consultar_api_version().then((response) => {
		this.response = response
	})
})

Then('a API deve retornar status 200', function () {
	expect(this.response.status).to.eq(200)
})

Then('deve informar a versao atual da API', function () {
	expect(this.response.body).to.have.property('API_Version').that.is.not.empty
})
