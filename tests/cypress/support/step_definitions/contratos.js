import { When, Then } from 'cypress-cucumber-preprocessor/steps'
const usuario = () => Cypress.env('usuario_coordenador_logistica')
const senha = () => Cypress.env('senha')
const uuidValido = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
When('consulto dois contratos com usuario autorizado', function () {
	cy.consultar_contratos({ limit: 2, offset: 0, usuario: usuario(), senha: senha() })
		.then((response) => { this.response = response })
})
When('consulto contratos sem autenticacao', function () {
	cy.consultar_contratos({ limit: 2, offset: 0 }).then((response) => {
		this.response = response
	})
})
When('consulto o contrato pelo UUID valido', function () {
	cy.consultar_contrato_por_uuid(uuidValido, usuario(), senha()).then((response) => {
		this.response = response
	})
})
When('consulto um contrato por UUID inexistente', function () {
	cy.consultar_contrato_por_uuid(
		'ffffffff-ffff-4fff-bfff-ffffffffffff', usuario(), senha(),
	).then((response) => { this.response = response })
})
Then('a lista de contratos retorna status 200 e dois contratos validos', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.have.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.be.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.have.length(2)
	this.response.body.results.forEach((contrato) => {
		expect(contrato).to.include.all.keys(
			'edital', 'vigencias', 'lotes', 'terceirizada', 'diretorias_regionais',
			'uuid', 'numero', 'processo', 'encerrado', 'programa',
		)
		expect(contrato.uuid).to.be.a('string').and.not.be.empty
		expect(contrato.vigencias).to.be.an('array')
		expect(contrato.lotes).to.be.an('array')
		expect(contrato.diretorias_regionais).to.be.an('array')
		expect(contrato.terceirizada).to.be.an('object')
	})
})
Then('a lista de contratos retorna status 401', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(401)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('o contrato retorna status 200 e os dados esperados', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.include.all.keys(
		'edital', 'vigencias', 'lotes', 'terceirizada', 'diretorias_regionais',
		'modalidade', 'uuid', 'numero', 'processo', 'encerrado', 'programa',
	)
	expect(this.response.body.uuid).to.eq(uuidValido)
	expect(this.response.body.vigencias).to.be.an('array')
	expect(this.response.body.lotes).to.be.an('array')
	expect(this.response.body.diretorias_regionais).to.be.an('array')
	expect(this.response.body.terceirizada).to.be.an('object')
})
Then('o contrato inexistente retorna pagina HTML com status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.headers['content-type']).to.include('text/html')
	expect(this.response.body).to.include('404')
})

When('consulto contratos de pos recebimento de uma empresa existente', function () {
	cy.autenticar_login(Cypress.env('usuario_dilog_cronograma'), senha())
	cy.consultar_contratos({ limit: 1, offset: 0, usuario: usuario(), senha: senha() }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		const contrato = response.body.results[0]
		this.uuidContrato = contrato.uuid
		expect(contrato.terceirizada.uuid).to.be.a('string').and.not.be.empty
		cy.consultar_listas_contratos('pos_recebimento', { empresa_id: contrato.terceirizada.uuid }).then((resposta) => { this.response = resposta })
	})
})
Then('os contratos de pos recebimento incluem o contrato da empresa', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results.map((item) => item.uuid)).to.include(this.uuidContrato)
	this.response.body.results.forEach((item) => {
		expect(item.numero).to.be.a('string')
		expect(item.uuid).to.be.a('string')
	})
})
When('consulto os numeros de contratos cadastrados', function () {
	cy.autenticar_login(Cypress.env('usuario_dilog_cronograma'), senha())
	cy.consultar_listas_contratos('numeros').then((response) => { this.response = response })
})
Then('a consulta retorna uma lista de numeros de contratos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.numeros_contratos_cadastrados).to.be.an('array').and.not.be.empty
	this.response.body.numeros_contratos_cadastrados.forEach((numero) => expect(numero).to.be.a('string'))
})
When('consulto a lista auxiliar de contratos {string} sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.consultar_listas_contratos(operacao, {}, false).then((response) => { this.response = response })
})
When('consulto contratos de pos recebimento com empresa {string}', function (condicao) {
	cy.autenticar_login(Cypress.env('usuario_dilog_cronograma'), senha())
	const query = condicao === 'ausente' ? {} : { empresa_id: condicao === 'invalida' ? 'invalido' : '00000000-0000-0000-0000-000000000000' }
	cy.consultar_listas_contratos('pos_recebimento', query).then((response) => { this.response = response })
})
Then('a lista de contratos de pos recebimento fica vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.deep.eq([])
})
