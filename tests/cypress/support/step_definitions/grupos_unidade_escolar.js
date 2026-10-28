import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}
function consultar(contexto, opcoes = {}) {
	return cy.executar_grupos_unidade_escolar(opcoes).then((response) => { contexto.response = response })
}
function validarGrupo(grupo) {
	expect(grupo.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(grupo.nome).to.be.a('string').and.not.be.empty
	expect(grupo.tipos_unidades).to.be.an('array')
	grupo.tipos_unidades.forEach((tipo) => {
		expect(tipo).to.have.property('uuid').that.is.a('string')
		expect(tipo).to.have.property('iniciais').that.is.a('string')
	})
}
When('consulto a listagem de grupos de unidade escolar', function () {
	return autenticar().then(() => consultar(this, { qs: { limit: 2 } }))
})
Then('grupos de unidade escolar retorna uma lista paginada valida', function () {
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarGrupo)
})
When('consulto o detalhe de um grupo de unidade escolar existente', function () {
	return autenticar().then(() => cy.executar_grupos_unidade_escolar({ qs: { limit: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'grupo disponivel em QA').to.be.an('array').and.not.be.empty
		this.grupoReferencia = response.body.results[0]
		return consultar(this, { caminho: this.grupoReferencia.uuid + '/' })
	})
})
Then('o detalhe de unidade escolar corresponde ao grupo consultado', function () {
	validarGrupo(this.response.body)
	expect(this.response.body).to.deep.eq(this.grupoReferencia)
})
When('consulto grupos de unidade escolar por DRE {string}', function (dre) {
	return autenticar().then(() => {
		if (dre !== 'existente') return consultar(this, { caminho: 'por-dre/', qs: dre === 'ausente' ? {} : { dre: inexistente } })
		return cy.request({ url: Cypress.config('baseUrl') + 'api/diretorias-regionais/',
			qs: { limit: 1 }, headers: { Authorization: 'JWT ' + globalThis.token }, failOnStatusCode: false,
		}).then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results, 'DRE disponivel em QA').to.be.an('array').and.not.be.empty
			return consultar(this, { caminho: 'por-dre/', qs: { dre: response.body.results[0].uuid } })
		})
	})
})
Then('a consulta de grupos por DRE retorna habilitacao dos grupos', function () {
	expect(this.response.body.grupos).to.be.an('array')
	this.response.body.grupos.forEach((grupo) => {
		expect(grupo.nome).to.be.a('string').and.not.be.empty
		expect(grupo.habilitado).to.be.a('boolean')
	})
})
When('executo {string} em grupos de unidade escolar na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = { method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined }
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})
Then('grupos de unidade escolar retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([400, 401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
