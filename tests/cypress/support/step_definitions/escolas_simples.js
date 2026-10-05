import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}
function consultar(contexto, opcoes = {}) {
	return cy.executar_escolas_simples({ token: globalThis.token, qs: { limit: 2 }, ...opcoes }).then((response) => { contexto.response = response })
}
function referencia(contexto) {
	return cy.executar_escolas_simples({ token: globalThis.token, qs: { limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		contexto.escola = response.body.results[0]
	})
}
function validarEscola(escola) {
	expect(escola).to.include.all.keys('uuid', 'nome', 'codigo_eol', 'tipo_unidade', 'lote', 'tipo_gestao', 'diretoria_regional', 'periodos_escolares', 'quantidade_alunos', 'quantidade_alunos_cei_da_cemei', 'quantidade_alunos_emei_da_cemei')
	expect(escola.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(escola.nome).to.be.a('string')
	expect(escola.codigo_eol).to.be.a('string')
	expect(escola.periodos_escolares).to.be.an('array')
	for (const campo of ['tipo_unidade', 'lote', 'tipo_gestao', 'diretoria_regional']) {
		if (escola[campo] !== null) expect(escola[campo]).to.be.an('object').and.have.property('uuid')
	}
}
When('consulto a listagem de escolas simples', function () {
	return autenticar().then(() => consultar(this))
})
When('consulto o detalhe de uma escola simples existente', function () {
	return autenticar().then(() => referencia(this)).then(() => consultar(this, { uuid: this.escola.uuid }))
})
When('consulto escolas simples com deslocamento', function () {
	return autenticar().then(() => consultar(this)).then(() => {
		expect(this.response.status).to.eq(200)
		expect(this.response.body.results).to.have.length(2)
		this.segundaEscola = this.response.body.results[1]
		return consultar(this, { qs: { limit: 1, offset: 1 } })
	})
})
When('consulto escolas simples alem do total', function () {
	return autenticar().then(() => consultar(this)).then(() => {
		expect(this.response.status).to.eq(200)
		return consultar(this, { qs: { limit: 1, offset: this.response.body.count } })
	})
})
When('envio PATCH vazio para uma escola simples existente', function () {
	return autenticar().then(() => referencia(this)).then(() => consultar(this, { metodo: 'PATCH', uuid: this.escola.uuid, body: {} }))
})
When('envio PUT vazio para uma escola simples existente', function () {
	return autenticar().then(() => referencia(this)).then(() => consultar(this, { metodo: 'PUT', uuid: this.escola.uuid, body: {} }))
})
When('envio {string} com codigo EOL invalido para uma escola simples', function (metodo) {
	return autenticar().then(() => referencia(this)).then(() => consultar(this, { metodo, uuid: this.escola.uuid, body: { codigo_eol: '1234567' } }))
})
When('executo {string} em escolas simples na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	const opcoes = { metodo, uuid: rota === 'listagem' ? '' : rota === 'malformado' ? 'uuid-invalido' : inexistente, body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined }
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'token invalido' ? 'token-invalido' : undefined })
})
Then('a operacao de escolas simples retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('escolas simples retorna uma lista paginada valida', function () {
	expect(this.response.body).to.have.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(Number.isInteger(this.response.body.count)).to.eq(true)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarEscola)
})
Then('o detalhe de escolas simples corresponde a escola consultada', function () {
	validarEscola(this.response.body)
	expect(this.response.body).to.deep.eq(this.escola)
})
Then('escolas simples respeita o deslocamento', function () {
	expect(this.response.body.results).to.deep.eq([this.segundaEscola])
})
Then('escolas simples retorna pagina vazia', function () {
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.next).to.eq(null)
})
Then('escolas simples informa campos obrigatorios', function () {
	for (const campo of ['codigo_eol', 'tipo_unidade', 'lote', 'tipo_gestao', 'diretoria_regional']) expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
Then('escolas simples informa codigo EOL invalido', function () {
	expect(this.response.body.codigo_eol).to.be.an('array').and.not.be.empty
})
