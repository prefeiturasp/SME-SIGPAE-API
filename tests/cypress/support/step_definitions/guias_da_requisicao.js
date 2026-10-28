import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil = 'logistica') {
	const usuarios = { logistica: 'usuario_coordenador_logistica', dilog: 'usuario_coordenador_codae_dilog_logistica' }
	return cy.autenticar_login(Cypress.env(usuarios[perfil]), Cypress.env('senha'))
}
function consultar(contexto, opcoes) {
	return cy.executar_guias_da_requisicao(opcoes).then((response) => { contexto.response = response })
}
When('consulto guias da requisicao na rota {string} com perfil {string}', function (rota, perfil) {
	this.rotaGuias = rota
	return autenticar(perfil).then(() => consultar(this, { caminho: rota === 'principal' ? '' : rota, qs: { page_size: 2 } }))
})
Then('guias da requisicao retorna uma lista valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
	this.response.body.results.forEach((guia) => {
		if (this.rotaGuias === 'unidades-escolares/') {
			expect(guia).to.have.all.keys('codigo_unidade', 'nome_unidade')
			expect(guia.nome_unidade).to.be.a('string')
		} else {
			expect(guia.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
			expect(guia).to.have.property('numero_guia')
		}
	})
})
When('consulto o detalhe de uma guia da requisicao existente', function () {
	return autenticar().then(() => cy.executar_guias_da_requisicao({ caminho: 'lista-numeros/' })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'guia disponivel em QA').to.be.an('array').and.not.be.empty
		this.guiaReferencia = response.body.results[0]
		return consultar(this, { caminho: this.guiaReferencia.uuid + '/' })
	})
})
Then('o detalhe da guia da requisicao corresponde ao registro consultado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.guiaReferencia.uuid)
	expect(this.response.body.numero_guia).to.eq(this.guiaReferencia.numero_guia)
})
When('executo {string} em guias da requisicao na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = { method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined }
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})
Then('guias da requisicao retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
