import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const textoExtenso =
	'12345645655654565256556565656252545856545656565656123456456556545652565565656562525458565456565656511'

const alimentoBase = {
	codigo_suprimento: 'teste automatizado',
	codigo_papa: 't a',
	nome_alimento: 'Teste Batatinha',
	guia: 8159,
}

const alimentoAlterado = {
	codigo_suprimento: 'Alteracao automatizado',
	codigo_papa: 'a a',
	nome_alimento: 'Teste Batatinha Alteracao',
	guia: 8160,
}

function dadosInvalidos(caso) {
	const alimento = { ...alimentoBase }

	const alteracoes = {
		codigo_suprimento_extenso: { codigo_suprimento: textoExtenso },
		codigo_papa_extenso: {
			codigo_suprimento: '1010101010',
			codigo_papa: '12312312312',
		},
		nome_alimento_extenso: { nome_alimento: textoExtenso },
		guia_texto: { guia: 'a' },
		guia_inexistente: { guia: '1' },
	}

	expect(alteracoes, `Caso invalido nao mapeado: ${caso}`).to.have.property(caso)
	return { ...alimento, ...alteracoes[caso] }
}

function validarCamposDoAlimento(alimento) {
	expect(alimento).to.have.property('alterado_em').that.exist
	expect(alimento).to.have.property('codigo_papa').that.exist
	expect(alimento).to.have.property('codigo_suprimento').that.exist
	expect(alimento).to.have.property('criado_em').that.exist
	expect(alimento).to.have.property('guia').that.exist
	expect(alimento).to.have.property('nome_alimento').that.exist
	expect(alimento).to.have.property('uuid').that.exist
}

function validarErro(response, caso) {
	const erros = {
		codigo_suprimento_extenso: {
			campo: 'codigo_suprimento',
			mensagem: 'Certifique-se de que este campo nao tenha mais de 100 caracteres.',
		},
		codigo_papa_extenso: {
			campo: 'codigo_papa',
			mensagem: 'Certifique-se de que este campo nao tenha mais de 10 caracteres.',
		},
		nome_alimento_extenso: {
			campo: 'nome_alimento',
			mensagem: 'Certifique-se de que este campo nao tenha mais de 100 caracteres.',
		},
		guia_texto: {
			campo: 'guia',
			mensagem: 'Tipo incorreto. Esperava valor pk, recebeu str.',
		},
		guia_inexistente: {
			campo: 'guia',
			mensagem: 'Pk invalido "1" - objeto nao existe.',
		},
	}

	const erro = erros[caso]
	expect(erro, `Erro nao mapeado: ${caso}`).to.exist
	expect(response.status).to.eq(400)
	const mensagemRecebida = response.body[erro.campo][0]
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
	expect(mensagemRecebida).to.eq(erro.mensagem)
}

function validarRedirecionamento(response) {
	expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
	expect(response.status).to.eq(200)
	expect(response.body).to.exist
	expect(response.redirects[0]).to.contain('301:')
	expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
	expect(response.redirects).to.be.an('array').that.is.not.empty
}

function excluirAlimento(uuid) {
	cy.excluir_alimentos_da_guia(uuid)
}

Given('que estou autenticado para gerenciar alimentos da guia', () => {
	cy.autenticar_login(
		Cypress.config('usuario_coordenador_codae_dilog_logistica'),
		Cypress.config('senha'),
	)
})

Given('que existe um alimento da guia para alteracao', function () {
	cy.cadastrar_alimentos_da_guia(alimentoBase).then((response) => {
		expect(response.status).to.eq(201)
		this.alimentoUuid = response.body.uuid
	})
})

When('consulto todos os alimentos da guia', function () {
	cy.validar_alimentos_da_guia('').then((response) => {
		this.response = response
	})
})

When('consulto alimentos da guia com limit 4 e offset 5', function () {
	cy.validar_alimentos_da_guia('?limit=4&offset=5').then((response) => {
		this.response = response
	})
})

When(
	'consulto alimentos da guia pelo caminho invalido {string}',
	function (caminho) {
		cy.validar_alimentos_da_guia(caminho).then((response) => {
			this.response = response
		})
	},
)

When('um diretor de UE consulta todos os alimentos da guia', function () {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
	cy.validar_alimentos_da_guia('').then((response) => {
		this.response = response
	})
})

When('consulto o alimento da guia de UUID {string}', function (uuid) {
	cy.validar_alimentos_da_guia(`${uuid}/`).then((response) => {
		this.response = response
	})
})

When('cadastro um alimento da guia com dados validos', function () {
	cy.cadastrar_alimentos_da_guia(alimentoBase).then((response) => {
		this.response = response
	})
})

When(
	'tento cadastrar um alimento da guia com {string} invalido',
	function (caso) {
		cy.cadastrar_alimentos_da_guia(dadosInvalidos(caso)).then((response) => {
			this.response = response
			this.casoInvalido = caso
		})
	},
)

When('cadastro e excluo um alimento da guia', function () {
	cy.cadastrar_alimentos_da_guia(alimentoBase).then((cadastro) => {
		expect(cadastro.status).to.eq(201)
		cy.excluir_alimentos_da_guia(cadastro.body.uuid).then((response) => {
			this.response = response
		})
	})
})

