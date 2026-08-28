import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar perfis', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de perfis', function () {
	cy.consultar_perfis().then((response) => { this.response = response })
})
When('consulto um perfil existente por UUID', function () {
	cy.consultar_perfis().then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy.consultar_perfis_por_uuid(this.uuid).then((response) => { this.response = response })
	})
})
When('consulto um perfil por UUID invalido', function () {
	cy.consultar_perfis_por_uuid('3ac751ee-f95d-4d5b-80da-437506b00000')
		.then((response) => { this.response = response })
})
When('consulto as visoes dos perfis', function () {
	cy.consultar_perfis_visoes().then((response) => { this.response = response })
})
Then('a lista de perfis retorna status 200 e dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('nome', 'visao', 'uuid')
})
Then('o perfil retorna status 200 e os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('nome', 'visao', 'uuid')
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('o perfil retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('as visoes dos perfis retornam status 200 e uma lista valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	expect(this.response.body[0]).to.include.all.keys('id', 'nome')
})
