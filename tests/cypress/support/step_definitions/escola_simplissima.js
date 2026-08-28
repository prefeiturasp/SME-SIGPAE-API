import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuidDre = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
Given('que estou autenticado como CODAE para consultar escolas simplissimas', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto a lista de escolas simplissimas', function () {
	cy.consultar_escola_simplissima().then((response) => { this.response = response })
})
When('consulto escolas simplissimas pelo UUID da DRE', function () {
	cy.consultar_escola_simplissima_por_uuid(uuidDre).then((response) => { this.response = response })
})
When('filtro escolas simplissimas pela DRE', function () {
	cy.consultar_escola_simplissima_por_dre(uuidDre).then((response) => { this.response = response })
})
Then('a lista de escolas simplissimas retorna dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol')
})
Then('a consulta por UUID retorna escolas simplissimas validas', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol')
})
Then('a consulta filtrada retorna escolas vinculadas a DRE', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol', 'diretoria_regional')
	expect(this.response.body[0].diretoria_regional.uuid).to.eq(uuidDre)
})
