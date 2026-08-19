import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidValido = '32e04f4b-7b10-4a73-afbc-d2550c3b1511/'
const uuidInvalido = 'b2dbaff4-dbd3-45b8-b67c-57ff4b5ad35b/'
const uuidPut = '5a192d62-999f-4805-89ed-91e9a88cc0b4/'
const uuidValidacoesPut = '1c3a8300-d963-49fb-a322-dccb6e06bcdd/'
const uuidPatch = 'b38437a5-ec30-406a-84cf-be4109a8651a/'

function nomeUnico(prefixo) {
	return `${prefixo} ${Date.now()} ${Cypress._.random(1000, 9999)}`
}

function buscarUuid(nome) {
	return cy.consultar_produtos_edital(`?nome=${encodeURIComponent(nome)}`)
		.then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results).to.be.an('array').and.not.empty
			return response.body.results[0].uuid
		})
}

function excluir(uuid) {
	if (!uuid) return
	cy.excluir_produto_edital(uuid).then((response) => {
		expect([204, 404]).to.include(response.status)
	})
}

function dadosInvalidos(erro) {
	const dados = { nome: 'Teste Automacao', ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	if (erro === 'tipo invalido') dados.tipo_produto = 'TERCEIRA'
	if (erro === 'sem nome') delete dados.nome
	if (erro === 'nome em branco') dados.nome = ''
	if (erro === 'sem ativo') delete dados.ativo
	if (erro === 'ativo em branco') dados.ativo = ''
	return dados
}

Given('que estou autenticado para gerenciar produtos do edital', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
})

When('consulto produtos do edital pelo filtro {string}', function (filtro) {
	if (filtro === 'nome existente') {
		cy.consultar_produtos_edital('').then((lista) => {
			expect(lista.status).to.eq(200)
			expect(lista.body.results).to.be.an('array').and.not.empty
			const nome = lista.body.results[0].nome
			cy.consultar_produtos_edital(`?nome=${encodeURIComponent(nome)}`)
				.then((response) => { this.response = response })
		})
		return
	}
	const filtros = {
		'sem filtro': '',
		'nome inexistente': '?nome=Produto nao existente',
		'data de cadastro': '?data_cadastro=13/03/2025',
		'data invalida': '?data_cadastro=13/03',
		status: `?status=${Math.random() < 0.5 ? 'Ativo' : 'Inativo'}`,
	}
	cy.consultar_produtos_edital(filtros[filtro]).then((response) => { this.response = response })
})

Then('a consulta de produtos do edital retorna uma lista valida', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.empty
	expect(this.response.body.results[0]).to.include.all.keys('uuid', 'nome', 'status', 'criado_em')
})

Then('a consulta de produtos do edital retorna uma lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.be.an('array').and.empty
})

Then('a consulta de produtos do edital retorna erro de data invalida', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property('data_cadastro')
})

When('cadastro um produto valido do edital', function () {
	this.dados = { nome: nomeUnico('Teste Automacao Novo Produto Cadastrado'), ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	cy.cadastrar_produto_edital(this.dados).then((response) => { this.response = response })
})

Then('o produto do edital e criado e removido com sucesso', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body.ativo).to.eq('True')
	expect(this.response.body.tipo_produto).to.eq('TERCEIRIZADA')
	buscarUuid(this.dados.nome).then(excluir)
})

When('cadastro duas vezes o mesmo produto do edital', function () {
	this.dados = { nome: nomeUnico('Produto Duplicado'), ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	cy.cadastrar_produto_edital(this.dados).then((primeira) => {
		expect(primeira.status).to.eq(201)
		buscarUuid(this.dados.nome).then((uuid) => {
			cy.cadastrar_produto_edital(this.dados).then((response) => { this.response = response })
			excluir(uuid)
		})
	})
})

Then('o segundo cadastro do produto retorna item ja cadastrado', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body[0]).to.eq('Item já cadastrado.')
})

When('cadastro produto do edital com erro {string}', function (erro) {
	cy.cadastrar_produto_edital(dadosInvalidos(erro)).then((response) => { this.response = response })
})

Then('o cadastro invalido do produto retorna erro no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property(campo)
})

When('consulto produto do edital por UUID {string}', function (tipo) {
	cy.validar_produto_edital(tipo === 'valido' ? uuidValido : uuidInvalido)
		.then((response) => { this.response = response })
})

Then('o produto do edital retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('uuid', 'nome', 'status', 'criado_em')
})

