import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto os dias da semana autenticado', function () {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha')).then(() => {
		cy.consultar_dias_semana(globalThis.token).then((response) => { this.response = response })
	})
})

When('consulto os dias da semana com acesso {string}', function (acesso) {
	cy.clearCookies()
	cy.consultar_dias_semana(acesso === 'token invalido' ? 'token-invalido' : undefined).then((response) => { this.response = response })
})

Then('a consulta dos dias da semana retorna os sete dias', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.deep.eq({
		0: 'Segunda', 1: 'Ter\u00e7a', 2: 'Quarta', 3: 'Quinta',
		4: 'Sexta', 5: 'S\u00e1bado', 6: 'Domingo',
	})
})

Then('a consulta dos dias da semana rejeita a autenticacao', function () {
	expect(this.response.status).to.eq(401)
	expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
