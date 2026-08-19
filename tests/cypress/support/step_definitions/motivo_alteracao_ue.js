import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar motivos de alteracao da UE', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto os motivos de alteracao da UE', function () {
	cy.consultar_motivo_alteracao_ue().then((response) => {
		this.response = response
	})
})

Then('a consulta de motivos da UE deve retornar status 200 e dados paginados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.to.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('nome', 'uuid', 'descricao')
})
