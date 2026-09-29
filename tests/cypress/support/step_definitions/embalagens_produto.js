import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

When('executo {string} em embalagens de produto na rota {string} sem autenticacao', function (metodo, rota) {
	cy.clearCookies()
	const uuid = rota === 'detalhe' ? uuidInexistente : ''
	const body = ['POST', 'PUT', 'PATCH'].includes(metodo) ? { nome: 'Teste sem autenticacao' } : undefined
	cy.executar_embalagens_produto(metodo, uuid, body, false).then((response) => {
		this.response = response
		if (metodo === 'POST' && response.status === 201) this.uuidEmbalagem = response.body.uuid
	})
})

When('executo {string} em uma embalagem de produto inexistente', function (metodo) {
	const body = ['PUT', 'PATCH'].includes(metodo) ? { nome: 'Embalagem inexistente' } : undefined
	guardarResposta(this, cy.executar_embalagens_produto(metodo, uuidInexistente, body))
})

When('cadastro uma embalagem de produto com nome de 101 caracteres', function () {
	cy.executar_embalagens_produto('POST', '', { nome: 'A'.repeat(101) }).then((response) => {
		this.response = response
		if (response.status === 201) this.uuidEmbalagem = response.body.uuid
	})
})

When('atualizo a embalagem de produto usando {string} com nome de 101 caracteres', function (metodo) {
	guardarResposta(this, cy.executar_embalagens_produto(metodo, this.uuidEmbalagem, { nome: 'A'.repeat(101) }))
})

Then('embalagens de produto informa erro no nome', function () {
	expect(this.response.body.nome).to.be.an('array').and.not.be.empty
	this.response.body.nome.forEach((mensagem) => {
		expect(mensagem).to.be.a('string').and.not.be.empty
	})
})

Then('embalagens de produto informa erro de autenticacao', function () {
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('o nome original da embalagem de produto foi preservado', function () {
	cy.executar_embalagens_produto('GET', this.uuidEmbalagem).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.include({ uuid: this.uuidEmbalagem, nome: this.nomeEmbalagem })
	})
})

function guardarResposta(contexto, requisicao) {
	requisicao.then((response) => {
		contexto.response = response
	})
}

function validarEmbalagens(response) {
	expect(response.body).to.have.property('results').that.is.an('array')

	response.body.results.forEach((embalagem) => {
		expect(embalagem).to.include.all.keys('uuid', 'nome')
		expect(embalagem.uuid).to.be.a('string').and.not.be.empty
		expect(embalagem.nome).to.be.a('string').and.not.be.empty
	})
}

Given(
	'que estou autenticado como CODAE para consultar embalagens de produto',
	() => {
		cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	},
)

When('consulto todas as embalagens de produto', function () {
	guardarResposta(this, cy.consultar_embalagens_produto())
})

When(
	'consulto embalagens de produto com limite {int} e deslocamento {int}',
	function (limit, offset) {
		this.limit = limit
		this.offset = offset
		guardarResposta(
			this,
			cy.consultar_embalagens_produto({ page: 1, limit, offset }),
		)
	},
)

Then(
	'a consulta de embalagens de produto retorna status 200 e uma lista valida',
	function () {
		expect(this.response.status).to.eq(200)
		validarEmbalagens(this.response)
	},
)

Then(
	'a consulta paginada de embalagens de produto retorna status 200 e uma lista valida',
	function () {
		expect(this.response.status).to.eq(200)
		validarEmbalagens(this.response)
		expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
		cy.consultar_embalagens_produto().then((response) => {
			expect(response.status).to.eq(200)
			expect(this.response.body.count).to.eq(response.body.results.length)
			expect(this.response.body.results).to.deep.eq(response.body.results.slice(this.offset, this.offset + this.limit))
		})
	},
)

function cadastrarEmbalagem(contexto) {
	contexto.nomeEmbalagem = `Automacao Cypress ${Date.now()}-${Cypress._.random(100000, 999999)}`
	return cy.executar_embalagens_produto('POST', '', { nome: contexto.nomeEmbalagem }).then((response) => {
		contexto.response = response
		if (response.status === 201) contexto.uuidEmbalagem = response.body.uuid
		expect(response.status, JSON.stringify(response.body)).to.eq(201)
		expect(contexto.uuidEmbalagem).to.be.a('string').and.not.be.empty
	})
}

After({ tags: '@embalagens_produto' }, function () {
	if (!this.uuidEmbalagem || this.embalagemExcluida) return
	cy.executar_embalagens_produto('DELETE', this.uuidEmbalagem).then((response) => {
		expect(response.status, 'Limpeza da embalagem criada pelo cenario').to.eq(204)
	})
})

Given('que cadastrei uma embalagem de produto para o cenario', function () {
	return cadastrarEmbalagem(this)
})

When('cadastro uma embalagem de produto', function () {
	return cadastrarEmbalagem(this)
})

When('consulto a embalagem de produto criada por UUID', function () {
	guardarResposta(this, cy.executar_embalagens_produto('GET', this.uuidEmbalagem))
})

When('atualizo a embalagem de produto criada usando {string}', function (metodo) {
	expect(['PUT', 'PATCH']).to.include(metodo)
	this.nomeEmbalagem = `Atualizada ${this.nomeEmbalagem}`
	guardarResposta(this, cy.executar_embalagens_produto(metodo, this.uuidEmbalagem, { nome: this.nomeEmbalagem }))
})

When('excluo a embalagem de produto criada', function () {
	cy.executar_embalagens_produto('DELETE', this.uuidEmbalagem).then((response) => {
		this.response = response
		this.embalagemExcluida = response.status === 204
	})
})

Then('a operacao de embalagens de produto retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
})

Then('a embalagem de produto corresponde aos dados enviados', function () {
	expect(this.response.body).to.include({ uuid: this.uuidEmbalagem, nome: this.nomeEmbalagem })
})

Then('a alteracao da embalagem de produto foi persistida', function () {
	cy.executar_embalagens_produto('GET', this.uuidEmbalagem).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.include({ uuid: this.uuidEmbalagem, nome: this.nomeEmbalagem })
	})
})

Then('a embalagem de produto excluida nao pode ser consultada', function () {
	cy.executar_embalagens_produto('GET', this.uuidEmbalagem).then((response) => {
		expect(response.status).to.eq(404)
	})
})
