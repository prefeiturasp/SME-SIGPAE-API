import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil = 'cronograma') {
	const usuarios = {
		cronograma: 'usuario_dilog_cronograma', escola: 'usuario_diretor_ue',
		COORDENADOR_LOGISTICA: 'usuario_coordenador_logistica',
		COORDENADOR_CODAE_DILOG_LOGISTICA: 'usuario_coordenador_codae_dilog_logistica',
		COORDENADOR_SUPERVISAO_NUTRICAO: 'usuario_coordenador_supervisao_nutricao',
		DILOG_CRONOGRAMA: 'usuario_dilog_cronograma',
		DILOG_QUALIDADE: 'usuario_dilog_qualidade',
		ABASTECIMENTO: 'usuario_abastecimento',
		DIRETOR_UE: 'usuario_diretor_ue',
		CODAE: 'usuario_codae',
		GPCODAE: 'usuario_gpcodae',
		DRE: 'usuario_dre',
		CLASSIFICACOES_DIETA: 'usuario_classificacoes_dieta',
		USUARIO_ESCOLA_CEI_ADMIN: 'usuario_escola_cei_admin',
		MEDICAO: 'usuario_medicao',
		DISTRIBUIDOR: 'usuario_distribuidor',
	}
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial de ' + perfil).to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.executar_interrupcao_programada_entrega(opcoes).then((response) => { contexto.response = response })
}

function validarInterrupcao(item) {
	expect(item.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(item.data).to.match(/^\d{2}\/\d{2}\/\d{4}$/)
	expect(['EMENDA', 'REUNIAO', 'INVENTARIO', 'FERIADO', 'OUTROS']).to.include(item.motivo)
	expect(['ARMAZENAVEL', 'PONTO_A_PONTO']).to.include(item.tipo_calendario)
	expect(item.motivo_display).to.be.a('string').and.not.be.empty
	expect(item.tipo_calendario_display).to.be.a('string').and.not.be.empty
}

When('consulto interrupcao programada de entrega na rota {string}', function (rota) {
	return autenticar().then(() => consultar(this, { caminho: rota === 'principal' ? '' : rota, qs: { limit: 2 } }))
})

function validarListagem() {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarInterrupcao)
}

Then('interrupcao programada retorna lista paginada valida', validarListagem)

function validarMotivos() {
	expect(this.response.body).to.be.an('array').and.not.be.empty
	const motivos = this.response.body.map((item) => item.value)
	expect(motivos).to.have.members(['EMENDA', 'REUNIAO', 'INVENTARIO', 'OUTROS'])
	this.response.body.forEach((item) => expect(item.label).to.be.a('string').and.not.be.empty)
}

Then('interrupcao programada retorna motivos sem feriado', validarMotivos)

function validarDatasBloqueadas() {
	expect(this.response.body.results).to.be.an('array')
	const ano = Number(new Intl.DateTimeFormat('en', { year: 'numeric', timeZone: 'America/Sao_Paulo' }).format(new Date()))
	this.response.body.results.forEach((data) => {
		expect(data).to.match(/^\d{4}-\d{2}-\d{2}$/)
		expect([ano, ano + 1]).to.include(Number(data.slice(0, 4)))
	})
}

Then('interrupcao programada retorna datas bloqueadas validas', validarDatasBloqueadas)

When('filtro interrupcoes programadas por {string} igual a {string}', function (campo, valor) {
	this.filtroInterrupcao = { campo, valor }
	return autenticar().then(() => consultar(this, { qs: { limit: 2, [campo + '[]']: valor } }))
})

Then('as interrupcoes correspondem ao filtro consultado', function () {
	const { campo, valor } = this.filtroInterrupcao
	this.response.body.results.forEach((item) => expect(item[campo]).to.eq(valor))
})

When('cadastro interrupcao programada com dados {string}', function (caso) {
	const corpos = {
		vazios: {},
		'data invalida': { data: 'data-invalida', motivo: 'REUNIAO' },
		'motivo invalido': { data: '2099-12-31', motivo: 'INVALIDO' },
		'calendario invalido': { data: '2099-12-31', motivo: 'REUNIAO', tipo_calendario: 'INVALIDO' },
		'outros sem descricao': { data: '2099-12-31', motivo: 'OUTROS' },
	}
	expect(corpos).to.have.property(caso)
	return autenticar().then(() => consultar(this, { method: 'POST', body: corpos[caso] }))
})

Then('interrupcao programada informa erro no campo {string}', function (campo) {
	expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
})

When('executo {string} em interrupcao programada na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = { method, caminho: rota === 'principal' ? '' : rota, body: method === 'POST' ? {} : undefined }
	if (['cronograma', 'escola'].includes(acesso)) return autenticar(acesso).then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('interrupcao programada retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('executo {string} em interrupcao programada na rota {string} com perfil {string}', function (method, rota, perfil) {
	this.rotaInterrupcaoPerfil = rota
	return autenticar(perfil).then(() => consultar(this, {
		method, caminho: rota === 'principal' ? '' : rota,
		qs: method === 'GET' ? { limit: 2 } : undefined,
		body: method === 'POST' ? {} : undefined,
	}))
})

Then('interrupcao programada valida o retorno permitido para o perfil', function () {
	if (this.response.status === 200) {
		const validadores = { principal: validarListagem, 'motivos/': validarMotivos, 'datas-bloqueadas-armazenavel/': validarDatasBloqueadas }
		expect(validadores).to.have.property(this.rotaInterrupcaoPerfil)
		validadores[this.rotaInterrupcaoPerfil].call(this)
	} else if (this.response.status === 400) {
		for (const campo of ['data', 'motivo']) expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})
