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
		if (response.status === 200) expect(response.body.results, 'catalogo IMR disponivel em QA').to.be.an('array').and.not.be.empty
		return response
	})
}

function obterUuidFormulario() {
	return cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO')
		.then((response) => {
			expect([200, 403]).to.include(response.status)
			if (response.status === 200) expect(response.body.results, 'formulario IMR disponivel em QA').to.be.an('array').and.not.be.empty
			return response
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
	obterUuidCatalogo(consulta).then((response) => {
		if (response.status === 403) {
			this.response = response
			return
		}
		this.uuidReferenciaIMR = response.body.results[0].uuid
		return consulta(this.uuidReferenciaIMR).then((detalhe) => { this.response = detalhe })
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
		expect(this.response.body.uuid).to.eq(this.uuidReferenciaIMR)
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
	obterUuidFormulario().then((response) => {
		if (response.status === 403) {
			this.response = response
			return
		}
		this.uuidFormularioIMR = response.body.results[0].uuid
		this.recursoFormularioIMR = recurso
		return consultas[recurso](this.uuidFormularioIMR).then((detalhe) => { this.response = detalhe })
	})
})

Then('o recurso de formulario IMR retorna {string}', function (resultado) {
	if (resultado === 'nao encontrado') {
		expect([403, 404]).to.include(this.response.status)
	} else {
		expect([200, 403]).to.include(this.response.status)
	}
	if (this.response.status === 403) permissao(this.response)
	if (this.response.status === 200) {
		if (this.recursoFormularioIMR === 'formulario') expect(this.response.body.uuid).to.eq(this.uuidFormularioIMR)
		else expect(this.response.body).to.be.an('array')
	}
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

When('executo {string} em IMR na rota {string} com acesso {string}', function (method, caminho, acesso) {
	const opcoes = { method, caminho, body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined }
	if (acesso === 'autenticado') {
		const perfil = caminho.startsWith('formulario-diretor/') ? 'usuario_diretor_ue' : 'usuario_coordenador_supervisao_nutricao'
		expect(Cypress.env(perfil), 'credencial do perfil IMR').to.be.a('string').and.not.be.empty
		return cy.autenticar_login(Cypress.env(perfil), Cypress.env('senha'))
			.then(() => cy.executar_imr(opcoes)).then((response) => { this.response = response })
	}
	cy.clearCookies()
	return cy.executar_imr({ ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
		.then((response) => { this.response = response })
})

Then('IMR retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('consulto IMR na rota {string} com parametro {string} igual a {string}', function (caminho, parametro, valor) {
	const perfil = caminho.startsWith('formulario-diretor/') ? 'usuario_diretor_ue' : 'usuario_coordenador_supervisao_nutricao'
	expect(Cypress.env(perfil), 'credencial do perfil IMR').to.be.a('string').and.not.be.empty
	return cy.autenticar_login(Cypress.env(perfil), Cypress.env('senha'))
		.then(() => cy.executar_imr({ caminho, qs: { [parametro]: valor } }))
		.then((response) => { this.response = response })
})

Then('IMR retorna resultados vazios', function () {
	expect(this.response.body.results).to.deep.eq([])
})

Then('IMR informa erro no campo {string}', function (campo) {
	expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
})
