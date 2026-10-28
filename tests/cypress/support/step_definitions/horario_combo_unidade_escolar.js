import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const hora = /^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d(\.\d{1,6})?)?$/

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.executar_horario_combo_unidade_escolar(opcoes).then((response) => { contexto.response = response })
}

function validarHorario(horario) {
	expect(horario.uuid).to.match(uuid)
	expect(horario.hora_inicial).to.match(hora)
	expect(horario.hora_final).to.match(hora)
	for (const campo of ['escola', 'tipo_alimentacao', 'periodo_escolar']) {
		expect(horario[campo]).to.be.an('object')
		expect(horario[campo].uuid).to.match(uuid)
	}
}

function obterReferencia(contexto) {
	return cy.executar_horario_combo_unidade_escolar({ qs: { limit: 1 } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'horario disponivel em QA').to.be.an('array').and.not.be.empty
		contexto.horarioReferencia = response.body.results[0]
		validarHorario(contexto.horarioReferencia)
	})
}

When('consulto a listagem de horarios do combo por unidade escolar', function () {
	return autenticar().then(() => consultar(this, { qs: { limit: 2 } }))
})

Then('horarios do combo retorna uma lista paginada valida', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarHorario)
})

When('consulto o detalhe de um horario do combo existente', function () {
	return autenticar().then(() => obterReferencia(this)).then(() => consultar(this, { caminho: this.horarioReferencia.uuid + '/' }))
})

Then('o detalhe do horario do combo corresponde ao registro consultado', function () {
	validarHorario(this.response.body)
	expect(this.response.body).to.deep.eq(this.horarioReferencia)
})

When('consulto horarios do combo por escola {string}', function (escola) {
	return autenticar().then(() => {
		if (escola === 'inexistente') return consultar(this, { caminho: 'escola/' + inexistente + '/', qs: { limit: 2 } })
		return obterReferencia(this).then(() => consultar(this, {
			caminho: 'escola/' + this.horarioReferencia.escola.uuid + '/', qs: { limit: 2 },
		}))
	})
})

Then('os horarios do combo pertencem a escola consultada', function () {
	expect(this.response.body.results).not.to.be.empty
	this.response.body.results.forEach((horario) => {
		expect(horario.escola.uuid).to.eq(this.horarioReferencia.escola.uuid)
	})
})

Then('horarios do combo retorna uma lista vazia', function () {
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
})

When('executo {string} em horarios do combo na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = {
		method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('horarios do combo retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('horarios do combo informa os campos obrigatorios', function () {
	for (const campo of ['hora_inicial', 'hora_final', 'escola', 'tipo_alimentacao', 'periodo_escolar']) {
		expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})
