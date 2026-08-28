import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const tipos = ['MARCA', 'FABRICANTE', 'UNIDADE_MEDIDA', 'EMBALAGEM']
const uuidInvalido = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
let processamentoInicialAguardado = false
function nome(prefixo) {
	return `${prefixo} ${Date.now()} ${Cypress._.random(1000, 9999)}`
}
function item(prefixo = 'Teste Automacao') {
	return { nome: nome(prefixo), tipo: tipos[Cypress._.random(0, tipos.length - 1)] }
}
function excluir(uuid, contexto) {
	if (!uuid) return
	cy.deletar_itens_cadastros(uuid).then((response) => {
		expect([204, 404]).to.include(response.status)
		contexto.exclusao = response
	})
}
function obterUuid(dados) {
	return cy.consultar_itens_cadastros_com_filtros(
		`?nome=${encodeURIComponent(dados.nome)}`,
	).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		return response.body.results[0].uuid
	})
}
Given('que estou autenticado como CODAE para gerenciar itens de cadastros', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	if (!processamentoInicialAguardado) {
		cy.wait(Cypress.env('wait_api_itens_cadastros') || 3000)
		processamentoInicialAguardado = true
	}
})
When('consulto todos os itens de cadastros', function () {
	cy.consultar_itens_cadastros().then((response) => { this.response = response })
})
When('filtro itens de cadastros pelos campos {string} existentes', function (campos) {
	cy.consultar_itens_cadastros().then((lista) => {
		const primeiro = lista.body.results[0]
		const filtro = campos.split(',').map((campo) =>
			`${campo}=${encodeURIComponent(primeiro[campo])}`).join('&')
		cy.consultar_itens_cadastros_com_filtros(`?${filtro}`).then((response) => {
			this.response = response
		})
	})
})
When('filtro itens de cadastros pelo campo {string} invalido', function (campo) {
	cy.consultar_itens_cadastros_com_filtros(`?${campo}=ValorInvalido Para o Teste`)
		.then((response) => { this.response = response })
})
When('consulto um item de cadastro existente por UUID', function () {
	cy.consultar_itens_cadastros().then((lista) => {
		cy.consultar_itens_cadastros_uuid(lista.body.results[0].uuid).then((response) => {
			this.response = response
		})
	})
})
When('consulto um item de cadastro por UUID invalido', function () {
	cy.consultar_itens_cadastros_uuid('3ac751ee-f95d-4d5b-80da-437506b1906j')
		.then((response) => { this.response = response })
})
When('consulto a lista de nomes dos itens de cadastros', function () {
	cy.consultar_itens_cadastros_lista_nomes().then((response) => { this.response = response })
})
When('consulto os tipos de itens de cadastros', function () {
	cy.consultar_itens_cadastros_tipos().then((response) => { this.response = response })
})
When('cadastro um item de cadastro valido', function () {
	const dados = item()
	cy.cadastrar_itens_cadastros(dados).then((response) => {
		this.response = response
		obterUuid(dados).then((uuid) => excluir(uuid, this))
	})
})
When('cadastro duas vezes o mesmo item de cadastro', function () {
	const dados = item('Item Existente')
	cy.cadastrar_itens_cadastros(dados).then((criado) => {
		expect(criado.status).to.eq(201)
		obterUuid(dados).then((uuid) => {
			cy.cadastrar_itens_cadastros(dados).then((response) => {
				this.response = response
				excluir(uuid, this)
			})
		})
	})
})
When('cadastro um item de cadastro com dados {string}', function (tipo) {
	const dados = tipo === 'tipo_invalido' ? { nome: nome('Tipo Invalido'), tipo: 'TIPO_INVALIDO' }
		: tipo === 'campos_vazios' ? { nome: '', tipo: '' } : {}
	cy.cadastrar_itens_cadastros(dados).then((response) => { this.response = response })
})
When('cadastro e excluo um item de cadastro', function () {
	const dados = item('DELETE')
	cy.cadastrar_itens_cadastros(dados).then((criado) => {
		expect(criado.status).to.eq(201)
		obterUuid(dados).then((uuid) => {
			cy.deletar_itens_cadastros(uuid).then((response) => { this.response = response })
		})
	})
})
When('excluo um item de cadastro por UUID invalido', function () {
	cy.deletar_itens_cadastros(uuidInvalido).then((response) => { this.response = response })
})
function atualizarDuplicado(contexto, metodo) {
	const base = item(`${metodo} Base`)
	const alvo = item(`${metodo} Alvo`)
	cy.cadastrar_itens_cadastros(base).then((criadoBase) => {
		expect(criadoBase.status).to.eq(201)
		obterUuid(base).then((uuidBase) => {
			cy.cadastrar_itens_cadastros(alvo).then((criadoAlvo) => {
				expect(criadoAlvo.status).to.eq(201)
				obterUuid(alvo).then((uuidAlvo) => {
					const comando = metodo === 'PUT' ? 'put_alterar_itens_cadastros' : 'patch_alterar_itens_cadastros'
					cy[comando](uuidAlvo, base).then((response) => {
						contexto.response = response
						excluir(uuidAlvo, contexto)
						excluir(uuidBase, contexto)
					})
				})
			})
		})
	})
}
function atualizar(contexto, metodo, tipo) {
	if (tipo === 'duplicado') return atualizarDuplicado(contexto, metodo)
	const original = item(metodo)
	cy.cadastrar_itens_cadastros(original).then((criado) => {
		expect(criado.status).to.eq(201)
		const dados = tipo === 'validos' ? { nome: nome(`Alterado ${metodo}`), tipo: original.tipo }
			: tipo === 'tipo_invalido' ? { nome: nome('Tipo Invalido'), tipo: 'TIPO_INVALIDO' }
				: tipo === 'campos_vazios' ? { nome: '', tipo: '' } : {}
		const comando = metodo === 'PUT' ? 'put_alterar_itens_cadastros' : 'patch_alterar_itens_cadastros'
		obterUuid(original).then((uuid) => {
			cy[comando](uuid, dados).then((response) => {
				contexto.response = response
				excluir(uuid, contexto)
			})
		})
	})
}
When('atualizo um item de cadastro por PUT com dados {string}', function (tipo) {
	atualizar(this, 'PUT', tipo)
})
When('atualizo um item de cadastro por PATCH com dados {string}', function (tipo) {
	atualizar(this, 'PATCH', tipo)
})
function validarItem(itemCadastro) {
	expect(itemCadastro).to.include.all.keys('uuid', 'nome', 'tipo', 'tipo_display')
}
Then('a lista de itens de cadastros retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarItem(this.response.body.results[0])
})
Then('o filtro de itens retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarItem(this.response.body.results[0])
})
Then('o filtro de itens retorna lista vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.be.an('array').and.empty
})
Then('o item de cadastro retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	validarItem(this.response.body)
})
Then('a operacao de item de cadastro retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('a lista de nomes retorna status 200 e resultados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
})
Then('os tipos de itens retornam dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	expect(this.response.body[0]).to.include.all.keys('tipo', 'tipo_display')
})
Then('o item de cadastro e criado e removido com sucesso', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body.tipo).to.be.oneOf(tipos)
	expect(this.exclusao.status).to.be.oneOf([204, 404])
})
Then('o segundo cadastro retorna status 400 e o item e removido', function () {
	expect(this.response.status).to.eq(400)
	expect(JSON.stringify(this.response.body)).to.contain('Item')
	expect(this.exclusao.status).to.be.oneOf([204, 404])
})
Then('o cadastro invalido do item retorna status 400', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.exist
})
Then('a exclusao do item retorna status 204', function () {
	expect(this.response.status).to.eq(204)
})
Then('a atualizacao valida do item retorna status 200 e realiza limpeza', function () {
	expect(this.response.status).to.eq(200)
	expect(this.exclusao.status).to.be.oneOf([204, 404])
})
Then('a atualizacao invalida do item retorna erro e realiza limpeza quando necessario', function () {
	expect([400, 404, 409]).to.include(this.response.status)
	expect(this.response.body).to.exist
	expect(this.exclusao.status).to.be.oneOf([204, 404])
})
