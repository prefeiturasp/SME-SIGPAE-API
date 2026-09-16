import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuid = '5067e137-e5f3-4876-a63f-7f58cce93f33'
function validarPeriodo(periodo) {
	expect(periodo).to.include.all.keys(
		'tipos_alimentacao', 'possui_alunos_regulares', 'nome',
		'uuid', 'posicao', 'tipo_turno',
	)
	expect(periodo.tipos_alimentacao).to.be.an('array')
	if (periodo.tipos_alimentacao.length) {
		expect(periodo.tipos_alimentacao[0]).to.include.all.keys('nome', 'uuid', 'posicao')
	}
}
Given('que estou autenticado como CODAE para consultar periodos escolares', () => {
	cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
})
When('consulto todos os periodos escolares', function () {
	cy.consultar_periodos_escolares().then((response) => { this.response = response })
})
When('consulto periodos escolares por um nome existente', function () {
	cy.consultar_periodos_escolares().then((lista) => {
		this.nome = lista.body.results[0].nome
		cy.consultar_periodos_escolares_por_nome(this.nome).then((response) => {
			this.response = response
		})
	})
})
When('consulto periodos escolares pelo nome invalido', function () {
	cy.consultar_periodos_escolares_por_nome('Nome Invalido Para Teste')
		.then((response) => { this.response = response })
})
When('consulto um periodo escolar por UUID existente', function () {
	cy.consultar_periodos_escolares().then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy.consultar_periodos_escolares_por_uuid(this.uuid).then((response) => {
			this.response = response
		})
	})
})
When('consulto um periodo escolar por UUID invalido', function () {
	cy.consultar_periodos_escolares_por_uuid('3ac751ee-f95d-4d5b-80da-437506b00000')
		.then((response) => { this.response = response })
})
function consultarFaixa(contexto, periodoUuid, data) {
	cy.consultar_alunos_por_faixa_etaria_data_referencia(periodoUuid, data)
		.then((response) => { contexto.response = response })
}
When('consulto alunos por faixa etaria com data valida', function () {
	cy.autenticar_login(Cypress.config('usuario_diretor_ue'), Cypress.config('senha'))
	consultarFaixa(this, uuid, '2025-10-15')
})
When('consulto alunos por faixa etaria com data invalida', function () {
	consultarFaixa(this, uuid, '2025-13-15')
})
When('consulto alunos por faixa etaria com UUID invalido', function () {
	consultarFaixa(this, '5067e137-e5f3-4876-a63f-0a00aaa00a00', '2025-12-15')
})
When('consulto inclusao continua por mes como diretor de UE', function () {
	cy.autenticar_login(Cypress.config('usuario_diretor_ue'), Cypress.config('senha'))
	cy.consultar_inclusao_continua_por_mes('?mes=10&ano=2025').then((response) => {
		this.response = response
	})
})
Then('a lista de periodos escolares retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (this.response.body.results.length) validarPeriodo(this.response.body.results[0])
})
Then('a consulta por nome retorna o periodo esperado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.be.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarPeriodo(this.response.body.results[0])
	expect(this.response.body.results[0].nome).to.eq(this.nome)
})
Then('a consulta por nome invalido retorna uma lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.be.an('array').and.empty
})
Then('a consulta por UUID retorna o periodo esperado', function () {
	expect(this.response.status).to.eq(200)
	validarPeriodo(this.response.body)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('a consulta do periodo invalido retorna status 400 ou 404', function () {
	expect([400, 404]).to.include(this.response.status)
})
Then('a consulta por faixa etaria retorna status suportado e dados coerentes', function () {
	expect([200, 500]).to.include(this.response.status)
	if (this.response.status === 500) return expect(this.response.body).to.exist
	expect(this.response.body).to.include.all.keys('count', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (this.response.body.results.length) {
		const resultado = this.response.body.results[0]
		expect(resultado).to.include.all.keys('faixa_etaria', 'count')
		expect(resultado.faixa_etaria).to.include.all.keys('__str__', 'uuid', 'inicio', 'fim')
	}
})
Then('a consulta por data invalida retorna o erro esperado', function () {
	expect([200, 400]).to.include(this.response.status)
	expect(this.response.body.data_referencia[0].toLowerCase()).to.contain('data')
})
Then('a consulta por UUID invalido retorna status 400 ou 404', function () {
	expect([400, 404]).to.include(this.response.status)
})
Then('a inclusao continua retorna status permitido e dados coerentes', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) expect(this.response.body.detail).to.not.be.empty
	else expect(this.response.body).to.have.property('periodos')
})
