import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil) {
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

function consultar(contexto, opcoes) {
	return cy.executar_inversoes_dia_cardapio(opcoes).then((response) => { contexto.response = response })
}

function validarInversao(item) {
	expect(item.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(item.status).to.be.a('string').and.not.be.empty
	expect(item.escola).to.be.an('object').and.have.property('uuid')
	expect(item.tipos_alimentacao).to.be.an('array')
	expect(item.logs).to.be.an('array')
}

When('executo {string} em inversoes de cardapio na rota {string} com perfil {string}', function (method, rota, perfil) {
	this.rotaInversao = rota
	return autenticar(perfil).then(() => consultar(this, {
		method, caminho: rota === 'principal' ? '' : rota,
		qs: method === 'GET' ? { limit: 2 } : undefined,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}))
})

Then('inversoes de cardapio retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('inversoes de cardapio valida o retorno permitido para o perfil', function () {
	if (this.response.status === 200) {
		expect(this.response.body.results).to.be.an('array')
		this.response.body.results.forEach(validarInversao)
		if (['principal', 'minhas-solicitacoes/'].includes(this.rotaInversao)) {
			expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
			expect(this.response.body.results).to.have.length.at.most(2)
		}
	} else if (this.response.status === 400) {
		for (const campo of ['escola', 'data_de', 'data_para', 'tipos_alimentacao']) {
			expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
		}
	}
})

When('consulto inversao de cardapio existente para {string} com perfil {string}', function (operacao, perfil) {
	return autenticar(perfil).then(() => cy.executar_inversoes_dia_cardapio({ qs: { limit: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'inversao de cardapio disponivel em QA').to.be.an('array').and.not.be.empty
		this.inversaoReferencia = response.body.results[0]
		return consultar(this, {
			caminho: this.inversaoReferencia.uuid + '/' + (operacao === 'PDF' ? 'relatorio/' : ''),
			encoding: operacao === 'PDF' ? 'binary' : 'utf8',
		})
	})
})

Then('o detalhe da inversao de cardapio corresponde ao registro consultado', function () {
	validarInversao(this.response.body)
	expect(this.response.body.uuid).to.eq(this.inversaoReferencia.uuid)
	expect(this.response.body.escola.uuid).to.eq(this.inversaoReferencia.escola.uuid)
})

Then('o relatorio da inversao de cardapio retorna PDF valido', function () {
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF')).to.eq(true)
})

When('executo {string} em inversoes de cardapio na rota {string} com acesso {string}', function (method, rota, acesso) {
	cy.clearCookies()
	return consultar(this, {
		method, caminho: rota === 'principal' ? '' : rota, token: acesso === 'ausente' ? null : 'token-invalido',
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	})
})
