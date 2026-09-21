import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

// Identificador nao numerico reservado aos cenarios negativos; nunca usar um login real.
const usernameInexistente = 'cypress-coresso-usuario-inexistente'
const camposObrigatorios = ['username', 'email', 'nome', 'visao', 'perfil', 'instituicao', 'cpf', 'eh_servidor']

Given('que estou autenticado como escola para cadastro CoreSSO', () => {
	const usuario = Cypress.env('usuario_diretor_ue')
	expect(usuario, 'Usuario escola no .env').to.be.a('string').and.not.be.empty
	cy.autenticar_login(usuario, Cypress.env('senha'))
})

When('acesso {string} do cadastro CoreSSO sem autenticacao', function (operacao) {
	cy.clearCookies()
	cy.requisitar_cadastro_com_coresso(operacao, { username: usernameInexistente, autenticado: false }).then((response) => {
		this.response = response
	})
})

When('cadastro usuario CoreSSO sem dados', function () {
	cy.requisitar_cadastro_com_coresso('cadastrar').then((response) => {
		this.response = response
	})
})

When('cadastro usuario CoreSSO com {string} invalido', function (campo) {
	// Campos obrigatorios ausentes impedem que a validacao alcance a criacao no CoreSSO.
	cy.requisitar_cadastro_com_coresso('cadastrar', { dados: { [campo]: 'valor-invalido' } }).then((response) => {
		this.response = response
	})
})

When('acesso {string} do cadastro CoreSSO como escola', function (operacao) {
	cy.requisitar_cadastro_com_coresso(operacao, { username: usernameInexistente }).then((response) => {
		this.response = response
	})
})

Then('o cadastro CoreSSO retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('o cadastro CoreSSO informa os campos obrigatorios', function () {
	expect(this.response.status).to.eq(400)
	camposObrigatorios.forEach((campo) => {
		expect(this.response.body).to.have.property(campo).that.is.an('array').and.not.be.empty
	})
})

Then('o cadastro CoreSSO retorna erro no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property(campo).that.is.an('array').and.not.be.empty
})

Then('o cadastro CoreSSO informa usuario inexistente', function () {
	expect(this.response.status).to.eq(400)
	const mensagem = this.response.body.detail.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
	expect(mensagem).to.contain('Usuario nao encontrado')
})
