import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado para consultar classificacoes de dieta por ID', () => {
	cy.autenticar_login(
		Cypress.env('usuario_classificacoes_dieta'),
		Cypress.env('senha'),
	)
})

When('consulto a classificacao de dieta pelo ID {int}', function (id) {
	cy.consultar_classificacao_dieta_por_id(id).then((response) => {
		this.response = response
	})
})

Then('a classificacao retorna status 200, ID {int} e nome {string}', function (id, nome) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.id).to.eq(id)
	const nomeRecebido = this.response.body.nome
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
	expect(nomeRecebido).to.eq(nome)
	expect(this.response.body.descricao).to.be.a('string')
})

Then('a classificacao retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
