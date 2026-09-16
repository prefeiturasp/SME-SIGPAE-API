import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado para consultar classificacoes de dieta', () => {
	cy.autenticar_login(Cypress.env('usuario_classificacoes_dieta'), Cypress.env('senha'))
})
When('consulto todas as classificacoes de dieta', function () {
	cy.validar_solicitacoes_dieta('').then((response) => { this.response = response })
})
When('consulto a classificacao de dieta pelo caminho {string}', function (id) {
	cy.validar_solicitacoes_dieta(id).then((response) => { this.response = response })
})
Then('a API retorna as classificacoes de dieta esperadas', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.to.be.empty
	this.response.body.forEach((item) => {
		expect(item).to.include.all.keys('id', 'descricao', 'nome')
	})
	expect(this.response.body.map((item) => item.nome)).to.include.members(
		['Tipo A', 'Tipo A ENTERAL', 'Tipo B', 'Tipo C'],
	)
})
Then('a API retorna a classificacao de dieta de ID 1', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('id', 'descricao', 'nome')
	expect(this.response.body.id).to.eq(1)
})
Then('a consulta de classificacao de dieta retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
