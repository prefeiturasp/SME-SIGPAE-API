import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_dilog_qualidade'), Cypress.env('senha'))
}
When('consulto ficha de recebimento na listagem {string}', function (rota) {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ caminho: rota === 'principal' ? '' : rota + '/', qs: { page_size: 2 } })).then((response) => { this.response = response })
})
Then('a listagem de fichas de recebimento retorna resultados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array')
})
When('consulto ficha de recebimento com filtro {string} igual a {string}', function (campo, valor) {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ qs: { [campo]: valor } })).then((response) => { this.response = response })
})
Then('a ficha de recebimento retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('a lista de fichas de recebimento esta vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
})
When('consulto ficha de recebimento com tamanho de pagina {int}', function (page_size) {
	this.tamanho = page_size
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ qs: { page_size } })).then((response) => { this.response = response })
})
Then('a ficha de recebimento respeita o tamanho da pagina', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.have.length(Math.min(this.tamanho, this.response.body.count))
})
When('consulto detalhe de ficha de recebimento existente', function () {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ qs: { page_size: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.uuid = response.body.results[0].uuid
		return cy.executar_fichas_de_recebimento({ caminho: this.uuid + '/' })
	}).then((response) => { this.response = response })
})
Then('o detalhe corresponde a ficha de recebimento consultada', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
When('consulto ficha de recebimento inexistente na acao {string}', function (acao) {
	const caminho = '00000000-0000-0000-0000-000000000000/' + (acao === 'detalhe' ? '' : acao + '/')
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ caminho })).then((response) => { this.response = response })
})
When('executo {string} na rota de ficha de recebimento {string} com acesso {string}', function (method, rota, acesso) {
	return cy.executar_fichas_de_recebimento({ method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido',
		body: method === 'GET' ? undefined : {},
	}).then((response) => { this.response = response })
})
When('envio DELETE para a colecao de fichas de recebimento', function () {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ method: 'DELETE' })).then((response) => { this.response = response })
})

When('gero o PDF de uma ficha de recebimento assinada existente', function () {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ qs: { page_size: 1, status: 'ASSINADA' } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'ficha assinada disponivel para gerar PDF').to.be.an('array').and.not.be.empty
		this.uuid = response.body.results[0].uuid
		return cy.executar_fichas_de_recebimento({ caminho: `${this.uuid}/gerar-pdf-ficha/`, encoding: 'binary' })
	}).then((response) => { this.response = response })
})
Then('a ficha de recebimento retorna um arquivo PDF valido', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body).to.be.a('string')
	expect(this.response.body.slice(0, 5), 'assinatura PDF').to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF'), 'marcador final PDF').to.eq(true)
})

When('valido a permissao de cadastro de recebimento do usuario de qualidade', function () {
	return autenticar().then(() => cy.executar_fichas_de_recebimento({ method: 'POST', body: { password: Cypress.env('senha') } })).then((response) => { this.response = response })
})
Then('o usuario de qualidade pode acessar a validacao de cadastro', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property('etapa')
	expect(this.response.body).to.have.property('data_entrega')
})
