import Login_SME_Localizadores from '../locators/login_locators'

const login_SME_Localizadores = new Login_SME_Localizadores()

Cypress.Commands.add('login_sme', (device) => {
	cy.configurar_visualizacao(device)
	cy.visit('/')
	cy.url().should('include', '/login')
})

Cypress.Commands.add('dados_de_login', (usuario, senha) => {
	cy.get('input.input-login', { timeout: 10000 }).should('have.length.at.least', 2)

	cy.get('input.input-login').eq(0).should('be.visible').clear()
	cy.get(login_SME_Localizadores.campo_senha()).should('be.visible').clear()

	if (usuario) {
		cy.get('input.input-login').eq(0).type(usuario)
	}

	if (senha) {
		cy.get(login_SME_Localizadores.campo_senha()).type(senha)
	}
})

Cypress.Commands.add('clicar_botao', () => {
	cy.get(login_SME_Localizadores.botao_acessar())
		.should('be.visible')
		.click()
})

Cypress.Commands.add('validar_mensagem', (mensagem) => {
	if (mensagem === 'Não foi possível logar no sistema') {
		cy.get(login_SME_Localizadores.mensagem_erro())
			.should('be.visible')
			.contains(mensagem)
	} else if (mensagem === 'Campo obrigatório') {
		cy.get(login_SME_Localizadores.mensagem_erro_campo_em_branco())
			.should('be.visible')
			.contains(mensagem)
	} else {
		cy.get(login_SME_Localizadores.mensagem())
			.should('be.visible')
			.and('contain', mensagem)
	}
})