import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

Given('que estou autenticado na API como CODAE para consultar a CODAE', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})

When('consulto a lista paginada da CODAE', function () {
	cy.consultar_codae().then((response) => {
		this.response = response
	})
})

Then('a consulta da CODAE deve retornar status 200 e registros validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.to.be.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.not.to.be.empty
	this.response.body.results.forEach((codae) => {
		expect(codae).to.include.all.keys(
			'id',
			'quantidade_alunos',
			'nome',
			'uuid',
			'acesso_modulo_medicao_inicial',
		)
		expect(codae.id).to.be.a('number')
		expect(codae.quantidade_alunos).to.be.a('number')
		expect(codae.nome).to.be.a('string').and.not.to.be.empty
		expect(codae.uuid).to.be.a('string').and.not.to.be.empty
		expect(codae.acesso_modulo_medicao_inicial).to.be.a('boolean')
	})
})

When('consulto uma CODAE existente por UUID', function () {
	cy.consultar_codae('limit=1&offset=0').then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.codae = response.body.results[0]
		cy.requisitar_codae('GET', { uuid: this.codae.uuid }).then((resposta) => { this.response = resposta })
	})
})
Then('o detalhe da CODAE corresponde ao registro solicitado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include({ uuid: this.codae.uuid, id: this.codae.id, nome: this.codae.nome })
	expect(this.response.body.quantidade_alunos).to.be.a('number')
})
When('consulto CODAE com pagina de um registro', function () {
	cy.consultar_codae('limit=1&offset=0').then((response) => { this.response = response })
})
Then('a paginacao CODAE respeita o limite solicitado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.have.length(1)
})
When('acesso CODAE inexistente usando {string}', function (metodo) {
	cy.requisitar_codae(metodo, { uuid: '00000000-0000-0000-0000-000000000000', dados: ['PUT', 'PATCH'].includes(metodo) ? {} : undefined }).then((response) => { this.response = response })
})
When('acesso {string} da CODAE sem autenticacao no caminho {string}', function (metodo, caminho) {
	cy.clearCookies()
	cy.requisitar_codae(metodo, { uuid: caminho === 'detalhe' ? '00000000-0000-0000-0000-000000000000' : undefined, autenticado: false }).then((response) => { this.response = response })
})
Then('a operacao CODAE retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
When('envio cadastro CODAE com {string} invalido', function (campo) {
	const dados = campo === 'quantidade_alunos' ? { quantidade_alunos: 'invalido' } : { quantidade_alunos: 0, nome: 'A'.repeat(101) }
	cy.requisitar_codae('POST', { dados }).then((response) => { this.response = response })
})
When('envio cadastro CODAE sem quantidade de alunos', function () {
	cy.requisitar_codae('POST', { dados: {} }).then((response) => { this.response = response })
})
When('envio atualizacao CODAE invalida usando {string}', function (metodo) {
	cy.consultar_codae('limit=1&offset=0').then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		// Nome acima do limite impede a gravacao no registro existente.
		cy.requisitar_codae(metodo, { uuid: response.body.results[0].uuid, dados: { quantidade_alunos: 0, nome: 'A'.repeat(101) } }).then((resposta) => { this.response = resposta })
	})
})
Then('a CODAE retorna erro no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
