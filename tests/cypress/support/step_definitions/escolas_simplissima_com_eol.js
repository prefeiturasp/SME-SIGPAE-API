import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function consultar(contexto, opcoes = {}) {
	return cy.executar_escola_simplissima_eol(opcoes).then((response) => { contexto.response = response })
}
function referencia(contexto) {
	return cy.consultar_escola_simplissima_eol().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		contexto.escola = response.body.results[0]
	})
}
function validarEscola(escola) {
	expect(escola).to.include.all.keys('uuid', 'codigo_eol', 'codigo_eol_escola', 'tipo_gestao')
	expect(escola.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(escola.codigo_eol).to.be.a('string')
	if (escola.codigo_eol_escola !== null) expect(escola.codigo_eol_escola).to.be.a('string')
	if (escola.tipo_gestao !== null) expect(escola.tipo_gestao).to.be.a('string')
}
Given('que estou autenticado como CODAE para consultar escolas simplissimas com EOL', () => {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto a lista de escolas simplissimas com EOL', function () {
	return consultar(this)
})
When('consulto uma escola simplissima com EOL existente', function () {
	return referencia(this).then(() => consultar(this, { uuid: this.escola.uuid }))
})
When('consulto a escola simplissima com EOL pelo UUID {string}', function (uuid) {
	return consultar(this, { uuid })
})
When('consulto escolas simplissimas com EOL com limite {int}', function (limit) {
	this.limite = limit
	return consultar(this, { qs: { limit } })
})
When('consulto escolas simplissimas com EOL com deslocamento', function () {
	return consultar(this, { qs: { limit: 2 } }).then(() => {
		expect(this.response.status).to.eq(200)
		expect(this.response.body.results).to.have.length(2)
		this.segundaEscola = this.response.body.results[1].uuid
		return consultar(this, { qs: { limit: 1, offset: 1 } })
	})
})
When('consulto escolas simplissimas com EOL depois do total', function () {
	return consultar(this, { qs: { limit: 1 } }).then(() => {
		expect(this.response.status).to.eq(200)
		return consultar(this, { qs: { limit: 1, offset: this.response.body.count } })
	})
})
When('consulto {string} de escolas simplissimas com EOL com autenticacao {string}', function (recurso, autenticacao) {
	return referencia(this).then(() => consultar(this, {
		uuid: recurso === 'detalhe' ? this.escola.uuid : undefined,
		token: autenticacao === 'ausente' ? null : 'token-invalido',
	}))
})
When('envio {string} para {string} de escolas simplissimas com EOL', function (method, recurso) {
	return referencia(this).then(() => consultar(this, { method, uuid: recurso === 'detalhe' ? this.escola.uuid : undefined }))
})
Then('a lista de escolas simplissimas com EOL retorna dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.be.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach(validarEscola)
})
Then('a escola simplissima com EOL retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('a escola simplissima com EOL corresponde a escola consultada', function () {
	expect(this.response.status).to.eq(200)
	validarEscola(this.response.body)
	expect(this.response.body.uuid).to.eq(this.escola.uuid)
	expect(this.response.body.codigo_eol).to.eq(this.escola.codigo_eol)
})
Then('a listagem de escolas simplissimas com EOL respeita o limite', function () {
	expect(this.response.body.results).to.have.length(Math.min(this.limite, this.response.body.count))
})
Then('a listagem de escolas simplissimas com EOL retorna a segunda escola', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.have.length(1)
	expect(this.response.body.results[0].uuid).to.eq(this.segundaEscola)
})
Then('a listagem de escolas simplissimas com EOL retorna vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.next).to.eq(null)
})
Then('a resposta de escolas simplissimas com EOL apresenta mensagem de erro', function () {
	expect(this.response.body).to.have.property('detail').that.is.a('string').and.not.be.empty
})

When('consulto a acao EOL {string} com filtro {string}', function (acao, filtro) {
	const uuid = '00000000-0000-0000-0000-000000000000'
	const body = filtro === 'nenhum' ? {} : { [filtro]: filtro === 'lote' ? uuid : [uuid] }
	return cy.executar_acao_escolas_eol({ acao, body }).then((response) => { this.response = response })
})
Then('a acao EOL retorna uma lista de escolas', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	this.response.body.slice(0, 10).forEach(validarEscola)
})
Then('a acao EOL informa ausencia de resultados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.deep.eq({ mensagem: 'N\u00e3o existem resultados para os filtros selecionados' })
})
Then('a acao EOL retorna uma lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.deep.eq([])
})
When('executo {string} na acao EOL {string} com acesso {string}', function (method, acao, acesso) {
	return cy.executar_acao_escolas_eol({ method, acao, token: acesso === 'ausente' ? null : acesso === 'invalido' ? 'token-invalido' : globalThis.token }).then((response) => { this.response = response })
})
