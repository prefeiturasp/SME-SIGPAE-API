import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const parametros = { ano: 2025, mes: 11 }

function consultar(usuario, contexto) {
	cy.consultar_dias_letivos({
		...parametros,
		usuario,
		senha: Cypress.env('senha'),
	}).then((response) => {
		contexto.response = response
	})
}

When('consulto os dias letivos com um usuario CODAE', function () {
	consultar(Cypress.env('usuario_codae'), this)
})

When('consulto os dias letivos com um usuario diretor de UE', function () {
	consultar(Cypress.env('usuario_diretor_ue'), this)
})

Then('a consulta de dias letivos retorna status 200 e uma lista valida', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((dia) => {
		expect(dia).to.have.all.keys(
			'uuid', 'data', 'lotes', 'tipos_unidade_escolar', 'periodos_escolares',
			'unidades_escolares', 'editais_numeros',
		)
		expect(dia.uuid).to.be.a('string').and.not.be.empty
		expect(dia.data).to.match(/^\d{4}-\d{2}-\d{2}$/)
		expect(dia.lotes).to.be.an('array')
		expect(dia.tipos_unidade_escolar).to.be.an('array')
		expect(dia.periodos_escolares).to.be.an('array')
		expect(dia.unidades_escolares).to.be.a('string')
		expect(dia.editais_numeros).to.be.a('string')
	})
})

Then('a consulta de dias letivos retorna status 403 e mensagem de permissao', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('executo {string} em dias letivos na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	const autenticado = acesso === 'autenticado'
	if (autenticado) cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	else cy.clearCookies()
	const caminho = rota === 'detalhe' ? '00000000-0000-0000-0000-000000000000' : rota === 'calendario' ? 'calendario' : ''
	cy.executar_dias_letivos(metodo, caminho, ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined, parametros, autenticado).then((response) => { this.response = response })
})

Then('a operacao de dias letivos retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('o cadastro de dias letivos informa campos obrigatorios', function () {
	for (const campo of ['recorrencias', 'lotes', 'tipos_unidades']) expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})

When('consulto o detalhe de um dia letivo existente', function () {
	cy.consultar_dias_letivos({ ano: new Date().getFullYear(), mes: new Date().getMonth() + 1, usuario: Cypress.env('usuario_codae'), senha: Cypress.env('senha') }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.be.an('array').and.not.be.empty
		this.diaConsultado = response.body[0]
		cy.executar_dias_letivos('GET', this.diaConsultado.uuid).then((resposta) => { this.response = resposta })
	})
})

Then('o detalhe de dias letivos corresponde ao UUID consultado', function () {
	expect(this.response.body.uuid).to.eq(this.diaConsultado.uuid)
	expect(this.response.body.data).to.eq(this.diaConsultado.data)
	expect(this.response.body).to.include.all.keys('lotes', 'tipos_unidades', 'unidades_educacionais', 'periodos_escolares')
})

Then('o calendario de dias letivos retorna uma lista', function () {
	expect(this.response.body).to.be.an('array')
})

When('consulto {string} de dias letivos sem filtros obrigatorios', function (rota) {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.executar_dias_letivos('GET', rota === 'calendario' ? 'calendario' : '').then((response) => { this.response = response })
})

Then('dias letivos informa os filtros obrigatorios', function () {
	for (const campo of ['ano', 'mes']) expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
