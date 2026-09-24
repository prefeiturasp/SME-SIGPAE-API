import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'
const filtros = () => ({ escola_uuid: uuidInexistente, mes: 1, ano: new Date().getFullYear() })

Given('que estou autenticado para consultar dias do calendario', function () {
	cy.autenticar_login(Cypress.env('usuario_coordenador_logistica'), Cypress.env('senha'))
})

When('consulto dias do calendario de uma escola existente', function () {
	cy.request({
		url: `${Cypress.config('baseUrl')}api/escolas-simplissima-com-eol/`,
		qs: { limit: 1, offset: 0 },
		headers: { Authorization: `JWT ${globalThis.token}` },
	}).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.filtrosDias = { ...filtros(), escola_uuid: response.body.results[0].uuid }
		cy.executar_dias_calendario({ filtros: this.filtrosDias }).then((resposta) => { this.response = resposta })
	})
})

When('consulto dias do calendario de uma escola inexistente', function () {
	cy.executar_dias_calendario({ filtros: filtros() }).then((response) => { this.response = response })
})

When('executo {string} em dia do calendario inexistente', function (metodo) {
	cy.executar_dias_calendario({ metodo, id: 0, filtros: filtros(), body: ['PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})

When('executo {string} em dias do calendario na rota {string} sem autenticacao', function (metodo, rota) {
	cy.clearCookies()
	cy.executar_dias_calendario({ metodo, id: rota === 'detalhe' ? 0 : '', filtros: filtros(), autenticado: false, body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})

When('cadastro dia do calendario sem campos obrigatorios', function () {
	cy.executar_dias_calendario({ metodo: 'POST', body: {} }).then((response) => { this.response = response })
})

Then('a operacao de dias do calendario retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('a listagem de dias do calendario possui estrutura valida', function () {
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((dia) => {
		expect(dia).to.include.all.keys('escola', 'dia', 'data', 'dia_letivo', 'periodo_escolar')
		expect(dia.escola).to.be.a('string')
		expect(dia.dia_letivo).to.be.a('boolean')
	})
})

Then('a listagem de dias do calendario esta vazia', function () {
	expect(this.response.body).to.deep.eq([])
})

Then('dias do calendario informa os campos obrigatorios', function () {
	for (const campo of ['escola', 'data', 'periodo_escolar']) {
		expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
	}
})


