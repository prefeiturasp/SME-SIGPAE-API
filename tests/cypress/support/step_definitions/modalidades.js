import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar modalidades', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de modalidades', function () {
	cy.consultar_modalidades().then((response) => { this.response = response })
})
When('consulto uma modalidade existente por UUID', function () {
	cy.consultar_modalidades().then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy.consultar_modalidades_por_uuid(this.uuid).then((response) => { this.response = response })
	})
})
When('consulto uma modalidade por UUID invalido', function () {
	cy.consultar_modalidades_por_uuid('3ac751ee-f95d-4d5b-80da-437506b00000')
		.then((response) => { this.response = response })
})
Then('a lista de modalidades retorna status 200 e dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('nome', 'uuid')
})
Then('a modalidade retorna status 200 e o UUID consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('nome')
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('a modalidade retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
