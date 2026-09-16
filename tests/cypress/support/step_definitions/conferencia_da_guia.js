import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const guia = '7ceb5d9f-4c90-42d8-b295-316c4aab3276'
let processamentoAguardado = false
function ontem() {
	const data = new Date()
	data.setDate(data.getDate() - 1)
	return data.toISOString().slice(0, 10)
}
function dados(tipo = 'validos') {
	const base = {
		guia, nome_motorista: `Motorista Teste ${Date.now()}${Cypress._.random(10, 99)}`,
		placa_veiculo: `AB${Cypress._.random(1000, 9999)}`,
		data_recebimento: ontem(), hora_recebimento: '11:00:00', eh_reposicao: true,
	}
	const alteracoes = {
		sem_placa: { placa_veiculo: '' }, sem_motorista: { nome_motorista: '' },
		sem_data: { data_recebimento: '' }, sem_hora: { hora_recebimento: '' },
		sem_guia: { guia: '' }, guia_invalida: { guia: 'sdfsdfsdfsdfsd' },
	}
	return { ...base, ...(alteracoes[tipo] || {}) }
}
function permissao(response) {
	expect(response.status).to.eq(403)
	expect(response.body.detail).to.not.be.empty
}
function excluir(uuid, contexto) {
	if (!uuid) return
	cy.excluir_conferencia_da_guia(uuid).then((response) => {
		expect([204, 403, 404]).to.include(response.status)
		contexto.exclusao = response
	})
}
Given('que estou autenticado como abastecimento para gerenciar conferencia da guia', () => {
	cy.autenticar_login(Cypress.env('usuario_abastecimento'), Cypress.env('senha'))
	if (!processamentoAguardado) {
		cy.wait(Cypress.env('wait_api_conferencia_da_guia') || 3000)
		processamentoAguardado = true
	}
})
When('consulto as conferencias da guia', function () {
	cy.consultar_conferencia_da_guia().then((response) => { this.response = response })
})
When('cadastro uma conferencia da guia com dados {string}', function (tipo) {
	cy.cadastrar_conferencia_da_guia(dados(tipo)).then((response) => {
		this.response = response
		if (tipo === 'validos' && response.status === 201) excluir(response.body.uuid, this)
	})
})
When('cadastro e excluo uma conferencia da guia', function () {
	cy.cadastrar_conferencia_da_guia(dados()).then((criada) => {
		if (criada.status === 403) return void (this.response = criada)
		cy.excluir_conferencia_da_guia(criada.body.uuid).then((response) => {
			this.response = response
		})
	})
})
When('excluo uma conferencia da guia por UUID invalido', function () {
	cy.excluir_conferencia_da_guia('2a69bc14-c0e8-43f8-b7d2-5cce299de')
		.then((response) => { this.response = response })
})
function atualizar(contexto, metodo, tipo) {
	cy.cadastrar_conferencia_da_guia(dados()).then((criada) => {
		if (criada.status === 403) return void (contexto.response = criada)
		const comando = metodo === 'PUT' ? 'alterar_conferencia_da_guia' : 'alterar_conferencia_da_guia_patch'
		cy[comando](dados(tipo), criada.body.uuid).then((response) => {
			contexto.response = response
			excluir(criada.body.uuid, contexto)
		})
	})
}
When('atualizo por PUT uma conferencia da guia com dados {string}', function (tipo) {
	atualizar(this, 'PUT', tipo)
})
When('atualizo por PATCH uma conferencia da guia com dados {string}', function (tipo) {
	atualizar(this, 'PATCH', tipo)
})
Then('a lista de conferencias retorna status permitido e dados validos', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return permissao(this.response)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (!this.response.body.results.length) return
	const item = this.response.body.results[0]
	expect(item.criado_por).to.include.all.keys(
		'uuid', 'cpf', 'nome', 'email', 'date_joined', 'registro_funcional',
		'tipo_usuario', 'cargo',
	)
	expect(item).to.include.all.keys(
		'criado_em', 'alterado_em', 'uuid', 'data_recebimento', 'hora_recebimento',
		'nome_motorista', 'placa_veiculo', 'eh_reposicao', 'guia',
	)
})
Then('o cadastro valido da conferencia retorna sucesso ou permissao e realiza limpeza', function () {
	expect([201, 403]).to.include(this.response.status)
	if (this.response.status === 403) return permissao(this.response)
	expect(this.response.body.criado_por).to.include.all.keys('cpf', 'tipo_usuario')
	expect(this.exclusao.status).to.be.oneOf([204, 403, 404])
})
Then('a conferencia invalida retorna erro no campo {string} ou permissao negada', function (campo) {
	expect([400, 403]).to.include(this.response.status)
	if (this.response.status === 403) return permissao(this.response)
	expect(this.response.body).to.have.property(campo)
	expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
Then('a exclusao da conferencia retorna status permitido', function () {
	expect([204, 403, 404]).to.include(this.response.status)
	if (this.response.status === 403) permissao(this.response)
})
Then('a exclusao invalida retorna status 403 ou 404', function () {
	expect([403, 404]).to.include(this.response.status)
	if (this.response.status === 403) permissao(this.response)
})
Then('a atualizacao valida da conferencia retorna sucesso ou permissao e realiza limpeza', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return permissao(this.response)
	expect(this.response.body.alterado_em).to.not.be.empty
	expect(this.exclusao.status).to.be.oneOf([204, 403, 404])
})
