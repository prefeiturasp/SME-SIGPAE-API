import { Before, Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const uuidInvalido = '3ac751ee-f95d-4d5b-80da-437506b00000'
const comandosLista = {
	completa: 'consultar_lista_laboratorios',
	credenciados: 'consultar_lista_laboratorios_credenciados',
	nomes: 'consultar_lista_nomes_laboratorios',
}
function dados(tipo = 'validos') {
	if (tipo === 'campos_ausentes') return {}
	const base = {
		nome: `Testes Automacao ${Date.now()}`,
		cnpj: Date.now().toString().slice(0, 14), cep: '05010000',
		logradouro: 'Rua Teste Automacao', numero: '123', bairro: 'Bairro Teste',
		cidade: 'Sao Paulo', estado: 'SP', credenciado: true,
		contato_nome: 'Contato Teste', contato_telefone: '1155555555',
		contato_telefone2: '115888888', contato_celular: '11977777777',
		contato_email: 'user@example.com', contato_eh_nutricionista: true,
		contato_crn_numero: '1234567', complemento: 'Complemento Teste',
	}
	if (tipo === 'booleanos_invalidos') {
		return { ...base, credenciado: '123', contato_eh_nutricionista: '456' }
	}
	if (tipo === 'campos_em_branco') {
		return Object.fromEntries(Object.keys(base).map((chave) => [chave,
			['credenciado'].includes(chave) ? false : '']))
	}
	return base
}
function validarLaboratorio(item) {
	expect(item).to.include.all.keys(
		'criado_em', 'alterado_em', 'uuid', 'nome', 'cnpj', 'cep', 'logradouro',
		'numero', 'complemento', 'bairro', 'cidade', 'estado', 'credenciado',
	)
	if (Object.prototype.hasOwnProperty.call(item, 'contatos')) {
		expect(item.contatos).to.be.an('array')
	}
}
function validarPermissao(response) {
	expect(response.status).to.eq(403)
	expect(response.body.detail).to.not.be.empty
}
Given('que estou autenticado como DILOG qualidade para gerenciar laboratorios', () => {
	return autenticarLaboratorios('DILOG_QUALIDADE')
})
When('consulto todos os laboratorios', function () {
	cy.consultar_laboratorios().then((response) => { this.response = response })
})
When('filtro laboratorios pelo campo existente {string}', function (campo) {
	cy.consultar_laboratorios().then((lista) => {
		if (lista.status === 403) return void (this.response = lista)
		this.valor = lista.body.results[0][campo]
		cy.consultar_laboratorios_com_filtros(`?${campo}=${this.valor}`)
			.then((response) => { this.response = response })
	})
})
When('filtro laboratorios pelo campo inexistente {string}', function (campo) {
	const valores = {
		nome: 'NomeInvalido Para o Teste', cnpj: '11110000000000',
		uuid: 'bd08e0a0-b0b0-0ab0-b000-a05c000f00c0',
	}
	cy.consultar_laboratorios_com_filtros(`?${campo}=${valores[campo]}`)
		.then((response) => { this.response = response })
})
When('consulto um laboratorio existente por UUID', function () {
	cy.consultar_laboratorios().then((lista) => {
		if (lista.status === 403) return void (this.response = lista)
		this.uuid = lista.body.results[0].uuid
		cy.consultar_laboratorios_por_uuid(this.uuid).then((response) => { this.response = response })
	})
})
When('consulto um laboratorio por UUID invalido', function () {
	cy.consultar_laboratorios_por_uuid(uuidInvalido).then((response) => { this.response = response })
})
When('consulto a listagem de laboratorios {string}', function (lista) {
	this.lista = lista
	cy[comandosLista[lista]]().then((response) => { this.response = response })
})
When('cadastro um laboratorio com dados {string}', function (tipo) {
	this.tipo = tipo
	cy.cadastrar_laboratorios(dados(tipo)).then((response) => {
		this.response = response
		if (response.status === 201) {
			cy.deletar_laboratorios(response.body.uuid).then((exclusao) => { this.exclusao = exclusao })
		}
	})
})
When('cadastro e excluo um laboratorio valido', function () {
	cy.cadastrar_laboratorios(dados()).then((criado) => {
		if (criado.status === 403) return void (this.response = criado)
		cy.deletar_laboratorios(criado.body.uuid).then((response) => { this.response = response })
	})
})
When('excluo um laboratorio por UUID invalido', function () {
	cy.deletar_laboratorios(uuidInvalido).then((response) => { this.response = response })
})
function atualizar(contexto, metodo, tipo) {
	cy.cadastrar_laboratorios(dados()).then((criado) => {
		if (criado.status === 403) return void (contexto.response = criado)
		const comando = metodo === 'PUT' ? 'put_alterar_laboratorios' : 'patch_alterar_laboratorios'
		cy[comando](criado.body.uuid, dados(tipo)).then((response) => {
			contexto.response = response
			cy.deletar_laboratorios(criado.body.uuid).then((exclusao) => { contexto.exclusao = exclusao })
		})
	})
}
When('atualizo por PUT um laboratorio com dados {string}', function (tipo) {
	atualizar(this, 'PUT', tipo)
})
When('atualizo por PATCH um laboratorio com dados {string}', function (tipo) {
	atualizar(this, 'PATCH', tipo)
})
When('atualizo por PUT um laboratorio com UUID invalido', function () {
	cy.put_alterar_laboratorios(uuidInvalido, {}).then((response) => { this.response = response })
})
When('atualizo por PATCH um laboratorio com UUID invalido', function () {
	cy.patch_alterar_laboratorios(uuidInvalido, {}).then((response) => { this.response = response })
})
Then('a consulta de laboratorios retorna status permitido e lista valida', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array')
	if (this.response.body.results.length) validarLaboratorio(this.response.body.results[0])
})
Then('o filtro valido de laboratorios retorna dados coerentes', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	validarLaboratorio(this.response.body.results[0])
})
Then('o filtro inexistente retorna lista vazia ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.be.an('array').and.empty
})
Then('o laboratorio por UUID retorna dados coerentes', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	validarLaboratorio(this.response.body)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('a operacao de laboratorio retorna status de erro permitido', function () {
	expect([400, 403, 404]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
})
Then('a listagem de laboratorios retorna status permitido e dados validos', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.response.body.results).to.be.an('array')
	if (!this.response.body.results.length || this.lista === 'nomes') return
	const item = this.response.body.results[0]
	if (this.lista === 'completa') expect(item).to.include.all.keys('nome', 'cnpj')
	else expect(item).to.include.all.keys('uuid', 'nome')
})
Then('o cadastro valido retorna sucesso ou permissao negada e realiza limpeza', function () {
	expect([201, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.exclusao.status).to.be.oneOf([204, 403, 404])
})
Then('o cadastro invalido retorna validacao ou permissao negada', function () {
	expect([400, 403]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
	else expect(this.response.body).to.be.an('object').and.not.be.empty
})
Then('a exclusao valida retorna status permitido', function () {
	expect([204, 403, 404]).to.include(this.response.status)
})
Then('a atualizacao valida retorna sucesso ou permissao negada e realiza limpeza', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.exclusao.status).to.be.oneOf([204, 403, 404])
})
Then('a atualizacao invalida retorna validacao ou permissao negada e realiza limpeza', function () {
	expect([400, 403]).to.include(this.response.status)
	if (this.response.status === 403) return validarPermissao(this.response)
	expect(this.response.body).to.be.an('object').and.not.be.empty
	expect(this.exclusao.status).to.be.oneOf([204, 403, 404])
})

