import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

After({ tags: '@emails_modulos' }, function () {
	if (!this.emailModuloCriado) return
	cy.executar_email_terceirizada_modulo({ metodo: 'DELETE', uuid: this.emailModuloCriado }).then((response) => {
		expect(response.status, 'Limpeza do email criado pelo cenario').to.eq(204)
	})
})

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
		cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	},
)

When('cadastro um email de terceirizada por modulo', function () {
	cy.consultar_terceirizadas().then((terceirizadas) => {
		expect(terceirizadas.status, JSON.stringify(terceirizadas.body)).to.eq(200)
		expect(terceirizadas.body.results).to.be.an('array').and.not.be.empty

		this.dadosCadastro = {
			terceirizada: terceirizadas.body.results[0].uuid,
			modulo: 'Gestão de Alimentação',
			email: `automacao.${Date.now()}@example.com`,
		}

		cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then(
			(response) => {
				if (response.status === 201) this.emailModuloCriado = response.body.uuid
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
			email: `automacao.${Date.now()}@example.com`,
		}

		cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then(
			(criacao) => {
				if (criacao.status === 201) this.emailModuloCriado = criacao.body.uuid
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

When('excluo o email de terceirizada por modulo criado', function () {
	cy.executar_email_terceirizada_modulo({ metodo: 'DELETE', uuid: this.emailModuloCriado }).then((response) => {
		this.response = response
		if (response.status === 204) this.emailModuloCriado = undefined
	})
})

When('cadastro novamente o mesmo email de terceirizada por modulo', function () {
	cy.cadastrar_email_terceirizada_modulo(this.dadosCadastro).then((response) => { this.response = response })
})

When('envio cadastro de email de terceirizada por modulo sem campos obrigatorios', function () {
	cy.cadastrar_email_terceirizada_modulo({}).then((response) => { this.response = response })
})

When('atualizo o email de terceirizada por modulo com email invalido', function () {
	cy.atualizar_email_terceirizada_modulo(this.emailModuloCriado, { email: 'email-invalido' }).then((response) => { this.response = response })
})

When('cadastro email de terceirizada por modulo com email invalido', function () {
	cy.cadastrar_email_terceirizada_modulo({ ...this.dadosCadastro, email: 'email-invalido' }).then((response) => { this.response = response })
})

When('executo {string} em emails de terceirizadas por modulo na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	const autenticado = acesso === 'autenticado'
	if (!autenticado) cy.clearCookies()
	cy.executar_email_terceirizada_modulo({
		metodo,
		uuid: rota === 'detalhe' ? uuidInexistente : '',
		body: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined,
		autenticado,
	}).then((response) => { this.response = response })
})

Then('a operacao de emails de terceirizadas por modulo retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
})

Then('emails de terceirizadas por modulo informa erro no campo {string}', function (campo) {
	expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
