import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['uuid', 'nome', 'codigo_eol', 'iniciais', 'acesso_modulo_medicao_inicial']
Given('que estou autenticado como DRE para consultar diretorias simplissimas', () => {
	cy.autenticar_login(Cypress.env('usuario_dre'), Cypress.env('senha'))
})
When('consulto a lista paginada de diretorias simplissimas', function () {
	cy.consultar_dre_simplissima().then((response) => { this.response = response })
})
When('consulto a diretoria simplissima pelo UUID {string}', function (uuid) {
	cy.consultar_dre_simplissima_por_uuid(uuid).then((response) => { this.response = response })
})
When('consulto a lista completa de diretorias simplissimas', function () {
	cy.consultar_lista_completa_dre_simplissima().then((response) => { this.response = response })
})
Then('a lista de diretorias simplissimas retorna status 200 e dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys(...campos)
})
Then('a consulta da diretoria simplissima retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrada apresenta os campos esperados da diretoria', function () {
	if (this.response.status === 200) expect(this.response.body).to.include.all.keys(...campos)
})
Then('a lista completa de diretorias simplissimas retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'iniciais', 'nome', 'codigo_eol')
})

When('consulto duas paginas consecutivas de diretorias simplissimas', function () {
	cy.consultar_dre_simplissima_opcoes({ qs: { limit: 2, offset: 0 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.have.length(2)
		this.paginaReferencia = response.body
		cy.consultar_dre_simplissima_opcoes({ qs: { limit: 1, offset: 1 } }).then((resposta) => { this.response = resposta })
	})
})
Then('a paginacao de diretorias simplissimas respeita limite e deslocamento', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.eq(this.paginaReferencia.count)
	expect(this.response.body.results).to.have.length(1)
	expect(this.response.body.results[0]).to.deep.eq(this.paginaReferencia.results[1])
})
When('consulto diretorias simplissimas alem da ultima pagina', function () {
	cy.consultar_dre_simplissima_opcoes({ qs: { limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		cy.consultar_dre_simplissima_opcoes({ qs: { limit: 1, offset: response.body.count } }).then((resposta) => { this.response = resposta })
	})
})
Then('a pagina de diretorias simplissimas esta vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.next).to.eq(null)
})
When('consulto diretorias simplissimas na rota {string} sem autenticacao', function (rota) {
	cy.clearCookies()
	if (rota === 'detalhe') {
		cy.consultar_dre_simplissima_opcoes({ qs: { limit: 1 } }).then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results).to.have.length(1)
			this.uuidPublico = response.body.results[0].uuid
			cy.consultar_dre_simplissima_opcoes({ caminho: this.uuidPublico, autenticado: false }).then((resposta) => { this.response = resposta })
		})
	} else {
		cy.consultar_dre_simplissima_opcoes({ caminho: rota === 'lista-completa' ? rota : '', autenticado: false }).then((response) => { this.response = response })
	}
	this.rotaPublica = rota
})
Then('a consulta publica de diretorias simplissimas retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	if (this.rotaPublica === 'detalhe') {
		expect(this.response.body.uuid).to.eq(this.uuidPublico)
		expect(this.response.body).to.include.all.keys(...campos)
	} else {
		expect(this.response.body.results).to.be.an('array').and.not.be.empty
		expect(this.response.body.results[0]).to.include.all.keys('uuid', 'nome', 'codigo_eol', 'iniciais')
	}
})