function autenticarLaboratorios(perfil) {
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

Before({ tags: '@funcionais_laboratorios' }, () => autenticarLaboratorios('DILOG_QUALIDADE'))

When('executo {string} em laboratorios na rota {string} com perfil {string}', function (method, rota, perfil) {
	this.rotaLaboratorioPerfil = rota
	return autenticarLaboratorios(perfil).then(() => cy.executar_laboratorios({
		method, caminho: rota === 'principal' ? '' : rota,
		qs: { page: 1, page_size: 2 },
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	})).then((response) => { this.response = response })
})

Then('laboratorios retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('laboratorios valida o retorno permitido para o perfil', function () {
	if (this.response.status === 200) {
		expect(this.response.body.results).to.be.an('array')
		this.response.body.results.forEach((item) => {
			if (this.rotaLaboratorioPerfil === 'principal') validarLaboratorio(item)
			else if (this.rotaLaboratorioPerfil === 'lista-nomes-laboratorios/') expect(item).to.be.a('string')
			else if (this.rotaLaboratorioPerfil === 'lista-laboratorios/') expect(item).to.include.all.keys('nome', 'cnpj')
			else expect(item).to.include.all.keys('uuid', 'nome')
		})
	} else if (this.response.status === 400) {
		for (const campo of ['nome', 'cnpj']) expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})

When('executo {string} em laboratorios na rota {string} com acesso {string}', function (method, rota, acesso) {
	cy.clearCookies()
	return cy.executar_laboratorios({
		method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido',
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}).then((response) => { this.response = response })
})
