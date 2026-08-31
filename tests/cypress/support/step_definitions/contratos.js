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
