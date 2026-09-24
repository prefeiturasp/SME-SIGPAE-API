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

function filtrosRelatorioCodae() {
	// Periodo curto para limitar o volume consultado e exportado em QA.
	const hoje = new Date()
	const data = `${String(hoje.getDate()).padStart(2, '0')}/${String(hoje.getMonth() + 1).padStart(2, '0')}/${hoje.getFullYear()}`
	return { status: 'AUTORIZADOS', de: data, ate: data, limit: 2, offset: 0 }
}

When('consulto o relatorio CODAE pela operacao {string}', function (operacao) {
	this.operacaoRelatorio = operacao
	cy.consultar_relatorio_solicitacoes_codae(operacao, filtrosRelatorioCodae()).then((response) => {
		this.response = response
	})
})

Then('o relatorio CODAE retorna os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	if (this.operacaoRelatorio === 'graficos') {
		expect(this.response.body).to.be.an('array')
	} else {
		expect(this.response.body.results).to.be.an('array')
		if (this.operacaoRelatorio === 'filtrar') {
			expect(this.response.body.count).to.be.a('number').and.at.least(0)
			expect(this.response.body.results.length).to.be.at.most(2)
		}
	}
})

Then('a exportacao CODAE confirma o recebimento da solicitacao', function () {
	expect(this.response.status).to.eq(200)
	const detalhe = this.response.body.detail.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
	expect(detalhe).to.eq('Solicitacao de geracao de arquivo recebida com sucesso.')
})

When('consulto o relatorio CODAE pela operacao {string} sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.consultar_relatorio_solicitacoes_codae(operacao, filtrosRelatorioCodae(), false).then((response) => {
		this.response = response
	})
})

Then('o relatorio CODAE rejeita a consulta sem autenticacao', function () {
	expect(this.response.status).to.eq(401)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
