import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar a CODAE', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})

When('consulto a lista paginada da CODAE', function () {
	cy.consultar_codae().then((response) => {
		this.response = response
	})
})

Then('a consulta da CODAE deve retornar status 200 e registros validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.to.be.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.not.to.be.empty
	this.response.body.results.forEach((codae) => {
		expect(codae).to.include.all.keys(
			'id',
			'quantidade_alunos',
			'nome',
			'uuid',
			'acesso_modulo_medicao_inicial',
		)
		expect(codae.id).to.be.a('number')
		expect(codae.quantidade_alunos).to.be.a('number')
		expect(codae.nome).to.be.a('string').and.not.to.be.empty
		expect(codae.uuid).to.be.a('string').and.not.to.be.empty
		expect(codae.acesso_modulo_medicao_inicial).to.be.a('boolean')
	})
})
