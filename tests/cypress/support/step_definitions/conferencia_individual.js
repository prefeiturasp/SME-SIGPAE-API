import { When, Then } from 'cypress-cucumber-preprocessor/steps'
When('consulto a conferencia individual com usuario CODAE', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
	cy.consultar_conferencia_individual({ limit: 10, offset: 0 }).then((response) => {
		this.response = response
	})
})
Then('a consulta de conferencia individual retorna status 403 e detalhe', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(403)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})

When('acesso conferencia individual usando {string} como {string} no caminho {string}', function (metodo, perfil, caminho) {
	if (perfil === 'anonimo') cy.clearCookies()
	else cy.autenticar_login(Cypress.env(perfil === 'abastecimento' ? 'usuario_abastecimento' : 'usuario_codae'), Cypress.env('senha'))
	cy.requisitar_conferencia_individual(metodo, {
		uuid: caminho === 'detalhe' ? '00000000-0000-0000-0000-000000000000' : undefined,
		dados: ['POST', 'PUT', 'PATCH'].includes(metodo) ? {} : undefined,
		autenticado: perfil !== 'anonimo',
	}).then((response) => { this.response = response })
})
Then('a operacao de conferencia individual retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
