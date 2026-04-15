import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const Dado = Given
const Quando = When
const Entao = Then

function obterUsuarioPorPerfil(perfil) {
	const usuarios = {
		COORDENADOR_LOGISTICA: Cypress.config('usuario_coordenador_logistica'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: Cypress.config(
			'usuario_coordenador_codae_dilog_logistica',
		),
		COORDENADOR_SUPERVISAO_NUTRICAO: Cypress.config(
			'usuario_coordenador_supervisao_nutricao',
		),
		DILOG_CRONOGRAMA: Cypress.config('usuario_dilog_cronograma'),
		DILOG_QUALIDADE: Cypress.config('usuario_dilog_qualidade'),
		ABASTECIMENTO: Cypress.config('usuario_abastecimento'),
		DIRETOR_UE: Cypress.config('usuario_diretor_ue'),
		CODAE: Cypress.config('usuario_codae'),
		GPCODAE: Cypress.config('usuario_gpcodae'),
		DRE: Cypress.config('usuario_dre'),

		USUARIO_INVALIDO: '3256563',
		SENHA_INVALIDA: Cypress.config('usuario_coordenador_logistica'),
		USUARIO_INEXISTENTE: '11111111111',
		USUARIO_EM_BRANCO: '',
		SENHA_EM_BRANCO: Cypress.config('usuario_coordenador_logistica'),
	}

	return usuarios[perfil]
}

function obterSenhaPorPerfil(perfil) {
	const senhas = {
		COORDENADOR_LOGISTICA: Cypress.config('senha'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: Cypress.config('senha'),
		COORDENADOR_SUPERVISAO_NUTRICAO: Cypress.config('senha'),
		DILOG_CRONOGRAMA: Cypress.config('senha'),
		DILOG_QUALIDADE: Cypress.config('senha'),
		ABASTECIMENTO: Cypress.config('senha'),
		DIRETOR_UE: Cypress.config('senha'),
		CODAE: Cypress.config('senha'),
		GPCODAE: Cypress.config('senha'),
		DRE: Cypress.config('senha'),

		USUARIO_INVALIDO: 'dsaa',
		SENHA_INVALIDA: 'admin',
		USUARIO_INEXISTENTE: 'senhainv',
		USUARIO_EM_BRANCO: Cypress.config('senha'),
		SENHA_EM_BRANCO: '',
	}

	return senhas[perfil]
}

Dado('que acesso o sistema', function () {
	cy.login_sme('web')
})

Quando(
	'informo os dados do usuário {string} no dispositivo {string}',
	function (perfil, device) {
		const usuario = obterUsuarioPorPerfil(perfil)
		const senha = obterSenhaPorPerfil(perfil)

		expect(usuario, `Usuário não mapeado para o perfil ${perfil}`).to.not.be
			.undefined
		expect(senha, `Senha não mapeada para o perfil ${perfil}`).to.not.be
			.undefined

		cy.dados_de_login(usuario, senha)
	},
)

Quando('clico no botão acessar', function () {
	cy.clicar_botao()
})

Entao('sistema apresenta {string}', function (mensagem) {
	cy.validar_mensagem(mensagem)
})