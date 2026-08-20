import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
Given('que estou autenticado como CODAE para consultar escolas simplissimas com DRE', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de escolas simplissimas com DRE', function () {
	cy.consultar_escola_simplissima_dre().then((response) => { this.response = response })
})
When('consulto a escola simplissima com DRE pelo UUID {string}', function (uuid) {
	cy.consultar_escola_simplissima_dre_por_uuid(uuid).then((response) => { this.response = response })
})
Then('a lista de escolas simplissimas com DRE retorna dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol')
})
Then('a escola simplissima com DRE retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrada apresenta os dados completos da escola com DRE', function () {
	if (this.response.status !== 200) return
	expect(this.response.body).to.include.all.keys(
		'uuid', 'nome', 'diretoria_regional', 'codigo_eol',
		'quantidade_alunos', 'lote_obj', 'tipo_unidade',
	)
	expect(this.response.body.diretoria_regional).to.be.an('object')
})
