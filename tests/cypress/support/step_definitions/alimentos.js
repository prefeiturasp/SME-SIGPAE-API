import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function validarEstruturaDoAlimento(alimento) {
	expect(alimento.ativo, 'O alimento deve estar ativo').to.be.true
	expect(alimento).to.have.property('id').that.is.a('number')
	expect(alimento).to.have.property('nome').that.is.a('string')
	expect(alimento).to.have.property('outras_informacoes').that.is.a('string')
	expect(alimento)
		.to.have.property('tipo_listagem_protocolo')
		.that.equals('SO_ALIMENTOS')
	expect(alimento)
		.to.have.property('uuid')
		.that.is.a('string')
		.and.have.length.greaterThan(0)
}

Given('que estou autenticado para consultar alimentos', () => {
	cy.autenticar_login(
		Cypress.config('usuario_coordenador_logistica'),
		Cypress.config('senha'),
	)
})

When('consulto os alimentos do tipo {string}', function (tipo) {
	cy.validar_alimentos(`?tipo=${tipo}`).then((response) => {
		this.response = response
	})
})

When('consulto todos os alimentos', function () {
	cy.validar_alimentos('').then((response) => {
		this.response = response
	})
})

When('consulto o alimento de id 489', function () {
	cy.validar_alimentos('489/').then((response) => {
		this.response = response
	})
})

When('consulto o alimento pelo caminho {string}', function (caminho) {
	cy.validar_alimentos(caminho).then((response) => {
		this.response = response
	})
})

Then('a consulta de alimentos deve retornar status 200', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.to.be.empty
})

Then('o primeiro alimento deve ser {string}', function (nome) {
	const primeiroAlimento = this.response.body[0]
	validarEstruturaDoAlimento(primeiroAlimento)
	expect(primeiroAlimento.nome).to.eq(nome)
})

Then('a consulta deve rejeitar o tipo de alimento invalido', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property('tipo').that.is.an('array')
	const mensagem = this.response.body.tipo[0]
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
	expect(mensagem).to.eq(
		'Faca uma escolha valida. batata nao e uma das escolhas disponiveis.',
	)
})

Then('deve retornar os dados completos do alimento ABACATE', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.all.keys(
		'ativo',
		'id',
		'marca',
		'nome',
		'outras_informacoes',
		'tipo',
		'tipo_listagem_protocolo',
		'uuid',
	)
	expect(this.response.body.ativo).to.eq(true)
	expect(this.response.body.id).to.eq(489)
	expect(this.response.body.marca).to.be.null
	expect(this.response.body.nome).to.eq('ABACATE')
	expect(this.response.body.outras_informacoes).to.eq('')
	expect(this.response.body.tipo).to.eq('E')
	expect(this.response.body.tipo_listagem_protocolo).to.eq('SO_ALIMENTOS')
	expect(this.response.body.uuid).to.eq(
		'b48dc997-2cbd-4c10-9766-711f41637922',
	)
})

Then(
	'a API de alimentos deve redirecionar para o caminho com barra final',
	function () {
		expect(this.response.allRequestResponses[0]['Response Status']).to.eq(301)
		expect(this.response.status).to.eq(200)
		expect(this.response.body).to.exist
		expect(this.response.redirects[0]).to.contain('301:')
		expect(this.response.allRequestResponses).to.be.an('array').that.is.not.empty
		expect(this.response.redirects).to.be.an('array').that.is.not.empty
	},
)
