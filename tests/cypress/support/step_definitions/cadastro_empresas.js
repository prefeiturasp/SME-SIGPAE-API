import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
import { Menu_Lateral_Locators } from '../locators/menu_lateral_locators'
import { Cadastro_Empresas_Locators } from '../locators/cadastro_empresas_locators'

const Dado = Given
const Quando = When
const Entao = Then

Quando('acesso o menu Cadastros > Empresas', function () {
	cy.get(Menu_Lateral_Locators.cadastros).click()
	cy.get(Menu_Lateral_Locators.cadastros_empresas).click()
})

Quando('preencho os campos obrigatórios de cadastro da empresa', function () {
	cy.get(Cadastro_Empresas_Locators.inputs.nomeEmpresa).type(
		'Cypress ' + new Date().getTime(),
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nome_usual).type(
		'Cypress ' + new Date().getTime(),
	)
	cy.get(Cadastro_Empresas_Locators.inputs.cnpj).type(
		'11' +
			Math.floor(Math.random() * 999999999)
				.toString()
				.padStart(9, '0') +
			'0001',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.cep).type('01001000')
	cy.get(Cadastro_Empresas_Locators.inputs.numero).type('100')
	cy.get(Cadastro_Empresas_Locators.inputs.telefone_empresa).type('11999999999')
	cy.get(Cadastro_Empresas_Locators.inputs.email_empresa).type(
		'empresa@teste.com',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_email).type(
		'responsavel@teste.com',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_nome).type(
		'Responsável Teste',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_cpf).type(
		Math.floor(Math.random() * 99999999999)
			.toString()
			.padStart(11, '0'),
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_telefone).type(
		'11988888888',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_cargo).type(
		'Gerente Teste',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_nome).type(
		'Representante Legal Teste',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_telefone).type(
		'11977777777',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_email).type(
		'representante@teste.com',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_nome).type(
		'Nutricionista Responsável Teste',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_crn).type(
		'CRN12345',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_telefone).type(
		'11966666666',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_email).type(
		'nutricionista@teste.com',
	)
})

Quando('clico no botão Salvar', function () {
	cy.get(Cadastro_Empresas_Locators.buttons.salvar).click()
})

Quando('confirmo a ação no modal de confirmação', function () {
	cy.get(Cadastro_Empresas_Locators.modais.confirmacao).click()
})

Entao('devo visualizar a mensagem {string}', function (mensagem) {
	cy.contains(Cadastro_Empresas_Locators.mensagens.sucesso, mensagem)
		.should('be.visible')
		.and('contain', mensagem)
})
