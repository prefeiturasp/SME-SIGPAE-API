import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar escolas simplissimas com EOL', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de escolas simplissimas com EOL', function () {
	cy.consultar_escola_simplissima_eol().then((response) => { this.response = response })
})
When('consulto a escola simplissima com EOL pelo UUID {string}', function (uuid) {
	cy.consultar_escola_simplissima_eol_por_uuid(uuid).then((response) => { this.response = response })
})
Then('a lista de escolas com EOL retorna status 200 e dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('codigo_eol', 'codigo_eol_escola', 'tipo_gestao', 'uuid')
})
Then('a escola simplissima com EOL retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrada apresenta os campos de EOL', function () {
	if (this.response.status !== 200) return
	expect(this.response.body).to.include.all.keys('uuid', 'codigo_eol', 'codigo_eol_escola', 'tipo_gestao')
})
