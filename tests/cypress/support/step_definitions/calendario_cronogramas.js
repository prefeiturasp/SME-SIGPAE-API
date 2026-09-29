import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado para consultar o calendario de cronogramas', () => {
	const usuario = Cypress.env('usuario_dilog_cronograma')
	expect(usuario, 'Credencial DILOG_CRONOGRAMA').to.be.a('string').and.not.be.empty
	cy.autenticar_login(usuario, Cypress.env('senha'))
})

Given('que estou autenticado como escola para consultar calendario', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
})

When('consulto o calendario de cronogramas com parametros {string}', function (parametros) {
	cy.validar_calendario_cronogramas(parametros).then((response) => {
		this.response = response
	})
})

When('consulto o calendario de cronogramas do mes atual', function () {
	const hoje = new Date()
	cy.validar_calendario_cronogramas(`?mes=${hoje.getMonth() + 1}&ano=${hoje.getFullYear()}&limit=2&offset=0`).then((response) => {
		this.response = response
	})
})

When('consulto a etapa de calendario com ID inexistente', function () {
	cy.validar_calendario_cronogramas('?mes=3&ano=2025', { id: 0 }).then((response) => {
		this.response = response
	})
})

When('consulto a etapa de calendario sem parametros', function () {
	cy.validar_calendario_cronogramas('', { id: 0 }).then((response) => {
		this.response = response
	})
})

When('consulto {string} do calendario sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.validar_calendario_cronogramas('?mes=3&ano=2025', {
		id: operacao === 'detalhe' ? 0 : undefined,
		autenticado: false,
	}).then((response) => {
		this.response = response
	})
})

Then('o calendario retorna uma lista paginada com limite de dois itens', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach((etapa) => {
		for (const campo of ['uuid', 'uuid_cronograma', 'nome_produto', 'data_programada', 'status']) {
			expect(etapa).to.have.property(campo).that.is.a('string')
		}
	})
})

Then('o calendario retorna erro de validacao contendo {string}', function (trecho) {
	expect(this.response.status).to.eq(400)
	const mensagem = JSON.stringify(this.response.body).normalize('NFD').replace(/[\u0300-\u036f]/g, '')
	expect(mensagem).to.contain(trecho)
})

Then('o calendario de cronogramas retorna status {int} e detalhe', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
