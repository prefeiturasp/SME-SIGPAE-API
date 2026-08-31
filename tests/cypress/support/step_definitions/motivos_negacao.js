import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar motivos de negacao', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto todos os motivos de negacao', function () {
	cy.consultar_motivos_negacao().then((response) => { this.response = response })
})
When('consulto motivos de negacao pelo processo {string}', function (processo) {
	this.processo = processo
	cy.consultar_motivos_negacao_por_processo(`?processo=${processo}`)
		.then((response) => { this.response = response })
})
When('consulto um motivo de negacao existente por ID', function () {
	cy.consultar_motivos_negacao().then((lista) => {
		this.id = lista.body[0].id
		cy.consultar_motivos_negacao_por_id(this.id).then((response) => {
			this.response = response
		})
	})
})
When('consulto um motivo de negacao pelo ID invalido', function () {
	cy.consultar_motivos_negacao_por_id('3ac751e').then((response) => {
		this.response = response
	})
})
Then('a API retorna uma lista valida de motivos de negacao', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	expect(this.response.body[0]).to.include.all.keys('id', 'descricao', 'processo')
})
Then('a API retorna motivos do processo {string}', function (processo) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	expect(this.response.body[0]).to.include.all.keys('id', 'descricao', 'processo')
	expect(this.response.body[0].processo).to.eq(processo)
})
Then('a API retorna status 400 e erro no processo', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.processo).to.be.an('array').and.not.be.empty
})
Then('a API retorna o motivo de negacao consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('id', 'descricao', 'processo')
	expect(this.response.body.id).to.eq(this.id)
})
Then('a consulta do motivo de negacao retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
