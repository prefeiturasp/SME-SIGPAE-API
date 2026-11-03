import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}
function consultar(contexto, opcoes) {
	return cy.executar_historico_escola(opcoes).then((response) => { contexto.response = response })
}
When('consulto o historico de uma escola existente no mes {int} e ano {int}', function (mes, ano) {
	return autenticar().then(() => cy.request({
		url: Cypress.config('baseUrl') + 'api/escolas-simples/', qs: { limit: 1 },
		headers: { Authorization: 'JWT ' + globalThis.token }, failOnStatusCode: false,
	})).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'escola disponivel em QA').to.be.an('array').and.not.be.empty
		return consultar(this, { uuid: response.body.results[0].uuid, qs: { mes, ano } })
	})
})
Then('o historico escolar retorna nome e tipo de unidade', function () {
	expect(this.response.body).to.have.all.keys('nome', 'tipo_unidade')
	expect(this.response.body.nome).to.be.a('string').and.not.be.empty
	expect(this.response.body.tipo_unidade).to.have.all.keys('uuid', 'iniciais')
	expect(this.response.body.tipo_unidade.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(this.response.body.tipo_unidade.iniciais).to.be.a('string').and.not.be.empty
})
When('consulto historico escolar com mes {string} e ano {string}', function (mes, ano) {
	const qs = {}
	if (mes !== 'ausente') qs.mes = mes
	if (ano !== 'ausente') qs.ano = ano
	return autenticar().then(() => consultar(this, { uuid: inexistente, qs }))
})
When('executo {string} em historico escolar com acesso {string}', function (method, acesso) {
	const opcoes = { method, uuid: inexistente, qs: { mes: 1, ano: 2024 },
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined }
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})
Then('historico escolar retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([400, 401, 405].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('historico escolar informa erro de {string}', function (erro) {
	const mensagens = { obrigatorios: 'obrigat', inteiros: 'inteiros', intervalo: 'entre 1 e 12' }
	expect(this.response.body.detail).to.include(mensagens[erro])
})
