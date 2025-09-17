import Login_SME_Localizadores from '../locators/login_locators'

const login_SME_Localizadores = new Login_SME_Localizadores

Cypress.Commands.add('login_sme', (device) => {
	cy.configurar_visualizacao(device)
	cy.visit('/')
})

Cypress.Commands.add('dados_de_login', (usuario, senha) => {
	usuario ? cy.get(login_SME_Localizadores.campo_usuario()).type(usuario) : ''
	senha ? cy.get(login_SME_Localizadores.campo_senha()).type(senha) : ''
})

Cypress.Commands.add('clicar_botao', () => {
	cy.get(login_SME_Localizadores.botao_acessar())
		.should('be.visible')
		.click()
})

Cypress.Commands.add('validar_mensagem', (mensagem) => {
	if (mensagem === 'Não foi possível logar no sistema') {
		cy.get(login_SME_Localizadores.mensagem_erro()).contains(mensagem)
	} else if (mensagem === 'Campo obrigatório') {
		cy.get(login_SME_Localizadores.logo_sigpae_login()).click()
		cy.get(login_SME_Localizadores.mensagem_erro_campo_em_branco()).contains(mensagem)
	} else {
		cy.get(login_SME_Localizadores.mensagem())
			.should('be.visible')
			.and('contain', mensagem)
	}
})