import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['uuid', 'nome', 'codigo_eol', 'iniciais', 'acesso_modulo_medicao_inicial']
Given('que estou autenticado como DRE para consultar diretorias simplissimas', () => {
	cy.autenticar_login(Cypress.config('usuario_dre'), Cypress.config('senha'))
})
When('consulto a lista paginada de diretorias simplissimas', function () {
	cy.consultar_dre_simplissima().then((response) => { this.response = response })
})
When('consulto a diretoria simplissima pelo UUID {string}', function (uuid) {
	cy.consultar_dre_simplissima_por_uuid(uuid).then((response) => { this.response = response })
})
When('consulto a lista completa de diretorias simplissimas', function () {
	cy.consultar_lista_completa_dre_simplissima().then((response) => { this.response = response })
})
Then('a lista de diretorias simplissimas retorna status 200 e dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys(...campos)
})
Then('a consulta da diretoria simplissima retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrada apresenta os campos esperados da diretoria', function () {
	if (this.response.status === 200) expect(this.response.body).to.include.all.keys(...campos)
})
Then('a lista completa de diretorias simplissimas retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'iniciais', 'nome', 'codigo_eol')
})
