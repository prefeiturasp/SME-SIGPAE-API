import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar perfis vinculados', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de perfis vinculados', function () {
	cy.consultar_perfis_vinculados().then((response) => { this.response = response })
})
When('consulto perfis vinculados pelo perfil master {int}', function (perfil) {
	cy.consultar_perfis_vinculados_por_perfil_master(perfil).then((response) => {
		this.response = response
	})
})
When('consulto os subordinados de um perfil master existente', function () {
	cy.consultar_perfis_vinculados().then((lista) => {
		const vinculo = lista.body.results[0]
		this.subordinado = vinculo.perfis_subordinados[0].nome
		cy.consultar_perfis_subordinados_por_perfil_master(vinculo.perfil_master.nome)
			.then((response) => { this.response = response })
	})
})
When('consulto subordinados pelo perfil master {string}', function (perfil) {
	cy.consultar_perfis_subordinados_por_perfil_master(perfil).then((response) => {
		this.response = response
	})
})
function validarVinculo(vinculo) {
	expect(vinculo).to.include.all.keys('perfil_master', 'perfis_subordinados')
	expect(vinculo.perfil_master).to.include.all.keys('nome', 'visao', 'uuid')
	expect(vinculo.perfis_subordinados).to.be.an('array').and.not.be.empty
	expect(vinculo.perfis_subordinados[0]).to.include.all.keys('nome', 'visao', 'uuid')
}
Then('a lista de perfis vinculados retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarVinculo(this.response.body.results[0])
})
Then('a consulta por perfil master retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrada apresenta os perfis vinculados', function () {
	if (this.response.status === 200) validarVinculo(this.response.body)
})
Then('a API retorna o perfil subordinado esperado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.include(this.subordinado)
})
Then('a consulta de subordinados retorna status 400 e detalhe', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
