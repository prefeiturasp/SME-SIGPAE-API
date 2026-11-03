import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar(perfil = 'escola') {
	const usuarios = {
		escola: 'usuario_diretor_ue', codae: 'usuario_codae', dre: 'usuario_dre',
		medicao: 'usuario_medicao',
	}
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial para inclusao CEMEI').to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function consultar(contexto, opcoes = {}) {
	return cy.executar_inclusao_alimentacao_cemei(opcoes).then((response) => { contexto.response = response })
}

function validarInclusao(inclusao) {
	expect(inclusao.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
	expect(inclusao.status).to.be.a('string').and.not.be.empty
	expect(inclusao.escola).to.be.an('object').and.have.property('uuid')
	for (const campo of ['dias_motivos_da_inclusao_cemei', 'quantidade_alunos_cei_da_inclusao_cemei', 'quantidade_alunos_emei_da_inclusao_cemei']) {
		expect(inclusao[campo], campo).to.be.an('array')
	}
}

When('consulto inclusoes de alimentacao CEMEI com perfil {string}', function (perfil) {
	return autenticar(perfil).then(() => consultar(this, { qs: { limit: 2 } }))
})

Then('inclusao de alimentacao CEMEI retorna lista paginada valida', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach(validarInclusao)
})

When('consulto inclusoes de alimentacao CEMEI com status {string}', function (status) {
	this.statusInclusaoCemei = status.toUpperCase()
	return autenticar().then(() => consultar(this, { qs: { status, limit: 2 } }))
})

Then('as inclusoes CEMEI correspondem ao status consultado', function () {
	this.response.body.results.forEach((inclusao) => {
		expect(inclusao.status).to.eq(this.statusInclusaoCemei)
	})
})

Then('inclusao de alimentacao CEMEI retorna lista vazia', function () {
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
})

When('consulto uma inclusao de alimentacao CEMEI existente para {string}', function (operacao) {
	return autenticar('medicao').then(() => cy.executar_inclusao_alimentacao_cemei({ qs: { limit: 1 } })).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results, 'inclusao CEMEI disponivel em QA').to.be.an('array').and.not.be.empty
		this.inclusaoCemeiReferencia = response.body.results[0]
		return consultar(this, {
			caminho: this.inclusaoCemeiReferencia.uuid + '/' + (operacao === 'PDF' ? 'relatorio/' : ''),
			encoding: operacao === 'PDF' ? 'binary' : 'utf8',
		})
	})
})

Then('o detalhe da inclusao CEMEI corresponde ao registro consultado', function () {
	validarInclusao(this.response.body)
	expect(this.response.body.uuid).to.eq(this.inclusaoCemeiReferencia.uuid)
	expect(this.response.body.escola.uuid).to.eq(this.inclusaoCemeiReferencia.escola.uuid)
})

Then('o relatorio da inclusao CEMEI retorna um PDF', function () {
	expect(this.response.headers['content-type']).to.include('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
	expect(this.response.body.trimEnd().endsWith('%%EOF')).to.eq(true)
})

When('executo {string} em inclusao de alimentacao CEMEI na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = {
		method, caminho: rota === 'principal' ? '' : rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('inclusao de alimentacao CEMEI retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

Then('inclusao de alimentacao CEMEI informa os campos obrigatorios', function () {
	for (const campo of ['escola', 'dias_motivos_da_inclusao_cemei']) {
		expect(this.response.body[campo], campo).to.be.an('array').and.not.be.empty
	}
})
