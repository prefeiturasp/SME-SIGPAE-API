import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado como DRE para consultar diretorias regionais', () => {
	cy.autenticar_login(Cypress.config('usuario_dre'), Cypress.config('senha'))
})

When('consulto uma diretoria regional com UUID valido', function () {
	cy.consultar_dre_por_uuid('8f1da4a7-11b6-4a09-9eaa-6633d066f26b').then((response) => {
		this.response = response
	})
})

When('consulto uma diretoria regional com UUID invalido', function () {
	cy.consultar_dre_por_uuid('3fa85f64-5717-4562-b3fc-2c963f66afa6').then((response) => {
		this.response = response
	})
})

Then('a diretoria regional deve retornar status 200 e os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.lotes).to.be.an('array')
	expect(this.response.body.escolas).to.be.an('array')
	expect(this.response.body).to.include.all.keys(
		'iniciais',
		'nome',
		'uuid',
		'codigo_eol',
		'acesso_modulo_medicao_inicial',
	)
})

Then('a diretoria regional deve retornar status 404', function () {
	expect(this.response.status).to.eq(404)
})
