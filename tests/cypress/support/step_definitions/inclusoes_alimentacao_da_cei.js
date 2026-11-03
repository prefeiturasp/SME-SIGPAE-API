import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil = 'escola') {
	const usuarios = { escola: 'usuario_diretor_ue', medicao: 'usuario_medicao' }
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial de inclusao da CEI').to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.executar_inclusoes_alimentacao_da_cei(opcoes).then((response) => { contexto.response = response })
}

function validarInclusao(inclusao) {
	expect(inclusao.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(inclusao.status).to.be.a('string').and.not.be.empty
	expect(inclusao.escola).to.be.an('object').and.have.property('uuid')
	expect(inclusao.quantidade_alunos_por_faixas_etarias).to.be.an('array')
	expect(inclusao.dias_motivos_da_inclusao_cei).to.be.an('array')
	expect(inclusao.tipos_alimentacao).to.be.an('array')
	expect(inclusao.logs).to.be.an('array')
}

When('consulto inclusoes de alimentacao da CEI na rota {string}', function (rota) {
	return autenticar().then(() => consultar(this, { caminho: rota === 'principal' ? '' : rota, qs: { limit: 2 } }))
})

Then('inclusoes de alimentacao da CEI retorna lista paginada valida', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarInclusao)
})

When('consulto uma inclusao de alimentacao da CEI existente para {string}', function (operacao) {
	return autenticar('medicao').then(() => cy.executar_inclusoes_alimentacao_da_cei({ qs: { limit: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'inclusao da CEI disponivel em QA').to.be.an('array').and.not.be.empty
		this.inclusaoCeiReferencia = response.body.results[0]
		return consultar(this, {
			caminho: this.inclusaoCeiReferencia.uuid + '/' + (operacao === 'PDF' ? 'relatorio/' : ''),
			encoding: operacao === 'PDF' ? 'binary' : 'utf8',
		})
	})
})

Then('o detalhe da inclusao da CEI corresponde ao registro consultado', function () {
	validarInclusao(this.response.body)
	expect(this.response.body.uuid).to.eq(this.inclusaoCeiReferencia.uuid)
	expect(this.response.body.escola.uuid).to.eq(this.inclusaoCeiReferencia.escola.uuid)
})

Then('o relatorio da inclusao da CEI retorna PDF valido', function () {
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF')).to.eq(true)
})

When('executo {string} em inclusoes de alimentacao da CEI na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = {
		method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('inclusoes de alimentacao da CEI retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('inclusoes de alimentacao da CEI informa campos obrigatorios', function () {
	for (const campo of ['escola', 'quantidade_alunos_por_faixas_etarias', 'dias_motivos_da_inclusao_cei']) {
		expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})
