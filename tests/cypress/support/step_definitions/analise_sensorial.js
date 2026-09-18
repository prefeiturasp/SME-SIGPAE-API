import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'

function validarPaginacao(response) {
	expect(response.body).to.have.property('count')
	expect(response.body).to.have.property('next')
	expect(response.body).to.have.property('previous')
	expect(response.body).to.have.property('results').that.is.an('array')
}

function validarAnaliseSensorial(analiseSensorial) {
	expect(analiseSensorial).to.have.property('homologacao_produto')
	expect(analiseSensorial).to.have.property('data')
	expect(analiseSensorial).to.have.property('hora')
	expect(analiseSensorial).to.have.property('anexos').that.is.an('array')
	expect(analiseSensorial).to.have.property('responsavel_produto')
	expect(analiseSensorial).to.have.property('registro_funcional')
	expect(analiseSensorial).to.have.property('observacao')

	if (analiseSensorial.anexos.length > 0) {
		expect(analiseSensorial.anexos[0]).to.have.property('nome')
	}
}

function validarResposta(response) {
	expect(response.status).to.eq(200)
	validarPaginacao(response)

	if (response.body.results.length > 0) {
		validarAnaliseSensorial(response.body.results[0])
	}
}

Given('que estou autenticado para consultar analises sensoriais', () => {
	cy.autenticar_login(Cypress.env('usuario_gpcodae'), Cypress.env('senha'))
})

When('consulto todas as analises sensoriais', function () {
	cy.consultar_analise_sensorial().then((response) => {
		this.response = response
	})
})

When('consulto analises sensoriais com filtro {string}', function (filtro) {
	cy.consultar_analise_sensorial_com_filtros(filtro).then((response) => {
		this.response = response
	})
})

Then('deve retornar a lista paginada de analises sensoriais', function () {
	validarResposta(this.response)
})

Then(
	'deve retornar no maximo {int} analise sensorial paginada',
	function (limite) {
		validarResposta(this.response)
		expect(this.response.body.results.length).to.be.at.most(limite)
	},
)

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

function identificarCriada(contexto) {
	return cy.consultar_referencia_analise_sensorial().then((homologacao) => {
		const resposta = homologacao.resposta_analise
		expect(homologacao.uuid).to.eq(contexto.dados.homologacao_produto)
		expect(resposta.observacao, 'Identificar somente registro criado pelo teste').to.eq(contexto.dados.observacao)
		expect(resposta.uuid).to.be.a('string').and.not.be.empty
		contexto.uuidCriada = resposta.uuid
	})
}

When('consulto uma analise sensorial existente por UUID', function () {
	cy.consultar_referencia_analise_sensorial().then((homologacao) => {
		this.referencia = homologacao.resposta_analise
		expect(this.referencia.uuid).to.be.a('string').and.not.be.empty
		cy.requisitar_analise_sensorial('GET', `${this.referencia.uuid}/`).then((response) => {
			this.response = response
		})
	})
})

Then('deve retornar a analise sensorial solicitada', function () {
	expect(this.response.status).to.eq(200)
	validarAnaliseSensorial(this.response.body)
	expect(this.response.body.registro_funcional).to.eq(this.referencia.registro_funcional)
	expect(this.response.body.observacao).to.eq(this.referencia.observacao)
})

When('cadastro uma analise sensorial de teste', function () {
	cy.consultar_referencia_analise_sensorial().then((homologacao) => {
		this.dados = {
			homologacao_produto: homologacao.uuid,
			data: new Date().toISOString().slice(0, 10),
			hora: '10:00:00',
			responsavel_produto: 'Automacao Cypress',
			registro_funcional: 'TESTE',
			observacao: `Automacao sensorial ${Date.now()}-${Cypress._.random(100000, 999999)}`,
		}
		cy.requisitar_analise_sensorial('POST', '', this.dados).then((response) => {
			this.response = response
			this.cadastroRealizado = response.status === 201
			expect(response.status).to.eq(201)
			identificarCriada(this)
		})
	})
})

Then('a analise sensorial de teste deve ser criada e consultavel', function () {
	cy.requisitar_analise_sensorial('GET', `${this.uuidCriada}/`).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.include({ ...this.dados, data: this.dados.data.split('-').reverse().join('/') })
	})
})

When('atualizo a analise sensorial de teste usando {string}', function (metodo) {
	this.observacaoAtualizada = `${this.dados.observacao} ${metodo}`
	const dados = metodo === 'PUT'
		? { ...this.dados, observacao: this.observacaoAtualizada }
		: { observacao: this.observacaoAtualizada }
	cy.requisitar_analise_sensorial(metodo, `${this.uuidCriada}/`, dados).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.observacao).to.eq(this.observacaoAtualizada)
	})
})

Then('a alteracao da analise sensorial deve estar persistida', function () {
	cy.requisitar_analise_sensorial('GET', `${this.uuidCriada}/`).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.observacao).to.eq(this.observacaoAtualizada)
	})
})

When('excluo a analise sensorial de teste', function () {
	cy.requisitar_analise_sensorial('DELETE', `${this.uuidCriada}/`).then((response) => {
		expect(response.status).to.eq(204)
		this.cadastroRealizado = false
	})
})

Then('a analise sensorial excluida nao deve ser encontrada', function () {
	cy.requisitar_analise_sensorial('GET', `${this.uuidCriada}/`).its('status').should('eq', 404)
})

After({ tags: '@ciclo_analise_sensorial' }, function () {
	if (!this.cadastroRealizado) return
	if (!this.uuidCriada) identificarCriada(this)
	cy.then(() => {
		cy.requisitar_analise_sensorial('DELETE', `${this.uuidCriada}/`).its('status').should('eq', 204)
	})
})

When('cadastro analise sensorial invalida no campo {string}', function (campo) {
	// Todos os payloads permanecem invalidos e nao geram registros.
	const invalidos = {
		homologacao_produto: uuidInexistente,
		data: 'data-invalida',
		hora: '25:99:99',
		responsavel_produto: '',
		registro_funcional: '12345678901',
	}
	cy.requisitar_analise_sensorial('POST', '', { [campo]: invalidos[campo] }).then((response) => {
		this.response = response
	})
})

Then('a analise sensorial deve retornar erro 400 no campo {string}', function (campo) {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.have.property(campo).that.is.an('array').and.not.be.empty
})

When('executo {string} para analise sensorial inexistente', function (metodo) {
	cy.requisitar_analise_sensorial(metodo, `${uuidInexistente}/`, ['PUT', 'PATCH'].includes(metodo) ? {} : undefined).then((response) => {
		this.response = response
	})
})

When('executo {string} no caminho sensorial {string} sem autenticacao', function (metodo, caminho) {
	cy.clearCookies()
	cy.requisitar_analise_sensorial(metodo, caminho, ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined, false).then((response) => {
		this.response = response
	})
})

When('respondo analise sensorial com perfil CODAE', function () {
	cy.requisitar_analise_sensorial('POST', 'terceirizada-responde-analise-sensorial/', { anexos: [] }).then((response) => {
		this.response = response
	})
})

Then('a operacao de analise sensorial deve retornar {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('tento atualizar a analise sensorial de teste com data invalida usando {string}', function (metodo) {
	const dados = metodo === 'PUT' ? { ...this.dados, data: 'invalida' } : { data: 'invalida' }
	cy.requisitar_analise_sensorial(metodo, `${this.uuidCriada}/`, dados).then((response) => {
		this.response = response
	})
})
