import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const escolaUuid = '3c32be8e-f191-468d-a4e2-3dd8751e5e7a'

const consultas = {
	'autorizadas temporariamente dieta': () =>
		cy.ue_consultar_autorizadas_temporariamente_dieta(escolaUuid),
	autorizados: () => cy.ue_consultar_autorizados(),
	'autorizados dieta': () => cy.ue_consultar_autorizados_dieta(escolaUuid),
	cancelados: () => cy.ue_consultar_cancelados(),
	'cancelados dieta': () => cy.ue_consultar_cancelados_dieta(escolaUuid),
	'inativas dieta': () => cy.ue_consultar_inativas_dieta(escolaUuid),
	'inativas temporariamente dieta': () =>
		cy.ue_consultar_inativas_temporariamente_dieta(escolaUuid),
	negados: () => cy.ue_consultar_negados(),
	'negados dieta': () => cy.ue_consultar_negados_dieta(escolaUuid),
	'pendentes autorizacao dieta': () =>
		cy.ue_consultar_pendentes_autorizacao_dieta(escolaUuid),
	'pendentes autorizacao': () => cy.ue_consultar_pendentes_autorizacao(),
	'aguardando vigencia dieta': () =>
		cy.ue_consultar_aguardando_vigencia_dieta(escolaUuid),
	'kit lanches autorizadas': () => cy.ue_consultar_kit_lanches_autorizadas(),
	'suspensoes autorizadas': () => cy.ue_consultar_suspensoes_autorizadas(),
}

Given('que estou autenticado como diretor de escola para consultar solicitacoes', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
})

When('consulto solicitacoes da escola pelo agrupamento {string}', function (agrupamento) {
	expect(consultas, `agrupamento ${agrupamento}`).to.have.property(agrupamento)
	consultas[agrupamento]().then((response) => {
		this.response = response
	})
})

When('consulto as solicitacoes detalhadas da escola', function () {
	cy.ue_consultar_solicitacoes_detalhadas().then((response) => {
		this.response = response
	})
})

Then('a consulta de solicitacoes da escola retorna uma lista paginada valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
})

Then('a consulta detalhada da escola retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('data').that.is.an('array')
	expect(this.response.body).to.have.property('status')
})

Then('a consulta de solicitacoes da escola retorna resultados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array')
})

function parametrosMensais() {
	const hoje = new Date()
	return { escola_uuid: escolaUuid, mes: hoje.getMonth() + 1, ano: hoje.getFullYear() }
}

function filtrosRelatorio() {
	const hoje = new Date()
	const data = `${String(hoje.getDate()).padStart(2, '0')}/${String(hoje.getMonth() + 1).padStart(2, '0')}/${hoje.getFullYear()}`
	return { status: 'AUTORIZADOS', de: data, ate: data, limit: 2, offset: 0 }
}

When('consulto a rota mensal da escola {string}', function (rota) {
	cy.executar_escola_solicitacoes({ rota, qs: parametrosMensais() }).then((response) => { this.response = response })
})

Then('a consulta de periodos da escola retorna uma lista valida', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((periodo) => expect(periodo).to.be.an('object'))
})

Then('a consulta da escola retorna a ultima data ou nenhum resultado', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.have.all.keys('ultima_data')
	if (this.response.body.ultima_data !== null) {
		expect(this.response.body.ultima_data).to.match(/^\d{4}-\d{2}-\d{2}$/)
		expect(Number.isNaN(Date.parse(this.response.body.ultima_data))).to.eq(false)
	}
})

When('envio os filtros de solicitacoes da escola para {string}', function (rota) {
	this.rotaRelatorioEscola = rota
	cy.executar_escola_solicitacoes({ rota, metodo: 'POST', body: filtrosRelatorio() }).then((response) => { this.response = response })
})

Then('o relatorio de solicitacoes da escola retorna dados validos', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	if (this.rotaRelatorioEscola === 'filtrar-solicitacoes-graficos') {
		expect(this.response.body).to.be.an('array')
	} else {
		expect(this.response.body.results).to.be.an('array')
		if (this.rotaRelatorioEscola === 'filtrar-solicitacoes-ga') {
			expect(this.response.body.count).to.be.a('number').and.at.least(0)
			expect(Number.isInteger(this.response.body.count)).to.eq(true)
			expect(this.response.body.results.length).to.be.at.most(2)
			expect(this.response.body.count).to.be.at.least(this.response.body.results.length)
		}
	}
})

Then('a exportacao de solicitacoes da escola confirma o recebimento', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body.detail).to.be.a('string')
	const detalhe = this.response.body.detail.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
	expect(detalhe).to.eq('Solicitacao de geracao de arquivo recebida com sucesso.')
})

When('executo {string} na rota de solicitacoes da escola {string} com acesso {string}', function (metodo, rota, acesso) {
	const autenticado = acesso === 'autenticado'
	if (!autenticado) cy.clearCookies()
	cy.executar_escola_solicitacoes({
		rota: rota.replace('{escola_uuid}', escolaUuid),
		metodo,
		qs: parametrosMensais(),
		body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? filtrosRelatorio() : undefined,
		autenticado,
	}).then((response) => { this.response = response })
})

Then('a operacao de solicitacoes da escola retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
	if ([401, 405].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
