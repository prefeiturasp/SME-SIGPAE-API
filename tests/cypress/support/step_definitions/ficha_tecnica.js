import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_dilog_qualidade'), Cypress.env('senha'))
}
When('consulto ficha tecnica na listagem {string}', function (rota) {
	return autenticar().then(() => cy.executar_ficha_tecnica({ caminho: rota === 'principal' ? '' : rota + '/', qs: { page_size: 2 } })).then((response) => { this.response = response })
})
Then('a listagem de fichas tecnicas retorna resultados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array')
})
When('consulto ficha tecnica com filtro {string} igual a {string}', function (campo, valor) {
	return autenticar().then(() => cy.executar_ficha_tecnica({ qs: { [campo]: valor } })).then((response) => { this.response = response })
})
Then('a ficha tecnica retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('a lista de fichas tecnicas esta vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
})
When('consulto ficha tecnica com tamanho de pagina {int}', function (page_size) {
	this.tamanho = page_size
	return autenticar().then(() => cy.executar_ficha_tecnica({ qs: { page_size } })).then((response) => { this.response = response })
})
Then('a ficha tecnica respeita o tamanho da pagina', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.have.length(Math.min(this.tamanho, this.response.body.count))
})
When('consulto detalhe de ficha tecnica existente', function () {
	return autenticar().then(() => cy.executar_ficha_tecnica({ qs: { page_size: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.uuid = response.body.results[0].uuid
		return cy.executar_ficha_tecnica({ caminho: this.uuid + '/' })
	}).then((response) => { this.response = response })
})
Then('o detalhe corresponde a ficha tecnica consultada', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
When('consulto ficha tecnica inexistente na acao {string}', function (acao) {
	const caminho = '00000000-0000-0000-0000-000000000000/' + (acao === 'detalhe' ? '' : acao + '/')
	return autenticar().then(() => cy.executar_ficha_tecnica({ caminho })).then((response) => { this.response = response })
})
When('executo {string} na rota de ficha tecnica {string} com acesso {string}', function (method, rota, acesso) {
	return cy.executar_ficha_tecnica({ method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido',
		body: method === 'GET' ? undefined : {},
	}).then((response) => { this.response = response })
})
When('envio DELETE para a colecao de fichas tecnicas', function () {
	return autenticar().then(() => cy.executar_ficha_tecnica({ method: 'DELETE' })).then((response) => { this.response = response })
})
