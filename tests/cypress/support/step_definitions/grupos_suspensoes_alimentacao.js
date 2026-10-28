import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto grupos de suspensoes de alimentacao na rota {string} com perfil {string}', function (rota, perfil) {
	const usuarios = { codae: 'usuario_codae', dre: 'usuario_dre', escola: 'usuario_diretor_ue' }
	expect(usuarios).to.have.property(perfil)
	return cy.autenticar_login(Cypress.env(usuarios[perfil]), Cypress.env('senha')).then(() =>
		cy.executar_grupos_suspensoes_alimentacao({ caminho: rota === 'principal' ? '' : rota, qs: { limit: 2 } }),
	).then((response) => { this.response = response })
})
Then('a consulta de grupos de suspensoes de alimentacao retorna uma lista', function () {
	expect(this.response.status).to.eq(200)
	const lista = Array.isArray(this.response.body) ? this.response.body : this.response.body.results
	expect(lista).to.be.an('array')
	lista.slice(0, 2).forEach((grupo) => {
		expect(grupo).to.have.property('uuid').that.matches(/^[0-9a-f-]{36}$/i)
		expect(grupo).to.have.property('status').that.is.a('string')
	})
})
When('executo {string} em grupos de suspensoes de alimentacao na rota {string} com acesso {string}', function (method, rota, acesso) {
	const executar = (caminho) => cy.executar_grupos_suspensoes_alimentacao({
		method, caminho, token: acesso === 'ausente' ? null : 'token-invalido',
		body: method === 'GET' ? undefined : {},
	}).then((response) => { this.response = response })
	if (rota === 'existente/') {
		return cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha')).then(() =>
			cy.executar_grupos_suspensoes_alimentacao({ caminho: 'meus_rascunhos/', qs: { limit: 1 } }),
		).then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results, 'suspensao existente para validar autenticacao').to.be.an('array').and.not.be.empty
			return executar(response.body.results[0].uuid + '/')
		})
	}
	return executar(rota === 'principal' ? '' : rota)
})
Then('grupos de suspensoes de alimentacao retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401 || status === 403) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
When('consulto grupo de suspensao de alimentacao inexistente', function () {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(() =>
		cy.executar_grupos_suspensoes_alimentacao({ caminho: '00000000-0000-0000-0000-000000000000/' }),
	).then((response) => { this.response = response })
})

When('consulto um grupo de suspensao de alimentacao existente para {string}', function (operacao) {
	return cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha')).then(() =>
		cy.executar_grupos_suspensoes_alimentacao({ caminho: 'meus_rascunhos/', qs: { limit: 1 } }),
	).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'grupo disponivel na listagem').to.be.an('array').and.not.be.empty
		this.grupoReferencia = response.body.results[0]
		return cy.executar_grupos_suspensoes_alimentacao({ caminho: this.grupoReferencia.uuid + '/' + (operacao === 'PDF' ? 'relatorio/' : ''), encoding: operacao === 'PDF' ? 'binary' : 'utf8' })
	}).then((response) => { this.response = response })
})
Then('o detalhe da suspensao corresponde ao registro consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.grupoReferencia.uuid)
	expect(this.response.body).to.include.all.keys('escola', 'suspensoes_alimentacao', 'quantidades_por_periodo', 'status')
})
Then('o relatorio da suspensao retorna um PDF', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF')).to.eq(true)
})
