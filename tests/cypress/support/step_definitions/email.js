import { When, Then } from 'cypress-cucumber-preprocessor/steps'
const parametros = { limit: 10, offset: 0 }
const campos = [
	'host', 'port', 'username', 'password', 'from_email',
	'use_tls', 'use_ssl', 'timeout',
]
When('consulto as configuracoes de email autenticado', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.consultar_email(parametros).then((response) => { this.response = response })
})
When('consulto as configuracoes de email sem autenticacao', function () {
	cy.consultar_email(parametros, false).then((response) => { this.response = response })
})
When('cadastro uma configuracao de email invalida', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.cadastrar_email({
		host: '', port: 'invalida', username: '', password: '',
		from_email: 'email-invalido', use_tls: 'invalido',
		use_ssl: 'invalido', timeout: 'invalido',
	}).then((response) => { this.response = response })
})
When('cadastro uma configuracao de email sem autenticacao', function () {
	cy.cadastrar_email({
		host: 'smtp.teste.local', port: 587, username: 'usuario.teste',
		password: 'senha-teste', from_email: 'teste@example.com',
		use_tls: true, use_ssl: false, timeout: 30,
	}, false).then((response) => { this.response = response })
})
Then('a lista de configuracoes de email retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number')
	expect(this.response.body.results).to.be.an('array')
	this.response.body.results.forEach((email) => {
		expect(email).to.include.all.keys(...campos)
		expect(email.host).to.be.a('string').and.not.be.empty
		expect(email.port).to.be.a('number')
		expect(email.username).to.be.a('string')
		expect(email.password).to.be.a('string')
		expect(email.from_email).to.be.a('string')
		expect(email.use_tls).to.be.a('boolean')
		expect(email.use_ssl).to.be.a('boolean')
		expect(email.timeout).to.be.a('number')
	})
})
Then('a consulta de email retorna status 401', function () {
	expect(this.response.status).to.eq(401)
	expect(this.response.body).to.have.property('detail')
})
Then('o cadastro de email retorna status 400', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.be.an('object').and.not.be.empty
})
Then('o cadastro de email retorna status 401', function () {
	expect(this.response.status).to.eq(401)
	expect(this.response.body).to.have.property('detail')
})
