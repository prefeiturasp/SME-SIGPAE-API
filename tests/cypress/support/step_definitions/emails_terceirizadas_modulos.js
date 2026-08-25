import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function dataHoraValida(valor) {
	if (!Number.isNaN(Date.parse(valor))) return true

	const partes = valor.match(
		/^(\d{2})\/(\d{2})\/(\d{4}) (\d{2}):(\d{2}):(\d{2})$/,
	)
	if (!partes) return false

	const [, dia, mes, ano, hora, minuto, segundo] = partes.map(Number)
	const data = new Date(ano, mes - 1, dia, hora, minuto, segundo)

	return (
		data.getFullYear() === ano &&
		data.getMonth() === mes - 1 &&
		data.getDate() === dia &&
		data.getHours() === hora &&
		data.getMinutes() === minuto &&
		data.getSeconds() === segundo
	)
}

function validarListaPaginada(response) {
	expect(response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(response.body.count).to.be.a('number').and.at.least(0)
	expect(response.body.results).to.be.an('array')

	response.body.results.forEach((registro) => {
		expect(registro).to.include.all.keys(
			'modulo',
			'terceirizada',
			'uuid',
			'email',
			'criado_em',
		)
		expect(registro.modulo).to.be.a('string')
		expect(registro.terceirizada).to.be.a('string')
		expect(registro.uuid).to.be.a('string').and.not.be.empty
		expect(registro.email).to.be.a('string').and.not.be.empty
		expect(registro.criado_em).to.be.a('string').and.not.be.empty
	})
}

Given(
	'que estou autenticado como CODAE para consultar emails de terceirizadas por modulo',
	() => {
		cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
	},
)

When('consulto os emails de terceirizadas por modulo', function () {
	cy.consultar_emails_terceirizadas_modulos().then((response) => {
		this.response = response
	})
})

When(
	'consulto os emails de terceirizadas com limite {int} modulo {string} e deslocamento {int}',
	function (limit, modulo, offset) {
		this.parametros = { limit, modulo, offset }
		cy.consultar_emails_terceirizadas_modulos(this.parametros).then(
			(response) => {
				this.response = response
			},
		)
	},
)

When(
	'consulto os emails de terceirizadas por modulo sem autenticacao',
	function () {
		cy.consultar_emails_terceirizadas_modulos(undefined, false).then(
			(response) => {
				this.response = response
			},
		)
	},
)

When(
	'cadastro um email de terceirizada usando os dados da consulta',
	function () {
		cy.consultar_emails_terceirizadas_modulos().then((consulta) => {
			expect(consulta.status, JSON.stringify(consulta.body)).to.eq(200)
			expect(consulta.body.results).to.be.an('array').and.not.be.empty

			const registro = consulta.body.results[0]
			cy.consultar_terceirizadas_por_nome(registro.terceirizada).then(
				(terceirizadas) => {
					expect(terceirizadas.status, JSON.stringify(terceirizadas.body)).to.eq(
						200,
					)
					expect(terceirizadas.body.results).to.be.an('array').and.not.be.empty

					this.dadosCadastro = {
						terceirizada: terceirizadas.body.results[0].uuid,
						modulo: registro.modulo,
						criado_por: 'Automacao Cypress',
						email: `automacao.${Date.now()}@example.com`,
					}

					cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then(
						(response) => {
							this.response = response
						},
					)
				},
			)
		})
	},
)

Then(
	'a consulta retorna status 200 e uma lista paginada valida',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
		validarListaPaginada(this.response)
	},
)

Then(
	'a consulta filtrada retorna status 200 e respeita o limite informado',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
		validarListaPaginada(this.response)
		expect(this.response.body.results).to.have.length.at.most(
			this.parametros.limit,
		)

		this.response.body.results.forEach((registro) => {
			expect(String(registro.modulo)).to.eq(this.parametros.modulo)
		})
	},
)

Then(
	'a consulta de emails de terceirizadas retorna status 401',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(401)
		expect(this.response.body).to.have.property('detail').that.is.a('string').and
			.not.be.empty
	},
)

Then(
	'o email de terceirizada por modulo e cadastrado com sucesso',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(201)
		expect(this.response.body).to.include({
			terceirizada: this.dadosCadastro.terceirizada,
			modulo: this.dadosCadastro.modulo,
			email: this.dadosCadastro.email,
		})
		expect(this.response.body).to.have.property('criado_por').that.is.a('string')
			.and.not.be.empty
		expect(this.response.body).to.have.property('uuid').that.is.a('string').and
			.not.be.empty
		expect(this.response.body).to.have.property('criado_em').that.is.a('string')
		expect(dataHoraValida(this.response.body.criado_em)).to.eq(true)
	},
)
