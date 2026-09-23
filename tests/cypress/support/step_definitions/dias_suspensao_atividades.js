import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const inexistente = '00000000-0000-0000-0000-000000000000'
const periodo = () => ({ mes: new Date().getMonth() + 1, ano: new Date().getFullYear() })

Given('que estou autenticado para dias de suspensao', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto os dias de suspensao cadastrados', function () {
	cy.executar_dias_suspensao().then((response) => { this.response = response })
})
When('consulto o detalhe de uma suspensao existente', function () {
	cy.executar_dias_suspensao().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.be.an('array').and.not.be.empty
		this.suspensao = response.body[0]
		cy.executar_dias_suspensao({ caminho: this.suspensao.uuid }).then((resposta) => { this.response = resposta })
	})
})
When('consulto lista de dias de suspensao para uma escola existente', function () {
	cy.request({ url: `${Cypress.config('baseUrl')}api/escolas-simplissima-com-eol/`, qs: { limit: 1 }, headers: { Authorization: `JWT ${globalThis.token}` } }).then((response) => {
		expect(response.body.results).to.be.an('array').and.not.be.empty
		cy.executar_dias_suspensao({ caminho: 'lista-dias', qs: { ...periodo(), escola: response.body.results[0].uuid } }).then((resposta) => { this.response = resposta })
	})
})
When('executo {string} em suspensao inexistente', function (metodo) {
	cy.executar_dias_suspensao({ metodo, caminho: inexistente, body: ['PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})
When('executo {string} na rota de suspensao {string} sem autenticacao', function (metodo, rota) {
	cy.clearCookies()
	cy.executar_dias_suspensao({ metodo, caminho: rota === 'detalhe' ? inexistente : rota === 'lista-dias' ? rota : '', autenticado: false, body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})
When('cadastro suspensao sem campos obrigatorios', function () {
	cy.executar_dias_suspensao({ metodo: 'POST', body: {} }).then((response) => { this.response = response })
})
When('consulto lista de dias de suspensao com {string}', function (condicao) {
	cy.executar_dias_suspensao({ caminho: 'lista-dias', qs: condicao === 'escola inexistente' ? { ...periodo(), escola: inexistente } : {} }).then((response) => { this.response = response })
})
Then('a operacao de suspensao retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('a listagem de suspensoes possui estrutura valida', function () {
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((dia) => {
		expect(dia).to.include.all.keys('uuid', 'data', 'tipo_unidade', 'edital', 'edital_numero', 'criado_por', 'criado_em')
		expect(dia.uuid).to.be.a('string').and.not.be.empty
	})
})
Then('o detalhe corresponde a suspensao consultada', function () {
	expect(this.response.body).to.deep.eq(this.suspensao)
})
Then('a lista de dias de suspensao apresenta datas e editais', function () {
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((dia) => {
		expect(dia.data).to.match(/^\d{2}\/\d{2}\/\d{4}$/)
		expect(dia.editais).to.be.an('array')
	})
})
Then('a suspensao informa campos obrigatorios', function () {
	for (const campo of ['data', 'cadastros_calendario']) expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
