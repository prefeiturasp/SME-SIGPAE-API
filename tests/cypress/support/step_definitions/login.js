import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const Dado = Given
const Quando = When
const Entao = Then

function obterUsuarioPorPerfil(perfil) {
	const usuarios = {
		COORDENADOR_LOGISTICA: Cypress.env('usuario_coordenador_logistica'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: Cypress.env(
			'usuario_coordenador_codae_dilog_logistica',
		),
		COORDENADOR_SUPERVISAO_NUTRICAO: Cypress.env(
			'usuario_coordenador_supervisao_nutricao',
		),
		DILOG_CRONOGRAMA: Cypress.env('usuario_dilog_cronograma'),
		DILOG_QUALIDADE: Cypress.env('usuario_dilog_qualidade'),
		ABASTECIMENTO: Cypress.env('usuario_abastecimento'),
		DIRETOR_UE: Cypress.env('usuario_diretor_ue'),
		CODAE: Cypress.env('usuario_codae'),
		GPCODAE: Cypress.env('usuario_gpcodae'),
		DRE: Cypress.env('usuario_dre'),

		USUARIO_INVALIDO: '3256563',
		SENHA_INVALIDA: Cypress.env('usuario_coordenador_logistica'),
		USUARIO_INEXISTENTE: '11111111111',
		USUARIO_EM_BRANCO: '',
		SENHA_EM_BRANCO: Cypress.env('usuario_coordenador_logistica'),
	}

	return usuarios[perfil]
}

function obterSenhaPorPerfil(perfil) {
	const senhas = {
		COORDENADOR_LOGISTICA: Cypress.env('senha'),
		COORDENADOR_CODAE_DILOG_LOGISTICA: Cypress.env('senha'),
		COORDENADOR_SUPERVISAO_NUTRICAO: Cypress.env('senha'),
		DILOG_CRONOGRAMA: Cypress.env('senha'),
		DILOG_QUALIDADE: Cypress.env('senha'),
		ABASTECIMENTO: Cypress.env('senha'),
		DIRETOR_UE: Cypress.env('senha'),
		CODAE: Cypress.env('senha'),
		GPCODAE: Cypress.env('senha'),
		DRE: Cypress.env('senha'),

		USUARIO_INVALIDO: 'dsaa',
		SENHA_INVALIDA: 'admin',
		USUARIO_INEXISTENTE: 'senhainv',
		USUARIO_EM_BRANCO: Cypress.env('senha'),
		SENHA_EM_BRANCO: '',
	}

	return senhas[perfil]
}

Dado('que acesso o sistema', function () {
	cy.login_sme('web')
})

Quando(
	'informo os dados do usuario {string} no dispositivo {string}',
	function (perfil, device) {
		const usuario = obterUsuarioPorPerfil(perfil)
		const senha = obterSenhaPorPerfil(perfil)

		expect(usuario, `Usuario nao mapeado para o perfil ${perfil}`).to.not.be
			.undefined
		expect(senha, `Senha nao mapeada para o perfil ${perfil}`).to.not.be
			.undefined

		cy.dados_de_login(usuario, senha)
	},
)

Quando('clico no botao acessar', function () {
	cy.clicar_botao()
})

Entao('sistema apresenta {string}', function (mensagem) {
	cy.validar_mensagem(mensagem)
})