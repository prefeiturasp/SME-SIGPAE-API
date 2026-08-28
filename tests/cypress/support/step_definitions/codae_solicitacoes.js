import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const consultas = {
	'pendentes autorizacao dieta': () => cy.consultar_pendentes_autorizacao_dieta(),
	'autorizados dieta': () => cy.consultar_autorizados_dieta(),
	'inativas dieta': () => cy.consultar_inativas_dieta(),
	'negados dieta': () => cy.consultar_negados_dieta(),
	'cancelados dieta': () => cy.consultar_cancelados_dieta(),
	'autorizadas temporariamente dieta': () =>
		cy.consultar_autorizadas_temporariamente_dieta(),
	autorizados: () => cy.consultar_autorizados(),
	cancelados: () => cy.consultar_cancelados(),
	negados: () => cy.consultar_negados(),
	'pendentes autorizacao': () => cy.consultar_pendentes_autorizacao(),
	questionamentos: () => cy.consultar_questionamentos(),
}

function validarPaginacao(response) {
	expect(response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(response.body.results).to.be.an('array')
}

Given('que estou autenticado como CODAE para consultar solicitacoes', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})

When('consulto solicitacoes da CODAE pelo agrupamento {string}', function (agrupamento) {
	expect(consultas).to.have.property(agrupamento)
	consultas[agrupamento]().then((response) => { this.response = response })
})

When('consulto dietas inativas temporariamente na CODAE', function () {
	cy.consultar_inativas_temporariamente_dieta().then((response) => { this.response = response })
})

When('consulto solicitacoes detalhadas da CODAE', function () {
	cy.consultar_solicitacoes_detalhadas().then((response) => { this.response = response })
})

When('consulto pendentes da CODAE com filtro {string}', function (filtro) {
	cy.consultar_pendentes_autorizacao_filtro_aplicado(filtro)
		.then((response) => { this.response = response })
})

When('consulto pendentes da CODAE com filtro {string} e visao {string}', function (filtro, visao) {
	cy.consultar_pendentes_autorizacao_filtro_aplicado_tipo_visao(filtro, visao)
		.then((response) => { this.response = response })
})

Then('a consulta agrupada da CODAE retorna dados ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		expect(this.response.body).to.have.property('detail')
		return
	}
	validarPaginacao(this.response)
})

Then('a consulta agrupada da CODAE retorna uma lista paginada com status 200', function () {
	expect(this.response.status).to.eq(200)
	validarPaginacao(this.response)
})

Then('a consulta detalhada da CODAE retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('data').that.is.an('array')
	expect(this.response.body).to.have.property('status')
})

Then('a consulta filtrada da CODAE retorna dados ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		expect(this.response.body).to.have.property('detail')
		return
	}
	expect(this.response.body).to.have.property('results').that.is.an('array')
})

Then('a consulta da CODAE retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})

Then('a consulta filtrada por visao da CODAE retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results')
})
