import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function executar(contexto, opcoes) {
	return cy.executar_lancamento_diario(opcoes).then((response) => { contexto.response = response })
}

function parametros(rota) {
	if (!['por-mes/', 'dados-dia-periodo/'].includes(rota)) return { limit: 1 }
	return cy.consultar_referencia_lancamento_diario().then((response) => {
		expect(response.status, 'referencia de escola e periodo').to.eq(200)
		expect(response.body.results, 'escola e periodo disponiveis em QA').to.be.an('array').and.not.be.empty
		const uuid = response.body.results[0].uuid
		expect(uuid).to.match(uuidRegex)
		return rota === 'por-mes/'
			? { mes: '01/2026', escola_periodo_escolar: uuid }
			: { data: '01/01/2026', escola_periodo_escolar: uuid }
	})
}

When('executo {string} em lancamento diario na rota {string} com perfil {string}', function (method, rota, perfil) {
	this.rotaLancamentoDiario = rota
	this.perfilLancamentoDiario = perfil
	return autenticarLancamentoDiario(perfil).then(() => parametros(rota)).then((qs) => executar(this, {
		method, caminho: rota === 'principal' ? '' : rota, qs,
		// POST vazio nao contem grupos e nao cria lancamentos; PUT/PATCH usam UUID inexistente.
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}))
})

Then('lancamento diario retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

function validarLancamento(item) {
	expect(item).to.include.all.keys('uuid', 'data', 'escola_periodo_escolar', 'refeicoes', 'frequencia', 'tipo_dieta', 'observacoes')
	expect(item.uuid).to.match(uuidRegex)
	expect(item.refeicoes).to.be.an('array')
}

Then('lancamento diario valida o retorno para o perfil', function () {
	if (this.response.status !== 200) return
	const body = this.response.body
	if (this.rotaLancamentoDiario === 'principal' && typeof body === 'string') {
		expect(body).to.eq('OK')
	} else if (this.rotaLancamentoDiario === 'principal') {
		expect(body).to.include.all.keys('count', 'next', 'previous', 'results')
		expect(body.count).to.be.a('number').and.at.least(0)
		expect(body.results).to.be.an('array').and.have.length.at.most(1)
		body.results.forEach(validarLancamento)
	} else if (this.rotaLancamentoDiario === 'por-mes/') {
		expect(body).to.be.an('array').and.have.length(31)
		body.forEach((dia, indice) => {
			expect(dia).to.include.all.keys('dia', 'eh_feriado_ou_fds', 'quantidade_alunos', 'lancamento')
			expect(dia.dia).to.eq(indice + 1)
			expect(dia.eh_feriado_ou_fds).to.be.a('boolean')
			if (dia.lancamento !== null) validarLancamento(dia.lancamento)
		})
	} else if (this.rotaLancamentoDiario === 'dados-dia-periodo/') {
		expect(body).to.include.all.keys('kits_lanches', 'merenda_seca', 'troca', 'tem_sobremesa_doce_na_semana', 'quantidade_alunos')
		expect(body.tem_sobremesa_doce_na_semana).to.be.a('boolean')
		expect(body.quantidade_alunos).to.include.all.keys('convencional', 'grupoA', 'grupoB')
	}
})

When('executo {string} em lancamento diario na rota {string} com acesso {string}', function (method, rota, acesso) {
	cy.clearCookies()
	return executar(this, {
		method, caminho: rota === 'principal' ? '' : rota,
		token: acesso === 'ausente' ? null : 'token-invalido',
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	})
})

function autenticarLancamentoDiario(perfil) {
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
