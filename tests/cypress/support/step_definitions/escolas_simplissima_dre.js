import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function consultar(contexto, opcoes = {}) {
	return cy.executar_escola_simplissima_dre(opcoes).then((response) => { contexto.response = response })
}
function referencia(contexto) {
	return cy.consultar_escola_simplissima_dre().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		contexto.escola = response.body.results[0]
	})
}
function validarEscola(escola) {
	expect(escola).to.include.all.keys('uuid', 'nome', 'codigo_eol', 'diretoria_regional', 'quantidade_alunos')
	expect(escola.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(escola.nome).to.be.a('string')
	expect(escola.codigo_eol).to.be.a('string')
	expect(escola.quantidade_alunos).to.be.a('number').and.be.at.least(0)
	if (escola.diretoria_regional !== null) {
		expect(escola.diretoria_regional).to.include.all.keys('uuid', 'nome', 'codigo_eol')
	}
}
Given('que estou autenticado como CODAE para consultar escolas simplissimas com DRE', () => {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
When('consulto a lista de escolas simplissimas com DRE', function () {
	return consultar(this)
})
When('consulto uma escola simplissima com DRE existente', function () {
	return referencia(this).then(() => consultar(this, { uuid: this.escola.uuid }))
})
When('consulto a escola simplissima com DRE pelo UUID {string}', function (uuid) {
	return consultar(this, { uuid })
})
When('consulto escolas simplissimas com DRE com limite {int}', function (limit) {
	this.limite = limit
	return consultar(this, { qs: { limit } })
})
When('consulto escolas simplissimas com DRE com deslocamento', function () {
	return consultar(this, { qs: { limit: 2 } }).then(() => {
		expect(this.response.status).to.eq(200)
		expect(this.response.body.results).to.have.length(2)
		this.segundaEscola = this.response.body.results[1].uuid
		return consultar(this, { qs: { limit: 1, offset: 1 } })
	})
})
When('consulto escolas simplissimas com DRE depois do total', function () {
	return consultar(this, { qs: { limit: 1 } }).then(() => {
		expect(this.response.status).to.eq(200)
		return consultar(this, { qs: { limit: 1, offset: this.response.body.count } })
	})
})
When('consulto {string} de escolas simplissimas com DRE com autenticacao {string}', function (recurso, autenticacao) {
	return referencia(this).then(() => consultar(this, {
		uuid: recurso === 'detalhe' ? this.escola.uuid : undefined,
		token: autenticacao === 'ausente' ? null : 'token-invalido',
	}))
})
When('envio {string} para {string} de escolas simplissimas com DRE', function (method, recurso) {
	return referencia(this).then(() => consultar(this, { method, uuid: recurso === 'detalhe' ? this.escola.uuid : undefined }))
})
Then('a lista de escolas simplissimas com DRE retorna dados paginados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.be.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach(validarEscola)
})
Then('a escola simplissima com DRE retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('a escola simplissima com DRE corresponde a escola consultada', function () {
	expect(this.response.status).to.eq(200)
	validarEscola(this.response.body)
	expect(this.response.body.uuid).to.eq(this.escola.uuid)
	expect(this.response.body.diretoria_regional).to.deep.eq(this.escola.diretoria_regional)
})
Then('a listagem de escolas simplissimas com DRE respeita o limite', function () {
	expect(this.response.body.results).to.have.length(Math.min(this.limite, this.response.body.count))
})
Then('a listagem de escolas simplissimas com DRE retorna a segunda escola', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.have.length(1)
	expect(this.response.body.results[0].uuid).to.eq(this.segundaEscola)
})
Then('a listagem de escolas simplissimas com DRE retorna vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.next).to.eq(null)
})
Then('a resposta de escolas simplissimas com DRE apresenta mensagem de erro', function () {
	expect(this.response.body).to.have.property('detail').that.is.a('string').and.not.be.empty
})
