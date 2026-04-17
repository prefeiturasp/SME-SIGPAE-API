import Login_SME_Localizadores from '../locators/login_locators'

const login_SME_Localizadores = new Login_SME_Localizadores()
const seletorCampoUsuario = `${login_SME_Localizadores.campo_usuario()}, [data-cy="login"]`
const seletoresErroLogin = [
	login_SME_Localizadores.mensagem_erro(),
	'.Toastify__toast',
	'[role="alert"]',
].join(', ')

function visitarTelaLogin() {
	cy.visit('/login', {
		onBeforeLoad(win) {
			win.localStorage.clear()
			win.sessionStorage.clear()
		},
	})
}

Cypress.Commands.add('login_sme', (device) => {
	cy.configurar_visualizacao(device)
	cy.clearCookies()
	cy.clearLocalStorage()
	cy.clearAllSessionStorage()

	visitarTelaLogin()

	cy.location('pathname', { timeout: 60000 }).then((pathname) => {
		if (pathname !== '/login') {
			visitarTelaLogin()
		}
	})
})

Cypress.Commands.add('dados_de_login', (usuario, senha) => {
	cy.location('pathname', { timeout: 60000 }).then((pathname) => {
		if (pathname !== '/login') {
			visitarTelaLogin()
		}
	})

	cy.get('body', { timeout: 15000 }).then(($body) => {
		const possuiCampoUsuario = $body.find(seletorCampoUsuario).length > 0

		if (!possuiCampoUsuario) {
			visitarTelaLogin()
		}
	})

	cy.get(seletorCampoUsuario, { timeout: 15000 })
		.filter(':visible')
		.should('have.length.at.least', 1)

	cy.get(seletorCampoUsuario)
		.filter(':visible')
		.first()
		.should('be.visible')
		.clear()

	cy.get(login_SME_Localizadores.campo_senha(), { timeout: 15000 })
		.filter(':visible')
		.first()
		.should('be.visible')
		.clear()

	if (usuario) {
		cy.get(seletorCampoUsuario)
			.filter(':visible')
			.first()
			.type(usuario)
	}

	if (senha) {
		cy.get(login_SME_Localizadores.campo_senha())
			.filter(':visible')
			.first()
			.type(senha)
	}
})

Cypress.Commands.add('clicar_botao', () => {
	cy.get(login_SME_Localizadores.botao_acessar())
		.filter(':visible')
		.first()
		.should('be.visible')
		.click()
})

Cypress.Commands.add('validar_mensagem', (mensagem) => {
	if (mensagem === 'Usuário ou senha inválidos') {
		cy.location('pathname', { timeout: 60000 }).should('eq', '/login')
		cy.get(seletoresErroLogin, { timeout: 60000 })
			.filter(':visible')
			.should('have.length.at.least', 1)
	} else if (mensagem === 'Campo obrigatório') {
		cy.contains(
			login_SME_Localizadores.mensagem_erro_campo_em_branco(),
			mensagem,
			{ timeout: 60000 },
		).should('be.visible')
	} else if (mensagem === 'sucesso') {
		cy.location('pathname', { timeout: 60000 }).should('not.eq', '/login')
		cy.get(login_SME_Localizadores.mensagem(), { timeout: 60000 })
			.filter(':visible')
			.first()
			.should('be.visible')
			.invoke('text')
			.should('not.be.empty')
	} else {
		cy.get(login_SME_Localizadores.mensagem())
			.filter(':visible')
			.first()
			.should('be.visible')
			.and('contain', mensagem)
	}
})