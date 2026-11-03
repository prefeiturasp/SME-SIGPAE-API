import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const rotas = { codae: 'pedidos-codae/', dre: 'pedidos-diretoria-regional/' }

function autenticar(perfil) {
	const usuarios = { codae: 'usuario_codae', dre: 'usuario_dre', escola: 'usuario_diretor_ue' }
	expect(usuarios).to.have.property(perfil)
	const usuario = Cypress.env(usuarios[perfil])
	expect(usuario, 'credencial do painel de inclusao').to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function consultar(contexto, perfil, filtro = 'sem_filtro', qs = {}) {
	expect(rotas).to.have.property(perfil)
	return autenticar(perfil).then(() => cy.executar_inclusao_alimentacao({
		caminho: rotas[perfil] + filtro + '/', qs: { page_size: 2, ...qs },
	})).then((response) => { contexto.response = response })
}

When('consulto o painel de inclusao de alimentacao como {string} com filtro {string}', function (perfil, filtro) {
	return consultar(this, perfil, filtro)
})

When('consulto o painel de inclusao de alimentacao como {string} com parametro {string} igual a {string}', function (perfil, parametro, valor) {
	return consultar(this, perfil, 'sem_filtro', { [parametro]: valor })
})

Then('o painel de inclusao de alimentacao retorna dados validos', function () {
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results', 'escolas_solicitantes', 'totais')
	expect(this.response.body.count).to.be.a('number').and.at.least(0)
	expect(this.response.body.escolas_solicitantes).to.be.a('number').and.at.least(0)
	expect(this.response.body.totais).to.have.all.keys('PRIORITARIO', 'LIMITE', 'REGULAR')
	Object.values(this.response.body.totais).forEach((total) => expect(total).to.be.a('number').and.at.least(0))
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
	this.response.body.results.forEach((inclusao) => {
		expect(inclusao.uuid).to.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
		expect(inclusao.status).to.be.a('string').and.not.be.empty
		expect(inclusao.escola).to.be.an('object')
	})
})

Then('o painel de inclusao de alimentacao retorna lista vazia', function () {
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
	expect(this.response.body.escolas_solicitantes).to.eq(0)
	Object.values(this.response.body.totais).forEach((total) => expect(total).to.eq(0))
})

When('consulto o painel de inclusao de alimentacao na rota {string} com acesso {string}', function (rota, acesso) {
	cy.clearCookies()
	return cy.executar_inclusao_alimentacao({ caminho: rota, token: acesso === 'ausente' ? null : 'token-invalido' })
		.then((response) => { this.response = response })
})

When('consulto o painel de inclusao de alimentacao de {string} com perfil escola', function (perfil) {
	expect(rotas).to.have.property(perfil)
	return autenticar('escola').then(() => cy.executar_inclusao_alimentacao({ caminho: rotas[perfil] + 'sem_filtro/' }))
		.then((response) => { this.response = response })
})

Then('o painel de inclusao de alimentacao retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
