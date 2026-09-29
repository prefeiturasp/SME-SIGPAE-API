import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
const quantidadeInicial = '0.01'
let criados = []
let cronogramasDisponiveis

function guardar(contexto, requisicao) {
	return requisicao.then((response) => {
		contexto.response = response
		if (response.status === 201 && response.body.uuid) {
			criados.push(response.body.uuid)
		}
		return response
	})
}

function listarCronogramas() {
	if (cronogramasDisponiveis) return cy.wrap(cronogramasDisponiveis, { log: false })
	return cy.consultar_cronogramas_ajuste_saldo_laudo().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.be.an('array').and.not.be.empty
		cronogramasDisponiveis = Cypress._.uniqBy(response.body, 'uuid')
		return cronogramasDisponiveis
	})
}

function buscarDocumento(cronogramas, indice = 0) {
	if (indice >= cronogramas.length) {
		throw new Error('Pre-condicao: nenhum documento com unidade de medida e saldo de pelo menos 1 foi encontrado em QA.')
	}
	const cronograma = cronogramas[indice]
	return cy.consultar_documentos_ajuste_saldo_laudo({ cronograma_uuid: cronograma.uuid })
		.then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body).to.be.an('array')
			const documento = response.body.find((item) => item.unidade_medida && Number(item.saldo_atual) >= 1)
			if (documento) return { documento, cronograma }
			return buscarDocumento(cronogramas, indice + 1)
		})
}

function prepararDocumento(contexto) {
	return listarCronogramas().then((cronogramas) => buscarDocumento(cronogramas))
		.then((dados) => {
			contexto.documento = dados.documento
			contexto.cronograma = dados.cronograma
			return dados
		})
}

function criarAjuste(contexto) {
	return prepararDocumento(contexto).then(() => guardar(contexto,
		cy.cadastrar_ajuste_saldo_laudo({
			documento_recebimento: contexto.documento.uuid,
			quantidade_descontada: quantidadeInicial,
		}),
	)).then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(201)
		expect(response.body.uuid).to.be.a('string').and.not.be.empty
		contexto.uuid = response.body.uuid
	})
}

function validarQuantidade(uuid, quantidade) {
	return cy.consultar_ajuste_saldo_laudo_por_uuid(uuid).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.uuid).to.eq(uuid)
		expect(Number(response.body.quantidade_descontada)).to.eq(Number(quantidade))
	})
}

Given('que estou autenticado como DILOG qualidade para ajuste de saldo do laudo', () => {
	criados = []
	cy.autenticar_login(Cypress.env('usuario_dilog_qualidade'), Cypress.env('senha'))
})

After({ tags: '@ajuste_saldo_laudo' }, () => {
	// Exclui apenas registros criados pelo cenario, inclusive se uma assercao falhar.
	for (const uuid of criados) {
		cy.excluir_ajuste_saldo_laudo(uuid).then((response) => {
			expect(response.status, `Limpeza do ajuste ${uuid}`).to.eq(204)
		})
	}
})

