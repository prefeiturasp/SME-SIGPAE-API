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

Given(
	'que estou autenticado como CODAE para consultar emails de terceirizadas por modulo',
	() => {
		cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
	},
)

When('cadastro um email de terceirizada por modulo', function () {
	cy.consultar_terceirizadas().then((terceirizadas) => {
		expect(terceirizadas.status, JSON.stringify(terceirizadas.body)).to.eq(200)
		expect(terceirizadas.body.results).to.be.an('array').and.not.be.empty

		this.dadosCadastro = {
			terceirizada: terceirizadas.body.results[0].uuid,
			modulo: 'Gestão de Alimentação',
			criado_por: 'Automacao Cypress',
			email: `automacao.${Date.now()}@example.com`,
		}

		cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then(
			(response) => {
				this.response = response
			},
		)
	})
})

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

When('atualizo um email de terceirizada por modulo', function () {
	cy.consultar_terceirizadas().then((terceirizadas) => {
		expect(terceirizadas.status, JSON.stringify(terceirizadas.body)).to.eq(200)
		expect(terceirizadas.body.results).to.be.an('array').and.not.be.empty

		this.dadosCadastro = {
			terceirizada: terceirizadas.body.results[0].uuid,
			modulo: 'Gestão de Alimentação',
			criado_por: 'Automacao Cypress',
			email: `automacao.${Date.now()}@example.com`,
		}

		cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then(
			(criacao) => {
				expect(criacao.status, JSON.stringify(criacao.body)).to.eq(201)

				this.dadosAtualizacao = {
					email: `automacao.atualizado.${Date.now()}@example.com`,
				}
				cy.atualizar_email_terceirizada_modulo(
					criacao.body.uuid,
					this.dadosAtualizacao,
				).then((response) => {
					this.response = response
				})
			},
		)
	})
})

Then(
	'o email de terceirizada por modulo e atualizado com sucesso',
	function () {
		expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
		expect(this.response.body).to.include({
			terceirizada: this.dadosCadastro.terceirizada,
			modulo: this.dadosCadastro.modulo,
			email: this.dadosAtualizacao.email,
		})
		expect(this.response.body).to.have.property('uuid').that.is.a('string').and
			.not.be.empty
		expect(this.response.body).to.have.property('criado_em').that.is.a('string')
	},
)