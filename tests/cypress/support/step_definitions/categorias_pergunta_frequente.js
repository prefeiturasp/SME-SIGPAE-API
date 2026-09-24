import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'
const inexistente = '00000000-0000-0000-0000-000000000000'
const requisitar = (operacao, opcoes) => cy.requisitar_categorias_pergunta_frequente(operacao, opcoes)

Given('que estou autenticado como {string} para categorias FAQ', function (perfil) {
	const chave = perfil === 'gestor' ? 'usuario_codae' : 'usuario_diretor_ue'
	expect(Cypress.env(chave), chave).to.be.a('string').and.not.be.empty
	cy.autenticar_login(Cypress.env(chave), Cypress.env('senha'))
})

When('consulto {string} de categorias FAQ', function (operacao) {
	this.operacao = operacao
	requisitar(operacao, { query: operacao === 'listar' ? { page: 1, page_size: 2 } : {} }).then((response) => { this.response = response })
})
Then('a consulta de categorias FAQ retorna sucesso', function () {
	expect(this.response.status).to.eq(200)
	const itens = this.operacao === 'listar' ? this.response.body.results : this.response.body
	expect(itens).to.be.an('array')
	if (this.operacao === 'listar') {
		expect(this.response.body.count).to.be.a('number')
		expect(this.response.body).to.include.keys('next', 'previous')
		expect(itens.length).to.be.at.most(2)
	}
	itens.forEach((item) => {
		expect(item.uuid).to.be.a('string').and.not.be.empty
		expect(item.nome).to.be.a('string').and.not.be.empty
		if (this.operacao === 'perguntas') expect(item.perguntas).to.be.an('array')
	})
})

Given('que criei uma categoria FAQ de teste', function () {
	this.nome = `Cypress FAQ ${Date.now()}-${Cypress._.random(100000, 999999)}`
	requisitar('cadastrar', { dados: { nome: this.nome } }).then((response) => {
		if (response.status === 201) this.uuidCriada = response.body.uuid
		expect(response.status).to.eq(201)
		expect(response.body.nome).to.eq(this.nome)
		expect(this.uuidCriada).to.be.a('string').and.not.be.empty
	})
})
When('consulto a categoria FAQ criada', function () {
	requisitar('detalhar', { uuid: this.uuidCriada }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.include({ uuid: this.uuidCriada, nome: this.nome })
	})
})
When('atualizo a categoria FAQ usando {string}', function (operacao) {
	this.nome = `${this.nome} ${operacao}`
	requisitar(operacao, { uuid: this.uuidCriada, dados: { nome: this.nome } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.nome).to.eq(this.nome)
	})
})
When('excluo a categoria FAQ criada', function () {
	const uuid = this.uuidCriada
	requisitar('excluir', { uuid }).then((response) => {
		expect(response.status).to.eq(204)
		this.uuidCriada = undefined
	})
	requisitar('detalhar', { uuid }).its('status').should('eq', 404)
})
After({ tags: '@categoria_faq_criada' }, function () {
	if (this.uuidCriada) requisitar('excluir', { uuid: this.uuidCriada }).its('status').should('eq', 204)
})

When('envio categoria FAQ com nome {string} usando {string}', function (tipo, operacao) {
	const dados = tipo === 'ausente' ? {} : { nome: tipo === 'vazio' ? '' : tipo === 'espacos' ? '   ' : 'A'.repeat(101) }
	requisitar(operacao, { uuid: this.uuidCriada, dados }).then((response) => { this.response = response })
})
Then('a categoria FAQ retorna erro no nome', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.nome).to.be.an('array').and.not.be.empty
})
When('tento cadastrar categoria FAQ duplicada', function () {
	requisitar('cadastrar', { dados: { nome: this.nome } }).then((response) => {
		this.response = response
		// Se a API aceitar a duplicata, remover tambem esse registro antes de falhar.
		if (response.status === 201) requisitar('excluir', { uuid: response.body.uuid }).its('status').should('eq', 204)
	})
})
When('acesso categoria FAQ inexistente usando {string}', function (operacao) {
	requisitar(operacao, { uuid: inexistente, dados: ['atualizar', 'parcial', 'cadastrar'].includes(operacao) ? { nome: 'Teste invalido' } : undefined }).then((response) => { this.response = response })
})
When('acesso categorias FAQ sem autenticacao usando {string}', function (operacao) {
	cy.clearCookies()
	requisitar(operacao, { uuid: inexistente, autenticado: false }).then((response) => { this.response = response })
})
Then('a operacao de categoria FAQ retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
