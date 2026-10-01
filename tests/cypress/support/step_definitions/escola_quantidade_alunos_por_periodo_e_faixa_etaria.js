import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

function dataReferencia() {
	const hoje = new Date()
	return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, '0')}-${String(hoje.getDate()).padStart(2, '0')}`
}

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.consultar_somatorio_faixas_etarias({
		uuid: uuidInexistente,
		data: dataReferencia(),
		token: globalThis.token,
		...opcoes,
	}).then((response) => { contexto.response = response })
}

When('consulto o somatorio de faixas etarias de uma escola existente', function () {
	autenticar()
	cy.consultar_escola_para_somatorio().then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		return consultar(this, { uuid: response.body.results[0].uuid })
	})
})

When('consulto o somatorio de faixas etarias com acesso {string}', function (acesso) {
	cy.clearCookies()
	return consultar(this, { token: acesso === 'token invalido' ? 'token-invalido' : undefined })
})

When('consulto o somatorio de faixas etarias para o UUID {string}', function (uuid) {
	autenticar()
	cy.then(() => consultar(this, { uuid }))
})

When('consulto o somatorio de faixas etarias com data {string}', function (data) {
	autenticar()
	cy.consultar_escola_para_somatorio().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		return consultar(this, { uuid: response.body.results[0].uuid, data })
	})
})

When('executo {string} na rota de somatorio de faixas etarias', function (metodo) {
	autenticar()
	cy.then(() => consultar(this, { metodo }))
})

Then('a operacao de somatorio de faixas etarias retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
})

Then('o somatorio de faixas etarias retorna quantidades validas', function () {
	const { count, results } = this.response.body
	expect(this.response.body).to.have.all.keys('count', 'results')
	expect(results).to.be.an('array')
	expect(count).to.eq(results.length)
	const uuids = results.map((item) => item.faixa_etaria.uuid)
	expect(new Set(uuids).size).to.eq(results.length)
	results.forEach((item) => {
		expect(item).to.have.all.keys('faixa_etaria', 'count')
		expect(item.count).to.be.a('number').and.at.least(0)
		expect(Number.isInteger(item.count)).to.eq(true)
		expect(item.faixa_etaria).to.include.all.keys('uuid', 'inicio', 'fim')
		expect(item.faixa_etaria.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
		expect(item.faixa_etaria.inicio).to.be.a('number').and.at.least(0)
		expect(item.faixa_etaria.fim).to.be.a('number').and.at.least(item.faixa_etaria.inicio)
	})
})

Then('o somatorio de faixas etarias informa erro de autenticacao', function () {
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('o somatorio de faixas etarias informa data invalida', function () {
	expect(this.response.body.data_referencia).to.be.an('array').and.not.be.empty
	expect(this.response.body).not.to.have.property('results')
})
