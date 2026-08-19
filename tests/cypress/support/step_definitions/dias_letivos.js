import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const parametros = { ano: 2025, mes: 11 }

function consultar(usuario, contexto) {
	cy.consultar_dias_letivos({
		...parametros,
		usuario,
		senha: Cypress.env('senha'),
	}).then((response) => {
		contexto.response = response
	})
}

When('consulto os dias letivos com um usuario CODAE', function () {
	consultar(Cypress.env('usuario_codae'), this)
})

When('consulto os dias letivos com um usuario diretor de UE', function () {
	consultar(Cypress.env('usuario_diretor_ue'), this)
})

Then('a consulta de dias letivos retorna status 200 e uma lista valida', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((dia) => {
		expect(dia).to.have.all.keys(
			'uuid', 'data', 'lotes', 'tipos_unidade_escolar', 'periodos_escolares',
			'unidades_escolares', 'editais_numeros',
		)
		expect(dia.uuid).to.be.a('string').and.not.be.empty
		expect(dia.data).to.match(/^\d{4}-\d{2}-\d{2}$/)
		expect(dia.lotes).to.be.an('array')
		expect(dia.tipos_unidade_escolar).to.be.an('array')
		expect(dia.periodos_escolares).to.be.an('array')
		expect(dia.unidades_escolares).to.be.a('string')
		expect(dia.editais_numeros).to.be.a('string')
	})
})

Then('a consulta de dias letivos retorna status 403 e mensagem de permissao', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
