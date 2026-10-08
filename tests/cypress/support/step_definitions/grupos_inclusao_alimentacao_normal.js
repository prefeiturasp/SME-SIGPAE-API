import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto grupos de inclusao normal na rota {string} com perfil {string}', function (rota, perfil) {
	const usuarios = { codae: 'usuario_codae', dre: 'usuario_dre', escola: 'usuario_diretor_ue' }
	expect(usuarios).to.have.property(perfil)
	return cy.autenticar_login(Cypress.env(usuarios[perfil]), Cypress.env('senha')).then(() =>
		cy.executar_grupos_inclusao_alimentacao_normal({ caminho: rota === 'principal' ? '' : rota, qs: { limit: 2 } }),
	).then((response) => { this.response = response })
})
Then('a consulta de grupos de inclusao normal retorna uma lista', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array')
	this.response.body.results.slice(0, 2).forEach((grupo) => {
		expect(grupo).to.have.property('uuid').that.matches(/^[0-9a-f-]{36}$/i)
		expect(grupo).to.have.property('status').that.is.a('string')
	})
})
When('executo {string} em grupos de inclusao normal na rota {string} com acesso {string}', function (method, rota, acesso) {
	return cy.executar_grupos_inclusao_alimentacao_normal({ method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido', body: method === 'GET' ? undefined : {},
	}).then((response) => { this.response = response })
})
Then('grupos de inclusao normal retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401 || status === 403) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
When('consulto grupo de inclusao normal inexistente', function () {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(() =>
		cy.executar_grupos_inclusao_alimentacao_normal({ caminho: '00000000-0000-0000-0000-000000000000/' }),
	).then((response) => { this.response = response })
})

When('consulto um grupo de inclusao normal existente para {string}', function (operacao) {
	return cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha')).then(() =>
		cy.executar_grupos_inclusao_alimentacao_normal({ qs: { limit: 1 } }),
	).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'grupo disponivel na listagem').to.be.an('array').and.not.be.empty
		this.grupoReferencia = response.body.results[0]
		return cy.executar_grupos_inclusao_alimentacao_normal({ caminho: this.grupoReferencia.uuid + '/' + (operacao === 'PDF' ? 'relatorio/' : ''), encoding: operacao === 'PDF' ? 'binary' : 'utf8' })
	}).then((response) => { this.response = response })
})
Then('o detalhe do grupo corresponde ao registro consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.grupoReferencia.uuid)
	expect(this.response.body).to.include.all.keys('escola', 'inclusoes', 'quantidades_periodo', 'status')
})
Then('o relatorio do grupo retorna um PDF', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF')).to.eq(true)
})
