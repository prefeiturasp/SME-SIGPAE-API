 import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function consultar(contexto, opcoes) {
	return cy.executar_kit_lanches(opcoes).then((response) => { contexto.response = response })
}

function validarKit(kit) {
	expect(kit).to.include.all.keys('uuid', 'nome', 'descricao', 'status', 'edital', 'tipos_unidades')
	expect(kit.uuid).to.match(uuidRegex)
	expect(kit.nome).to.be.a('string')
	expect(kit.descricao).to.be.a('string')
	expect(['ATIVO', 'INATIVO']).to.include(kit.status)
	expect(kit.tipos_unidades).to.be.an('array')
	kit.tipos_unidades.forEach((uuid) => expect(uuid).to.match(uuidRegex))
	if (kit.edital !== null) expect(kit.edital).to.match(uuidRegex)
}

function parametrosNomeInexistente() {
	return { nome: 'KIT_INEXISTENTE_CYPRESS_AUTOMACAO', edital: inexistente, 'tipos_unidades[]': inexistente }
}

function obterReferencia(contexto) {
	return cy.executar_kit_lanches().then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'kits disponiveis em QA').to.be.an('array').and.not.be.empty
		contexto.kitReferencia = response.body.results.find((kit) => kit.nome && kit.edital && kit.tipos_unidades.length)
		expect(contexto.kitReferencia, 'kit com nome, edital e tipo de unidade').to.exist
	})
}

When('executo {string} em kit lanches na rota {string} com perfil {string}', function (method, rota, perfil) {
	this.rotaKitPerfil = rota
	return autenticarKit(perfil).then(() => consultar(this, {
		method, caminho: rota === 'principal' ? '' : rota,
		qs: rota === 'nome-existe/' ? parametrosNomeInexistente() : { page: 1, page_size: 2 },
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}))
})

Then('kit lanches retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('kit lanches valida o retorno permitido para o perfil', function () {
	if (this.response.status === 200 && this.rotaKitPerfil === 'principal') {
		expect(this.response.body.results).to.be.an('array')
		this.response.body.results.forEach(validarKit)
	} else if (this.response.status === 200 && this.rotaKitPerfil === 'consulta-kits/') {
		expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
		expect(this.response.body.count).to.be.a('number').and.at.least(0)
		expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
		this.response.body.results.forEach((kit) => {
			expect(kit.uuid).to.match(uuidRegex)
			expect(kit.nome).to.be.a('string')
			expect(['Ativo', 'Inativo']).to.include(kit.status)
			expect(kit.tipos_unidades).to.be.an('array')
		})
	} else if (this.response.status === 400) {
		for (const campo of ['edital', 'tipos_unidades']) expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	} else if (this.rotaKitPerfil === 'nome-existe/' && this.response.status === 404) {
		// QA substitui o corpo das respostas 404 por uma pagina HTML.
		expect(this.response.body).to.exist
	}
})

When('consulto detalhe de kit lanche existente com perfil {string}', function (perfil) {
	return autenticarKit(perfil).then(() => obterReferencia(this))
		.then(() => consultar(this, { caminho: this.kitReferencia.uuid + '/' }))
})

Then('o detalhe do kit lanche corresponde ao registro consultado', function () {
	validarKit(this.response.body)
	expect(this.response.body).to.deep.eq(this.kitReferencia)
})

When('filtro kit lanches na rota {string} por {string} igual a {string} com perfil {string}', function (rota, campo, valor, perfil) {
	this.campoFiltroKit = campo
	this.valorFiltroKit = valor
	this.rotaKitPerfil = rota
	return autenticarKit(perfil).then(() => consultar(this, {
		caminho: rota === 'principal' ? '' : rota, qs: { [campo]: valor, page_size: 2 },
	}))
})

Then('os kits correspondem ao filtro informado', function () {
	expect(this.response.body.results).to.be.an('array')
	if (this.campoFiltroKit === 'status') {
		const esperado = this.rotaKitPerfil === 'consulta-kits/' ? { ATIVO: 'Ativo', INATIVO: 'Inativo' }[this.valorFiltroKit] : this.valorFiltroKit
		this.response.body.results.forEach((kit) => expect(kit.status).to.eq(esperado))
	} else {
		expect(this.response.body.results).to.deep.eq([])
	}
})

When('consulto nome de kit lanche {string} com perfil {string}', function (caso, perfil) {
	return autenticarKit(perfil).then(() => obterReferencia(this)).then(() => {
		const kit = this.kitReferencia
		const qs = { nome: kit.nome, edital: kit.edital, 'tipos_unidades[]': kit.tipos_unidades[0] }
		if (caso === 'do proprio registro') qs.uuid = kit.uuid
		return consultar(this, { caminho: 'nome-existe/', qs })
	})
})

Then('kit lanches informa nome {string}', function (resultado) {
	if (resultado === 'existente') expect(this.response.body.detail).to.include('já existe')
	else expect(this.response.status).to.eq(404)
})

When('executo {string} em kit lanches na rota {string} com acesso {string}', function (method, rota, acesso) {
	cy.clearCookies()
	return consultar(this, {
		method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido',
		qs: rota === 'nome-existe/' ? parametrosNomeInexistente() : undefined,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	})
})

function autenticarKit(perfil) {
	const usuarios = {
		COORDENADOR_LOGISTICA: 'usuario_coordenador_logistica',
		COORDENADOR_CODAE_DILOG_LOGISTICA: 'usuario_coordenador_codae_dilog_logistica',
		COORDENADOR_SUPERVISAO_NUTRICAO: 'usuario_coordenador_supervisao_nutricao',
		DILOG_CRONOGRAMA: 'usuario_dilog_cronograma', DILOG_QUALIDADE: 'usuario_dilog_qualidade',
		ABASTECIMENTO: 'usuario_abastecimento', DIRETOR_UE: 'usuario_diretor_ue',
		CODAE: 'usuario_codae', GPCODAE: 'usuario_gpcodae', DRE: 'usuario_dre',
		CLASSIFICACOES_DIETA: 'usuario_classificacoes_dieta', USUARIO_ESCOLA_CEI_ADMIN: 'usuario_escola_cei_admin',
		MEDICAO: 'usuario_medicao', DISTRIBUIDOR: 'usuario_distribuidor',
		EMEF: 'usuario_emef', CEMEI: 'usuario_cemei', CEI: 'usuario_cei', CCI: 'usuario_cci',
		DILOG_DIRETORIA: 'usuario_dilog_diretoria', ADMINISTRADOR_EMPRESA: 'usuario_administrador_empresa',
	}
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial de ' + perfil).to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}
