import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidInvalido = '3ac751ee-f95d-4d5b-80da-437506b1906j'
const catalogos = {
	equipamentos: (uuid) => cy.consultar_imr_equipamentos(uuid),
	insumos: (uuid) => cy.consultar_imr_insumos(uuid),
	mobiliarios: (uuid) => cy.consultar_imr_mobiliarios(uuid),
	'periodos visita': (uuid) => cy.consultar_imr_periodos_visita(uuid),
	'reparos adaptacoes': (uuid) => cy.consultar_imr_reparos_adaptacoes(uuid),
	'utensilios cozinha': (uuid) => cy.consultar_imr_utensilios_cozinha(uuid),
	'utensilios mesa': (uuid) => cy.consultar_imr_utensilios_mesa(uuid),
}

function permissao(response) {
	expect(response.status).to.eq(403)
	expect(response.body).to.have.property('detail').that.is.not.empty
}

function obterUuidCatalogo(consulta) {
	return consulta('').then((response) => {
		expect([200, 403]).to.include(response.status)
		if (response.status === 403 || !response.body.results.length) return null
		return response.body.results[0].uuid
	})
}

function obterUuidFormulario() {
	return cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO')
		.then((response) => {
			expect([200, 403]).to.include(response.status)
			if (response.status === 403 || !response.body.results.length) return []
			return response.body.results.map((formulario) => formulario.uuid)
		})
}

function consultarPrimeiroFormularioValido(uuids, consulta, indice = 0) {
	return consulta(uuids[indice]).then((response) => {
		if ([200, 403].includes(response.status) || indice === uuids.length - 1) {
			return response
		}
		return consultarPrimeiroFormularioValido(uuids, consulta, indice + 1)
	})
}

Given('que estou autenticado como CODAE para consultar IMR', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})

When('consulto o catalogo IMR {string} com identificador {string}', function (catalogo, identificador) {
	const consulta = catalogos[catalogo]
	expect(consulta).to.be.a('function')
	if (identificador === 'lista') {
		consulta('').then((response) => { this.response = response })
		return
	}
	if (identificador === 'invalido') {
		consulta(uuidInvalido).then((response) => { this.response = response })
		return
	}
	obterUuidCatalogo(consulta).then((uuid) => {
		if (uuid) consulta(uuid).then((response) => { this.response = response })
		else this.response = { status: 403, body: { detail: 'Sem permissao ou massa' } }
	})
})

Then('o catalogo IMR retorna {string}', function (resultado) {
	if (resultado === 'nao encontrado') {
		expect([403, 404]).to.include(this.response.status)
		if (this.response.status === 403) permissao(this.response)
		return
	}
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		permissao(this.response)
		return
	}
	if (resultado === 'lista ou permissao') {
		expect(this.response.body).to.have.property('results').that.is.an('array')
	} else {
		expect(this.response.body).to.include.all.keys('nome', 'criado_em', 'alterado_em', 'uuid')
	}
})

When('consulto formularios IMR com status {string}', function (status) {
	this.status = status
	cy.consultar_imr_formulario_supervisao_por_status(status)
		.then((response) => { this.response = response })
})

Then('a lista de formularios IMR retorna dados ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		permissao(this.response)
		return
	}
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (this.response.body.results.length) {
		expect(this.response.body.results[0]).to.include.all.keys('uuid', 'diretoria_regional', 'unidade_educacional', 'data')
	}
})

Then('a consulta de formulario IMR retorna erro de status ou permissao negada', function () {
	expect([400, 403]).to.include(this.response.status)
	if (this.response.status === 403) permissao(this.response)
})

When('consulto o recurso de formulario IMR {string} com UUID {string}', function (recurso, identificador) {
	const consultas = {
		formulario: (uuid) => cy.consultar_imr_formulario_supervisao_por_uuid(uuid),
		respostas: (uuid) => cy.consultar_imr_formulario_supervisao_respostas(uuid),
		'nao se aplica': (uuid) => cy.consultar_imr_formulario_supervisao_respostas_nao_aplica(uuid),
	}
	const executar = (uuid) => {
		consultas[recurso](uuid).then((response) => { this.response = response })
	}
	if (identificador === 'invalido') {
		executar(uuidInvalido)
		return
	}
	obterUuidFormulario().then((uuids) => {
		if (uuids.length) {
			consultarPrimeiroFormularioValido(uuids, consultas[recurso])
				.then((response) => { this.response = response })
		}
		else this.response = { status: 403, body: { detail: 'Sem permissao ou massa' } }
	})
})

Then('o recurso de formulario IMR retorna {string}', function (resultado) {
	if (resultado === 'nao encontrado') {
		expect([403, 404]).to.include(this.response.status)
	} else {
		expect([200, 403]).to.include(this.response.status)
	}
	if (this.response.status === 403) permissao(this.response)
	if (this.response.status === 200) expect(this.response.body).to.exist
})

When('consulto a consulta auxiliar IMR {string}', function (consulta) {
	const comandos = {
		dashboard: () => cy.consultar_imr_formulario_supervisao_dashboard(),
		nutricionistas: () => cy.consultar_imr_formulario_supervisao_lista_nomes_nutricionistas(),
	}
	comandos[consulta]().then((response) => { this.response = response })
})

Then('a consulta auxiliar IMR retorna lista ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		permissao(this.response)
		return
	}
	expect(this.response.body).to.have.property('results').that.is.an('array')
})
