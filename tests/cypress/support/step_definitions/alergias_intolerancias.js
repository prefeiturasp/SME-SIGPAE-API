import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado para consultar alergias e intolerancias', () => {
	const usuario = Cypress.config('usuario_coordenador_logistica')
	const senha = Cypress.config('senha')

	cy.autenticar_login(usuario, senha)
})

When('consulto todas as alergias e intolerancias', function () {
	cy.validar_alergias_intolerancias('').then((response) => {
		this.response = response
	})
})

When('consulto a alergia ou intolerancia de id 127', function () {
	cy.validar_alergias_intolerancias('127/').then((response) => {
		this.response = response
	})
})

When(
	'consulto alergias e intolerancias pelo caminho {string}',
	function (caminho) {
		cy.validar_alergias_intolerancias(caminho).then((response) => {
			this.response = response
		})
	},
)

Then(
	'a consulta de alergias e intolerancias deve retornar status 200',
	function () {
		expect(this.response.status).to.eq(200)
	},
)

Then('deve retornar a alergia ARGININEMIA com id 127 na lista', function () {
	expect(this.response.body).to.be.an('array').and.not.to.be.empty
	expect(this.response.body[0]).to.have.property('descricao').that.is.a('string')
	expect(this.response.body[0].descricao).to.include('ARGININEMIA')
	expect(this.response.body[0]).to.have.property('id').that.equals(127)
})

Then('deve retornar a alergia ARGININEMIA com id 127', function () {
	expect(this.response.body).to.have.property('descricao').that.is.a('string')
	expect(this.response.body).to.have.property('id').that.is.a('number')
	expect(this.response.body.descricao).to.eq('ARGININEMIA')
	expect(this.response.body.id).to.eq(127)
})

Then(
	'a API deve redirecionar a consulta para o caminho com barra final',
	function () {
		expect(this.response.allRequestResponses[0]['Response Status']).to.eq(301)
		expect(this.response.status).to.eq(200)
		expect(this.response.body).to.exist
		expect(this.response.redirects[0]).to.contain('301:')
		expect(this.response.allRequestResponses).to.be.an('array').that.is.not.empty
		expect(this.response.redirects).to.be.an('array').that.is.not.empty
	},
)