When('excluo um alimento da guia sem informar UUID', function () {
	cy.excluir_alimentos_da_guia('').then((response) => {
		this.response = response
	})
})

When('excluo o alimento da guia de UUID inexistente', function () {
	cy.excluir_alimentos_da_guia('5e141551-d242-482c-b74a-64e7e7efeb24').then(
		(response) => {
			this.response = response
		},
	)
})

When('altero o alimento da guia via PUT com dados validos', function () {
	cy.alterar_alimentos_da_guia(this.alimentoUuid, alimentoAlterado).then(
		(response) => {
			this.response = response
		},
	)
})

When('altero o alimento da guia via PATCH com dados validos', function () {
	cy.alterar_alimentos_da_guia_patch(this.alimentoUuid, alimentoAlterado).then(
		(response) => {
			this.response = response
		},
	)
})

When(
	'tento alterar o alimento da guia via PUT com {string} invalido',
	function (caso) {
		cy.alterar_alimentos_da_guia(
			this.alimentoUuid,
			dadosInvalidos(caso),
		).then((response) => {
			this.response = response
			this.casoInvalido = caso
		})
	},
)

When(
	'tento alterar o alimento da guia via PATCH com {string} invalido',
	function (caso) {
		cy.alterar_alimentos_da_guia_patch(
			this.alimentoUuid,
			dadosInvalidos(caso),
		).then((response) => {
			this.response = response
			this.casoInvalido = caso
		})
	},
)

When('consulto a lista de nomes dos alimentos da guia', function () {
	cy.Validar_lista_de_nomes_alimentos_da_guia().then((response) => {
		this.response = response
	})
})

Then('a consulta de alimentos da guia deve retornar uma lista paginada', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('count').that.exist
	expect(this.response.body).to.have.property('next').that.exist
	expect(this.response.body).to.have.property('previous')
	expect(this.response.body).to.have.property('results').that.is.an('array').and.not
		.to.be.empty
	validarCamposDoAlimento(this.response.body.results[0])
})

Then(
	'a API de alimentos da guia deve redirecionar para o caminho com barra final',
	function () {
		validarRedirecionamento(this.response)
	},
)

Then('a consulta de alimentos da guia deve retornar permissao negada', function () {
	expect(this.response.status).to.eq(403)
	expect(this.response.body).to.have.property('detail').that.is.a('string').and.not
		.to.be.empty
})

Then('deve retornar os dados do alimento da guia com status 200', function () {
	expect(this.response.status).to.eq(200)
	validarCamposDoAlimento(this.response.body)
})

Then('o alimento da guia deve ser cadastrado com sucesso', function () {
	expect(this.response.status).to.eq(201)
	validarCamposDoAlimento(this.response.body)
	expect(this.response.body.codigo_papa).to.eq(alimentoBase.codigo_papa)
	expect(this.response.body.codigo_suprimento).to.eq(
		alimentoBase.codigo_suprimento,
	)
	expect(this.response.body.guia).to.eq(alimentoBase.guia)
	excluirAlimento(this.response.body.uuid)
})

Then(
	'o cadastro deve ser rejeitado por {string} invalido',
	function (caso) {
		expect(caso).to.eq(this.casoInvalido)
		validarErro(this.response, caso)
	},
)

Then('a exclusao do alimento da guia deve retornar status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})

Then('o alimento da guia deve ser alterado via PUT com sucesso', function () {
	expect(this.response.status).to.eq(200)
	validarCamposDoAlimento(this.response.body)
	expect(this.response.body.codigo_papa).to.eq(alimentoAlterado.codigo_papa)
	expect(this.response.body.codigo_suprimento).to.eq(
		alimentoAlterado.codigo_suprimento,
	)
	expect(this.response.body.nome_alimento).to.eq(alimentoAlterado.nome_alimento)
	expect(this.response.body.guia).to.eq(alimentoAlterado.guia)
	excluirAlimento(this.response.body.uuid)
})

Then('o alimento da guia deve ser alterado via PATCH com sucesso', function () {
	expect(this.response.status).to.eq(200)
	validarCamposDoAlimento(this.response.body)
	expect(this.response.body.codigo_papa).to.eq(alimentoAlterado.codigo_papa)
	expect(this.response.body.codigo_suprimento).to.eq(
		alimentoAlterado.codigo_suprimento,
	)
	expect(this.response.body.nome_alimento).to.eq(alimentoAlterado.nome_alimento)
	expect(this.response.body.guia).to.eq(alimentoAlterado.guia)
	excluirAlimento(this.response.body.uuid)
})

Then(
	'a alteracao deve ser rejeitada por {string} invalido',
	function (caso) {
		expect(caso).to.eq(this.casoInvalido)
		validarErro(this.response, caso)
		excluirAlimento(this.alimentoUuid)
	},
)

Then('deve retornar os nomes e UUIDs dos alimentos da guia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('results').that.is.an('array').and.not
		.to.be.empty
	const primeiroResultado = this.response.body.results[0]
	expect(primeiroResultado).to.have.property('nome_alimento').that.exist
	expect(primeiroResultado).to.have.property('uuid').that.exist
})
