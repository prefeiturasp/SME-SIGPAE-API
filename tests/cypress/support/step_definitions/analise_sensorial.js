import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function validarPaginacao(response) {
	expect(response.body).to.have.property('count')
	expect(response.body).to.have.property('next')
	expect(response.body).to.have.property('previous')
	expect(response.body).to.have.property('results').that.is.an('array')
}

function validarAnaliseSensorial(analiseSensorial) {
	expect(analiseSensorial).to.have.property('homologacao_produto')
	expect(analiseSensorial).to.have.property('data')
	expect(analiseSensorial).to.have.property('hora')
	expect(analiseSensorial).to.have.property('anexos').that.is.an('array')
	expect(analiseSensorial).to.have.property('responsavel_produto')
	expect(analiseSensorial).to.have.property('registro_funcional')
	expect(analiseSensorial).to.have.property('observacao')

	if (analiseSensorial.anexos.length > 0) {
		expect(analiseSensorial.anexos[0]).to.have.property('nome')
	}
}

function validarResposta(response) {
	expect(response.status).to.eq(200)
	validarPaginacao(response)

	if (response.body.results.length > 0) {
		validarAnaliseSensorial(response.body.results[0])
	}
}

Given('que estou autenticado para consultar analises sensoriais', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})

When('consulto todas as analises sensoriais', function () {
	cy.consultar_analise_sensorial().then((response) => {
		this.response = response
	})
})

When('consulto analises sensoriais com filtro {string}', function (filtro) {
	cy.consultar_analise_sensorial_com_filtros(filtro).then((response) => {
		this.response = response
	})
})

Then('deve retornar a lista paginada de analises sensoriais', function () {
	validarResposta(this.response)
})

Then(
	'deve retornar no maximo {int} analise sensorial paginada',
	function (limite) {
		validarResposta(this.response)
		expect(this.response.body.results.length).to.be.at.most(limite)
	},
)
