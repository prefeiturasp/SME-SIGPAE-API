import Login_SME_Localizadores from '../locators/login_locators'

const login_SME_Localizadores = new Login_SME_Localizadores()

Cypress.Commands.add('login_sme', (device) => {
	cy.clearCookies()
	cy.clearLocalStorage()
	cy.configurar_visualizacao(device)
	cy.visit('/login')
})

Cypress.Commands.add('dados_de_login', (usuario, senha) => {
	cy.location('pathname', { timeout: 10000 }).then((pathname) => {
		if (pathname !== '/login') {
			cy.log(`Sessão já autenticada na rota ${pathname}; pulando preenchimento do formulário.`)
			return
		}

		cy.get(login_SME_Localizadores.campo_usuario(), { timeout: 10000 })
			.should('be.visible')
			.clear()
		cy.get(login_SME_Localizadores.campo_senha(), { timeout: 10000 })
			.should('be.visible')
			.clear()

		if (usuario) {
			cy.get(login_SME_Localizadores.campo_usuario()).type(usuario)
		}

		if (senha) {
			cy.get(login_SME_Localizadores.campo_senha()).type(senha)
		}
	})
})

Cypress.Commands.add('clicar_botao', () => {
	cy.location('pathname', { timeout: 10000 }).then((pathname) => {
		if (pathname !== '/login') {
			cy.log(`Sessão já autenticada na rota ${pathname}; pulando clique no botão acessar.`)
			return
		}

		cy.get(login_SME_Localizadores.botao_acessar())
			.should('be.visible')
			.click()
	})
})

Cypress.Commands.add('validar_mensagem', (mensagem) => {
	if (mensagem === 'NÃ£o foi possÃ­vel logar no sistema') {
		cy.get(login_SME_Localizadores.mensagem_erro())
			.should('be.visible')
			.contains(mensagem)
	} else if (mensagem === 'Campo obrigatÃ³rio') {
		cy.get(login_SME_Localizadores.mensagem_erro_campo_em_branco())
			.should('be.visible')
			.contains(mensagem)
	}
})
