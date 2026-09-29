import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const inexistente = '00000000-0000-0000-0000-000000000000'
Given('que estou autenticado para cronogramas semanais', () => {
	cy.autenticar_login(Cypress.env('usuario_dilog_cronograma'), Cypress.env('senha'))
})
When('consulto cronogramas semanais pela operacao {string}', function (operacao) {
	const hoje = new Date()
	cy.requisitar_cronogramas_semanais(operacao, { query: { page_size: 2, mes: hoje.getMonth() + 1, ano: hoje.getFullYear() } }).then((response) => { this.response = response })
})
Then('a consulta semanal retorna lista com sucesso', function () {
	expect(this.response.status).to.eq(200)
	const lista = Array.isArray(this.response.body) ? this.response.body : this.response.body.results
	expect(lista).to.be.an('array')
	lista.forEach((item) => expect(item.uuid).to.be.a('string').and.not.be.empty)
})
When('consulto detalhe de cronograma semanal existente', function () {
	cy.requisitar_cronogramas_semanais('get /', { query: { page_size: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.uuid = response.body.results[0].uuid
		cy.requisitar_cronogramas_semanais('get {uuid}/', { uuid: this.uuid }).then((resposta) => { this.response = resposta })
	})
})
Then('o detalhe semanal corresponde ao UUID consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
When('acesso semanal inexistente usando {string}', function (operacao) {
	cy.requisitar_cronogramas_semanais(operacao, { uuid: inexistente }).then((response) => { this.response = response })
})
When('cadastro rascunho semanal com mensal {string}', function (tipo) {
	cy.requisitar_cronogramas_semanais('post rascunho/', { dados: tipo === 'ausente' ? {} : { cronograma_mensal: inexistente } }).then((response) => { this.response = response })
})
Then('o rascunho semanal informa erro no cronograma mensal', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.cronograma_mensal).to.be.an('array').and.not.be.empty
})
When('consulto calendario semanal com parametros {string}', function (tipo) {
	cy.requisitar_cronogramas_semanais('get calendario/', { query: tipo === 'ausentes' ? {} : { mes: 'abc', ano: 'xyz' } }).then((response) => { this.response = response })
})
When('acesso operacao semanal {string} sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.requisitar_cronogramas_semanais(operacao, { uuid: inexistente, autenticado: false }).then((response) => { this.response = response })
})
Then('a operacao semanal retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
