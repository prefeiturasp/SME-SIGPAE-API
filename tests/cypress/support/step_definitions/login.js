import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const Dado = Given
const Quando = When
const Entao = Then

function obterCredencial(chave) {
	return Cypress.env(chave)
}

function obterUsuarioPorPerfil(perfil) {
	const usuarios = {
		COORDENADOR_LOGISTICA: obterCredencial('usuario_coordenador_logistica'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: obterCredencial(
			'usuario_coordenador_codae_dilog_logistica',
		),
		COORDENADOR_SUPERVISAO_NUTRICAO: obterCredencial(
			'usuario_coordenador_supervisao_nutricao',
		),
		DILOG_CRONOGRAMA: obterCredencial('usuario_dilog_cronograma'),
		DILOG_QUALIDADE: obterCredencial('usuario_dilog_qualidade'),
		ABASTECIMENTO: obterCredencial('usuario_abastecimento'),
		DIRETOR_UE: obterCredencial('usuario_diretor_ue'),
		CODAE: obterCredencial('usuario_codae'),
		GPCODAE: obterCredencial('usuario_gpcodae'),
		DRE: obterCredencial('usuario_dre'),

		USUARIO_INVALIDO: '3256563',
		SENHA_INVALIDA: obterCredencial('usuario_coordenador_logistica'),
		USUARIO_INEXISTENTE: '11111111111',
		USUARIO_EM_BRANCO: '',
		SENHA_EM_BRANCO: obterCredencial('usuario_coordenador_logistica'),
	}

	return usuarios[perfil]
}

function obterSenhaPorPerfil(perfil) {
	const senhas = {
		COORDENADOR_LOGISTICA: obterCredencial('senha'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: obterCredencial('senha'),
		COORDENADOR_SUPERVISAO_NUTRICAO: obterCredencial('senha'),
		DILOG_CRONOGRAMA: obterCredencial('senha'),
		DILOG_QUALIDADE: obterCredencial('senha'),
		ABASTECIMENTO: obterCredencial('senha'),
		DIRETOR_UE: obterCredencial('senha'),
		CODAE: obterCredencial('senha'),
		GPCODAE: obterCredencial('senha'),
		DRE: obterCredencial('senha'),

		USUARIO_INVALIDO: 'dsaa',
		SENHA_INVALIDA: 'admin',
		USUARIO_INEXISTENTE: 'senhainv',
		USUARIO_EM_BRANCO: obterCredencial('senha'),
		SENHA_EM_BRANCO: '',
	}

	return senhas[perfil]
}

Dado('que acesso o sistema', function () {
	cy.clearCookies()
	cy.clearLocalStorage()
	cy.login_sme('web')
})

Quando(
	'informo os dados do usuário {string} no dispositivo {string}',
	function (perfil, device) {
		const usuario = obterUsuarioPorPerfil(perfil)
		const senha = obterSenhaPorPerfil(perfil)

		expect(
			usuario,
			`Usuário não configurado para o perfil ${perfil}. Verifique a variável de ambiente correspondente no cypress.config.js/.env.`,
		).to.not.be.undefined

		expect(
			senha,
			`Senha não configurada para o perfil ${perfil}. Verifique a variável SENHA no cypress.config.js/.env.`,
		).to.not.be.undefined

		cy.dados_de_login(usuario, senha)
	},
)

Quando('clico no botão acessar', function () {
	cy.clicar_botao()
})

Entao('o sistema deve abrir a tela inicial', function () {
	cy.url().should('not.include', '/login')
	cy.get('#root').should('be.visible')
	cy.get('[data-cy="login"]').should('not.exist')
	cy.get('[data-cy="password"]').should('not.exist')
})

Entao('sistema apresenta {string}', function (mensagem) {
	cy.validar_mensagem(mensagem)
})
