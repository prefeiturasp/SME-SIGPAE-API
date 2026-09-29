import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
const perfis = { escola: 'usuario_diretor_ue', codae: 'usuario_codae', dre: 'usuario_dre' }

function autenticar(perfil) {
	const usuario = Cypress.env(perfis[perfil])
	expect(usuario, `Credencial CEMEI do perfil ${perfil}`).to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

When('consulto as alteracoes de cardapio CEMEI', function () {
	autenticar('escola')
	cy.requisitar_alteracoes_cardapio_cemei('listar').then((response) => {
		this.response = response
	})
})

Then('deve retornar a listagem paginada de alteracoes CEMEI', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number')
	expect(this.response.body.results).to.be.an('array')
})

When('consulto {string} de cardapio CEMEI como {string}', function (operacao, perfil) {
	autenticar(perfil)
	cy.requisitar_alteracoes_cardapio_cemei(operacao).then((response) => {
		this.response = response
	})
})

Then('a consulta CEMEI retorna uma lista de solicitacoes', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
})

When('consulto {string} de uma solicitacao CEMEI existente', function (operacao) {
	autenticar('codae')
	cy.requisitar_alteracoes_cardapio_cemei('pedidos_codae').then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'Solicitacao CEMEI para consulta').to.be.an('array').and.not.be.empty
		this.uuid = response.body.results[0].uuid
		cy.requisitar_alteracoes_cardapio_cemei(operacao, { uuid: this.uuid }).then((resposta) => {
			this.response = resposta
		})
	})
})

Then('o detalhe CEMEI corresponde ao UUID solicitado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
})

Then('o relatorio CEMEI e um PDF valido', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.headers['content-type']).to.contain('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
})

When('acesso {string} CEMEI inexistente como {string}', function (operacao, perfil) {
	autenticar(perfil)
	cy.requisitar_alteracoes_cardapio_cemei(operacao, { uuid: inexistente, dados: { justificativa: 'Teste automatizado' } }).then((response) => {
		this.response = response
	})
})

When('acesso {string} CEMEI sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.requisitar_alteracoes_cardapio_cemei(operacao, { uuid: inexistente, autenticado: false }).then((response) => {
		this.response = response
	})
})

When('cadastro alteracao CEMEI sem campos obrigatorios', function () {
	autenticar('escola')
	cy.requisitar_alteracoes_cardapio_cemei('cadastrar', { dados: {} }).then((response) => {
		this.response = response
	})
})

Then('o cadastro CEMEI informa os campos obrigatorios', function () {
	expect(this.response.status).to.eq(400)
	for (const campo of ['motivo', 'escola']) {
		expect(this.response.body).to.have.property(campo).that.is.an('array').and.not.be.empty
	}
})

Then('a operacao CEMEI retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
