import Login_SME_Localizadores from '../locators/login_locators'

const login_SME_Localizadores = new Login_SME_Localizadores()
const seletoresUsuario = ['[data-cy="login"]', 'input.input-login']
const seletoresSenha = ['[data-cy="password"]', 'input[type="password"]']

function possuiElementoVisivel($body, seletores) {
	return seletores.some((item) => $body.find(item).filter(':visible').length > 0)
}

function obterPrimeiroSeletorDisponivel(seletores, nomeCampo, timeout = 10000) {
	return cy.get('body', { timeout }).then(($body) => {
		const seletor = seletores.find(
			(item) => $body.find(item).filter(':visible').length > 0,
		)

		expect(
			seletor,
			`Campo ${nomeCampo} nao encontrado. Seletores verificados: ${seletores.join(', ')}`,
		).to.exist

		return seletor
	})
}

function visitarTelaLogin() {
	cy.visit('/login', {
		onBeforeLoad(win) {
			win.localStorage.clear()
			win.sessionStorage.clear()
		},
	})
}

function garantirTelaDeLogin() {
	cy.get('body', { timeout: 15000 }).then(($body) => {
		if (possuiElementoVisivel($body, seletoresUsuario)) {
			return
		}

		const possuiAcaoSair =
			$body.find('button, a, span, div').filter((_, element) => {
				return element.innerText?.trim() === 'Sair'
			}).length > 0

		if (possuiAcaoSair) {
			cy.contains('button, a, span, div', /^Sair$/, { timeout: 15000 })
				.filter(':visible')
				.first()
				.click({ force: true })
		}

		visitarTelaLogin()
		cy.get(seletoresUsuario.join(', '), { timeout: 15000 })
			.filter(':visible')
			.should('have.length.at.least', 1)
	})
}

Cypress.Commands.add('login_sme', (device) => {
	cy.configurar_visualizacao(device)
	visitarTelaLogin()
	garantirTelaDeLogin()
})

Cypress.Commands.add('dados_de_login', (usuario, senha) => {
	garantirTelaDeLogin()

	obterPrimeiroSeletorDisponivel(seletoresUsuario, 'usuario').then(
		(seletorUsuario) => {
			cy.get(seletorUsuario, { timeout: 10000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.clear()

			if (usuario) {
				cy.get(seletorUsuario).filter(':visible').first().type(usuario)
			}
		},
	)

	obterPrimeiroSeletorDisponivel(seletoresSenha, 'senha').then(
		(seletorSenha) => {
			cy.get(seletorSenha, { timeout: 10000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.clear()

			if (senha) {
				cy.get(seletorSenha).filter(':visible').first().type(senha, {
					log: false,
				})
			}
		},
	)
})

Cypress.Commands.add('clicar_botao', () => {
	cy.get(login_SME_Localizadores.botao_acessar())
		.should('be.visible')
		.click()
})

Cypress.Commands.add('validar_mensagem', (mensagem) => {
	if (mensagem === 'N\u00e3o foi poss\u00edvel logar no sistema') {
		cy.get(login_SME_Localizadores.mensagem_erro())
			.should('be.visible')
			.contains(mensagem)
	} else if (mensagem === 'Campo obrigat\u00f3rio') {
		cy.get(login_SME_Localizadores.mensagem_erro_campo_em_branco())
			.should('be.visible')
			.contains(mensagem)
	} else {
		cy.get(login_SME_Localizadores.mensagem())
			.should('be.visible')
			.and('contain', mensagem)
	}
})
