import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('solicito confirmacao de email para usuario inexistente', function () {
	cy.clearCookies()
	cy.confirmar_email('00000000-0000-0000-0000-000000000000', 'chave-invalida').then((response) => {
		this.response = response
	})
})

Then('a confirmacao de email retorna erro de usuario inexistente', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body.detail).to.eq('Erro ao confirmar email')
})
