import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado como CODAE para consultar escola simplissima sem paginacao', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto a escola simplissima sem paginacao pelo UUID {string}', function (uuid) {
	cy.consultar_escola_simplissima_dre_unpaginated_por_uuid(uuid).then((response) => {
		this.response = response
	})
})

Then('a consulta da escola simplissima sem paginacao retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})

Then('quando encontrada apresenta os dados esperados da escola', function () {
	if (this.response.status !== 200) return
	expect(this.response.body).to.include.all.keys(
		'uuid', 'nome', 'diretoria_regional', 'codigo_eol',
		'quantidade_alunos', 'lote_obj', 'tipo_unidade',
	)
	expect(this.response.body.diretoria_regional).to.be.an('object')
})
