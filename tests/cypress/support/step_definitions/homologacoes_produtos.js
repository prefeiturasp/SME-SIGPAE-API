import { When, Then } from 'cypress-cucumber-preprocessor/steps'

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_homologacao_produto'), Cypress.env('senha'))
}

function consultar(contexto, opcoes) {
	return cy.executar_homologacoes_produtos(opcoes).then((response) => { contexto.response = response })
}

When('consulto o numero de protocolo de homologacoes de produtos', function () {
	return autenticar().then(() => consultar(this, { caminho: 'numero_protocolo/' }))
})

Then('homologacoes de produtos retorna um protocolo valido', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.match(/^AS\d{6}$/)
})

When('executo {string} em homologacoes de produtos na rota {string} com acesso {string}', function (method, rota, acesso) {
	const opcoes = {
		method, caminho: rota,
		body: ['POST', 'PUT', 'PATCH'].includes(method) ? {} : undefined,
	}
	if (acesso === 'autenticado') return autenticar().then(() => consultar(this, opcoes))
	cy.clearCookies()
	return consultar(this, { ...opcoes, token: acesso === 'ausente' ? null : 'token-invalido' })
})

Then('homologacoes de produtos retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
