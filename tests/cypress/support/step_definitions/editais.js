import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['uuid', 'numero', 'tipo_contratacao', 'processo', 'objeto', 'eh_imr']
Given('que estou autenticado como DRE para consultar editais', () => {
	cy.autenticar_login(Cypress.config('usuario_dre'), Cypress.config('senha'))
})
When('consulto a lista de editais', function () {
	cy.consultar_editais().then((response) => { this.response = response })
})
When('consulto um edital pelo UUID {string}', function (uuid) {
	cy.consultar_editais_por_uuid(uuid).then((response) => { this.response = response })
})
When('consulto a lista de numeros de editais', function () {
	cy.consultar_lista_numeros_editais().then((response) => { this.response = response })
})
Then('a lista de editais retorna status 200 e os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys(...campos)
})
Then('a consulta do edital retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrado apresenta os campos esperados do edital', function () {
	if (this.response.status === 200) expect(this.response.body).to.include.all.keys(...campos)
})
Then('a lista de numeros de editais retorna status 200 e dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'numero')
})
