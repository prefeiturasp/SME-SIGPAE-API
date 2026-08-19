import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['tipo_nutricional', 'eh_dependente', 'nome', 'uuid', 'medida', 'eh_fixo']
Given('que estou autenticado como CODAE para consultar informacoes nutricionais', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de informacoes nutricionais', function () {
	cy.consultar_informacoes_nutricionais('').then((response) => { this.response = response })
})
When('consulto uma informacao nutricional existente por UUID', function () {
	cy.consultar_informacoes_nutricionais('').then((lista) => {
		cy.consultar_informacoes_nutricionais(lista.body.results[0].uuid)
			.then((response) => { this.response = response })
	})
})
When('consulto uma informacao nutricional por UUID invalido', function () {
	cy.consultar_informacoes_nutricionais('3ac751ee-f95d-4d5b-80da-437506b1906j')
		.then((response) => { this.response = response })
})
When('consulto as informacoes nutricionais agrupadas', function () {
	cy.consultar_informacoes_nutricionais_agrupadas().then((response) => {
		this.response = response
	})
})
When('consulto as informacoes nutricionais ordenadas', function () {
	cy.consultar_informacoes_nutricionais_ordenadas().then((response) => {
		this.response = response
	})
})
function validarInformacao(item) {
	expect(item).to.include.all.keys(...campos)
	expect(item.tipo_nutricional).to.include.all.keys('nome', 'uuid')
}
Then('a lista de informacoes nutricionais retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarInformacao(this.response.body.results[0])
})
Then('a informacao nutricional retorna os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	validarInformacao(this.response.body)
})
Then('a informacao nutricional retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('as informacoes agrupadas retornam dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	const grupo = this.response.body.results[0]
	expect(grupo).to.include.all.keys('nome', 'informacoes_nutricionais')
	expect(grupo.informacoes_nutricionais[0]).to.include.all.keys('nome', 'uuid', 'medida')
})
Then('as informacoes ordenadas retornam dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarInformacao(this.response.body.results[0])
})
