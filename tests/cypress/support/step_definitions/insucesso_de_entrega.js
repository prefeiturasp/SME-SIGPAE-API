import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil = 'distribuidor') {
	const usuarios = { distribuidor: 'usuario_distribuidor', escola: 'usuario_diretor_ue' }
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial de ' + perfil + ' configurada no ambiente').to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.executar_insucesso_de_entrega(opcoes).then((response) => { contexto.response = response })
}

function validarInsucesso(insucesso) {
	expect(insucesso.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(insucesso.guia).to.be.an('object').and.have.property('uuid')
	expect(insucesso.criado_por).to.be.an('object')
	for (const campo of ['motivo', 'nome_motorista', 'placa_veiculo', 'hora_tentativa', 'justificativa']) {
		expect(insucesso[campo], campo).to.be.a('string').and.not.be.empty
	}
}

When('consulto a listagem de insucesso de entrega', function () {
	return autenticar().then(() => consultar(this, { qs: { limit: 2 } }))
})

Then('insucesso de entrega retorna lista paginada valida', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarInsucesso)
})

When('consulto o detalhe de um insucesso de entrega existente', function () {
	return autenticar().then(() => cy.executar_insucesso_de_entrega({ qs: { limit: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'insucesso de entrega disponivel em QA').to.be.an('array').and.not.be.empty
		this.insucessoReferencia = response.body.results[0]
		return consultar(this, { caminho: this.insucessoReferencia.uuid + '/' })
	})
})

Then('o detalhe do insucesso de entrega corresponde ao registro consultado', function () {
	validarInsucesso(this.response.body)
	expect(this.response.body).to.deep.eq(this.insucessoReferencia)
})

When('executo {string} em insucesso de entrega na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = {
		method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}
	if (['distribuidor', 'escola'].includes(acesso)) return autenticar(acesso).then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('insucesso de entrega retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('insucesso de entrega informa os campos obrigatorios', function () {
	for (const campo of ['guia', 'motivo', 'nome_motorista', 'placa_veiculo', 'hora_tentativa', 'justificativa']) {
		expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})
