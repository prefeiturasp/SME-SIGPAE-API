import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const Dado = Given
const Quando = When
const Entao = Then

Dado('eu acesso o sistema com a visualização {string}', function (device) {
	cy.login_sme(device)
})

Dado(
	'informo os dados nos campos {string} e {string}',
	function (usuario, senha) {
		cy.dados_de_login(usuario, senha)
	},
)

Quando('clico no botão acessar', function () {
	cy.clicar_botao()
})

Entao(
	'sistema realiza validacao necessesaria {string} para o cenario {string}',
	function (mensagem) {
		cy.validar_mensagem(mensagem)
	},
)

Dado(
	'que estou logado no sistema com usuário {string} e {string}',

	function (usuario, senha) {
		if (usuario === 'Cronograma') {
			usuario = Cypress.config('usuario_dilog_cronograma')
		} else if (usuario === 'Abastecimento') {
			usuario = Cypress.config('usuario_abastecimento')
		} else if (usuario === 'Diretor UE') {
			usuario = Cypress.config('usuario_diretor_ue')
		} else if (usuario === 'Codae') {
			usuario = Cypress.config('usuario_codae')
		} else if (usuario === 'GP Codae') {
			usuario = Cypress.config('usuario_gpcodae')
		} else if (usuario === 'DRE') {
			usuario = Cypress.config('usuario_dre')
		}

		cy.login_sme('web')
		cy.dados_de_login(usuario, Cypress.config('senha'))
		cy.clicar_botao()
	},
)