Given('que criei um ajuste de saldo para o cenario', function () {
	return criarAjuste(this)
})
When('cadastro um ajuste de saldo valido', function () {
	return criarAjuste(this)
})
When('consulto os ajustes de saldo com pagina {int} e tamanho {int}', function (page, page_size) {
	this.tamanho = page_size
	return guardar(this, cy.consultar_ajuste_saldo_laudo({ page, page_size }))
})
Then('a listagem de ajustes de saldo retorna dados paginados', function () {
	const { status, body } = this.response
	 expect(status).to.eq(200)
	 expect(body).to.include.all.keys('count', 'next', 'previous', 'results')
	 expect(body.count).to.be.a('number')
	 expect(body.results).to.be.an('array').and.have.length.at.most(this.tamanho)
	 body.results.forEach((item) => {
		expect(item).to.include.all.keys('uuid', 'numero_cronograma', 'produto', 'fornecedor', 'numero_laudo', 'unidade_medida', 'quantidade_descontada')
	 })
})
When('filtro os ajustes pelo cronograma do registro criado', function () {
	return guardar(this, cy.consultar_ajuste_saldo_laudo({ numero_cronograma: this.cronograma.numero }))
})
Then('todos os ajustes retornados pertencem ao cronograma informado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((item) => expect(item.numero_cronograma).to.eq(this.cronograma.numero))
})
Then('o ajuste e criado e pode ser consultado', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body.documento_recebimento).to.eq(`${this.cronograma.numero} - Laudo: ${this.documento.numero_laudo}`)
	return validarQuantidade(this.uuid, quantidadeInicial)
})
When('consulto o ajuste de saldo criado por UUID', function () {
	return guardar(this, cy.consultar_ajuste_saldo_laudo_por_uuid(this.uuid))
})
Then('o detalhe do ajuste de saldo corresponde ao registro criado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include({ uuid: this.uuid, numero_cronograma: this.cronograma.numero, numero_laudo: this.documento.numero_laudo, unidade_medida: this.documento.unidade_medida })
	expect(Number(this.response.body.quantidade_descontada)).to.eq(Number(quantidadeInicial))
})
When('cadastro um ajuste de saldo com {string}', function (caso) {
	const dados = { documento_recebimento: inexistente, quantidade_descontada: quantidadeInicial }
	if (caso === 'documento ausente') delete dados.documento_recebimento
	if (caso === 'documento invalido') dados.documento_recebimento = 'uuid-invalido'
	if (caso === 'quantidade ausente') delete dados.quantidade_descontada
	if (caso === 'quantidade invalida') dados.quantidade_descontada = 'invalida'
	if (caso === 'casas decimais') dados.quantidade_descontada = '0.001'
	return guardar(this, cy.cadastrar_ajuste_saldo_laudo(dados))
})
When('cadastro um ajuste com desconto maior que o saldo disponivel', function () {
	return prepararDocumento(this).then(() => guardar(this, cy.cadastrar_ajuste_saldo_laudo({
		documento_recebimento: this.documento.uuid,
		quantidade_descontada: (Number(this.documento.saldo_atual) + 1).toFixed(2),
	})))
})
Then('o ajuste de saldo retorna erro no campo {string}', function (campo) {
	expect(this.response.status, `Esperado erro de validacao em ${campo}`).to.eq(400)
	expect(this.response.body).to.have.property(campo).that.is.not.empty
})
When('executo {string} em um ajuste de saldo inexistente', function (metodo) {
	const comandos = {
		PUT: () => cy.atualizar_ajuste_saldo_laudo(inexistente, {}),
		DELETE: () => cy.excluir_ajuste_saldo_laudo(inexistente),
	}
	return guardar(this, comandos[metodo]())
})
Then('a operacao de ajuste de saldo retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	// As respostas 404 observadas em QA chegam como uma pagina HTML.
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
When('envio PUT com outra quantidade para o ajuste criado', function () {
	return guardar(this, cy.atualizar_ajuste_saldo_laudo(this.uuid, { quantidade_descontada: '0.02' }))
})
Then('o PUT retorna sucesso e preserva a quantidade somente de leitura', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
	expect(Number(this.response.body.quantidade_descontada)).to.eq(Number(quantidadeInicial))
	return validarQuantidade(this.uuid, quantidadeInicial)
})
When('atualizo a quantidade do ajuste criado por PATCH', function () {
	return guardar(this, cy.atualizar_ajuste_saldo_laudo_patch(this.uuid, { quantidade_descontada: '0.02' }))
})
Then('a quantidade do ajuste e atualizada e persistida', function () {
	expect(this.response.status).to.eq(200)
	expect(Number(this.response.body.quantidade_descontada)).to.eq(0.02)
	return validarQuantidade(this.uuid, '0.02')
})
When('envio PATCH de ajuste de saldo com {string}', function (caso) {
	const dados = {
		'quantidade ausente': {},
		'quantidade invalida': { quantidade_descontada: 'invalida' },
		'saldo insuficiente': { quantidade_descontada: (Number(this.documento.saldo_atual) + 1).toFixed(2) },
	}
	return guardar(this, cy.atualizar_ajuste_saldo_laudo_patch(this.uuid, dados[caso]))
})
Then('a quantidade original do ajuste permanece inalterada', function () {
	return validarQuantidade(this.uuid, quantidadeInicial)
})
When('excluo o ajuste de saldo criado', function () {
	return guardar(this, cy.excluir_ajuste_saldo_laudo(this.uuid)).then((response) => {
		if (response.status === 204) criados = criados.filter((uuid) => uuid !== this.uuid)
	})
})
Then('o ajuste e excluido e uma segunda exclusao retorna 404', function () {
	expect(this.response.status).to.eq(204)
	return cy.excluir_ajuste_saldo_laudo(this.uuid).then((response) => expect(response.status).to.eq(404))
})
When('consulto os cronogramas mensais para ajuste de saldo', function () {
	return guardar(this, cy.consultar_cronogramas_ajuste_saldo_laudo())
})
Then('os cronogramas de ajuste de saldo possuem os campos esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	this.response.body.forEach((item) => expect(item).to.include.all.keys('uuid', 'numero', 'produto_nome', 'fornecedor_nome', 'numero_contrato'))
})
When('consulto documentos de um cronograma disponivel para ajuste', function () {
	return prepararDocumento(this).then(() => guardar(this,
		cy.consultar_documentos_ajuste_saldo_laudo({ cronograma_uuid: this.cronograma.uuid }),
	))
})
Then('os documentos do cronograma possuem os dados de saldo', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.be.an('array').and.not.be.empty
	this.response.body.forEach((item) => {
		expect(item).to.include.all.keys('uuid', 'numero_laudo', 'quantidade_laudo', 'saldo_atual')
		expect(item.saldo_atual).to.be.a('number')
	})
})
When('consulto documentos de ajuste sem informar cronograma', function () {
	return guardar(this, cy.consultar_documentos_ajuste_saldo_laudo())
})
When('consulto documentos de ajuste de cronograma inexistente', function () {
	return guardar(this, cy.consultar_documentos_ajuste_saldo_laudo({ cronograma_uuid: inexistente }))
})
Then('a consulta de documentos de ajuste retorna {int} com mensagem {string}', function (status, mensagem) {
	expect(this.response.status).to.eq(status)
	expect(this.response.body.detail).to.eq(mensagem)
})
When('acesso {string} de ajuste de saldo sem autenticacao', function (rota) {
	const comandos = {
		listar: () => cy.consultar_ajuste_saldo_laudo({}, false),
		cadastrar: () => cy.cadastrar_ajuste_saldo_laudo({}, false),
		detalhar: () => cy.consultar_ajuste_saldo_laudo_por_uuid(inexistente, false),
		atualizar: () => cy.atualizar_ajuste_saldo_laudo(inexistente, {}, false),
		parcial: () => cy.atualizar_ajuste_saldo_laudo_patch(inexistente, {}, false),
		excluir: () => cy.excluir_ajuste_saldo_laudo(inexistente, false),
		cronogramas: () => cy.consultar_cronogramas_ajuste_saldo_laudo(false),
		documentos: () => cy.consultar_documentos_ajuste_saldo_laudo({}, false),
	}
	return guardar(this, comandos[rota]())
})
When('consulto ajustes de saldo como diretor de escola', function () {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
	return guardar(this, cy.consultar_ajuste_saldo_laudo())
})