Then('a operacao de produto do edital retorna status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.body).to.exist
})

When('consulto a lista auxiliar de produtos {string}', function (lista) {
	const consultas = {
		'completa logistica': () => cy.validar_lista_completa_logistica(),
		nomes: () => cy.validar_lista_nomes(),
		'nomes logistica': () => cy.validar_lista_nomes_logistica(),
		'todos produtos logistica': () => cy.validar_produtos_logistica(),
	}
	consultas[lista]().then((response) => { this.response = response })
})

Then('a lista auxiliar de produtos retorna resultados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array').and.not.empty
})

When('atualizo um produto do edital por PUT com dados validos', function () {
	const dados = { nome: 'PRODUTO ATUALIZADO COM SUCESSO', ativo: 'Ativo', tipo_produto: 'TERCEIRIZADA' }
	cy.atualizar_produto_edital(uuidPut, dados).then((response) => { this.response = response })
})

Then('o produto e atualizado e restaurado por PUT', function () {
	expect(this.response.status).to.eq(200)
	const original = { nome: 'PRODUTO CRIADO', ativo: 'Ativo', tipo_produto: 'TERCEIRIZADA' }
	cy.atualizar_produto_edital(uuidPut, original).its('status').should('eq', 200)
})

function atualizarDuplicado(metodo, contexto) {
	const base = { nome: nomeUnico(`Produto Base ${metodo}`), ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	const alvo = { nome: nomeUnico(`Produto Alvo ${metodo}`), ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	cy.cadastrar_produto_edital(base).then(() => buscarUuid(base.nome).then((uuidBase) => {
		cy.cadastrar_produto_edital(alvo).then(() => buscarUuid(alvo.nome).then((uuidAlvo) => {
			const dados = { nome: base.nome, ativo: 'Ativo', tipo_produto: 'TERCEIRIZADA' }
			const comando = metodo === 'PUT' ? cy.atualizar_produto_edital : cy.atualizar_produto_edital_patch
			comando(`${uuidAlvo}/`, dados).then((response) => { contexto.response = response })
			excluir(uuidAlvo)
		}))
		excluir(uuidBase)
	}))
}

When('atualizo produto do edital por PUT com nome duplicado', function () { atualizarDuplicado('PUT', this) })
When('atualizo produto do edital por PATCH com nome duplicado', function () { atualizarDuplicado('PATCH', this) })

Then('a atualizacao do produto retorna item ja cadastrado', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body[0]).to.eq('Item já cadastrado.')
})

When('atualizo produto do edital por PUT com erro {string}', function (erro) {
	cy.atualizar_produto_edital(uuidValidacoesPut, dadosInvalidos(erro))
		.then((response) => { this.response = response })
})

When('atualizo produto do edital por PATCH com erro {string}', function (erro) {
	cy.atualizar_produto_edital_patch(uuidPatch, dadosInvalidos(erro))
		.then((response) => { this.response = response })
})

Then('a atualizacao invalida do produto retorna erro no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property(campo)
})

When('crio e excluo um produto do edital', function () {
	const dados = { nome: nomeUnico('Automacao Produto Para Exclusao'), ativo: 'True', tipo_produto: 'TERCEIRIZADA' }
	cy.cadastrar_produto_edital(dados).then((inclusao) => {
		expect(inclusao.status).to.eq(201)
		buscarUuid(dados.nome).then((uuid) => {
			cy.excluir_produto_edital(uuid).then((response) => { this.response = response })
		})
	})
})

Then('a exclusao do produto do edital retorna status 204', function () {
	expect(this.response.status).to.eq(204)
})

When('excluo um produto do edital inexistente', function () {
	cy.excluir_produto_edital(uuidInvalido).then((response) => { this.response = response })
})

When('atualizo um produto do edital por PATCH com dados validos', function () {
	const dados = { nome: 'PRODUTO ATUALIZADO VIA PATCH COM SUCESSO', ativo: 'Ativo', tipo_produto: 'TERCEIRIZADA' }
	cy.atualizar_produto_edital_patch(uuidPatch, dados).then((response) => { this.response = response })
})

Then('o produto e atualizado e restaurado por PATCH', function () {
	expect(this.response.status).to.eq(200)
	const original = { nome: 'PRODUTO ATUALIZADO VIA PATCH', ativo: 'Ativo', tipo_produto: 'TERCEIRIZADA' }
	cy.atualizar_produto_edital_patch(uuidPatch, original).its('status').should('eq', 200)
})
