import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

function consultar(contexto, qs = {}) {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.executar_downloads({ qs: { page: 1, page_size: 10, ...qs } }).then((response) => {
		contexto.response = response
	})
}

When('consulto os downloads com um usuario CODAE', function () {
	consultar(this)
})

When('consulto downloads filtrando um UUID inexistente', function () {
	consultar(this, { uuid: uuidInexistente })
})

When('consulto downloads com visto {string}', function (visto) {
	consultar(this, { visto })
})

When('executo {string} em downloads na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	const autenticado = acesso === 'autenticado'
	if (autenticado) cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	else cy.clearCookies()
	const caminhos = { listagem: '', detalhe: uuidInexistente, 'marcar-visto': 'marcar-visto', 'quantidade-nao-vistos': 'quantidade-nao-vistos' }
	expect(caminhos).to.have.property(rota)
	cy.executar_downloads({
		metodo,
		caminho: caminhos[rota],
		body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined,
		autenticado,
	}).then((response) => { this.response = response })
})

When('marco como visto um download inexistente', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.executar_downloads({ metodo: 'PUT', caminho: 'marcar-visto', body: { uuid: uuidInexistente, visto: true } }).then((response) => {
		this.response = response
	})
})

Then('a operacao de downloads retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('a consulta de downloads retorna uma lista paginada valida', function () {
	const body = this.response.body
	expect(body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(body.count).to.be.a('number').and.at.least(0)
	expect(Number.isInteger(body.count)).to.eq(true)
	for (const campo of ['next', 'previous']) {
		if (body[campo] !== null) expect(body[campo]).to.be.a('string').and.not.be.empty
	}
	expect(body.results).to.be.an('array').and.have.length.at.most(10)
	expect(body.count).to.be.at.least(body.results.length)
	body.results.forEach((download) => {
		expect(download).to.have.all.keys('uuid', 'identificador', 'arquivo', 'status', 'data_criacao', 'msg_erro', 'visto')
		expect(download.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
		for (const campo of ['identificador', 'status', 'data_criacao', 'msg_erro']) expect(download[campo]).to.be.a('string')
		if (download.arquivo !== null) expect(download.arquivo).to.be.a('string')
		expect(download.visto).to.be.a('boolean')
	})
})

Then('downloads retorna uma quantidade de nao vistos valida', function () {
	expect(this.response.body).to.have.all.keys('quantidade_nao_vistos')
	const quantidade = this.response.body.quantidade_nao_vistos
	expect(quantidade).to.be.a('number').and.at.least(0)
	expect(Number.isInteger(quantidade)).to.eq(true)
})

Then('a consulta de downloads retorna uma lista vazia', function () {
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
})

Then('os downloads correspondem ao filtro visto {string}', function (visto) {
	this.response.body.results.forEach((download) => {
		expect(download.visto).to.eq(visto === 'true')
	})
})

Then('o cadastro de downloads informa o status obrigatorio', function () {
	expect(this.response.body.status).to.be.an('array').and.not.be.empty
})

Then('downloads retorna uma mensagem de erro', function () {
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
