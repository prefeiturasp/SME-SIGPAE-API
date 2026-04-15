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
	const timestamp = new Date().getTime()

	// Dados básicos
	cy.get(Cadastro_Empresas_Locators.inputs.nomeEmpresa).type(`Cypress ${timestamp}`)
	cy.get(Cadastro_Empresas_Locators.inputs.nome_usual).type(`Cypress ${timestamp}`)

	// ⚠️ CNPJ fake (pode precisar ajustar depois)
	cy.get(Cadastro_Empresas_Locators.inputs.cnpj).type(
		'11' +
			Math.floor(Math.random() * 999999999)
				.toString()
				.padStart(9, '0') +
			'0001',
	)

	// CEP → preenche automaticamente endereço
	cy.get(Cadastro_Empresas_Locators.inputs.cep).clear().type('01001000')

	// Validação do preenchimento automático
	cy.get(Cadastro_Empresas_Locators.inputs.endereco, { timeout: 10000 })
		.should('have.value', 'Praça da Sé')

	cy.get(Cadastro_Empresas_Locators.inputs.bairro)
		.should('have.value', 'Sé')

	cy.get(Cadastro_Empresas_Locators.inputs.cidade)
		.should('have.value', 'São Paulo')

	cy.get(Cadastro_Empresas_Locators.inputs.estado)
		.should('have.value', 'SP')

	// Complementares
	cy.get(Cadastro_Empresas_Locators.inputs.numero).type('100')
	cy.get(Cadastro_Empresas_Locators.inputs.complemento).type('Sala 1')

	// Empresa
	cy.get(Cadastro_Empresas_Locators.inputs.telefone_empresa).type('11999999999')
	cy.get(Cadastro_Empresas_Locators.inputs.email_empresa).type('empresa@teste.com')

	// Responsável
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_email).type('responsavel@teste.com')
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_nome).type('Responsável Teste')
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_cpf).type(
		Math.floor(Math.random() * 99999999999)
			.toString()
			.padStart(11, '0'),
	)
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_telefone).type('11988888888')
	cy.get(Cadastro_Empresas_Locators.inputs.responsavel_cargo).type('Gerente Teste')

	// Representante legal
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_nome).type('Representante Legal Teste')
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_telefone).type('11977777777')
	cy.get(Cadastro_Empresas_Locators.inputs.rep_legal_email).type('representante@teste.com')

	// Nutricionista
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_nome).type(
		'Nutricionista Responsável Teste',
	)
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_crn).type('CRN12345')
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_telefone).type('11966666666')
	cy.get(Cadastro_Empresas_Locators.inputs.nutri_responsavel_email).type(
		'nutricionista@teste.com',
	)
})

Quando('clico no botão Salvar', function () {
	cy.intercept('POST', '**/api/terceirizadas/**').as('postTerceirizada')
	cy.get(Cadastro_Empresas_Locators.buttons.salvar).click()
})

Quando('confirmo a ação no modal de confirmação', function () {
	cy.get(Cadastro_Empresas_Locators.modais.confirmacao).click()
})

Entao('devo visualizar a mensagem {string}', function (mensagem) {
	cy.wait('@postTerceirizada').then(({ response }) => {
		cy.log(`STATUS: ${response.statusCode}`)
		cy.log(`BODY: ${JSON.stringify(response.body)}`)

		expect(response.statusCode).to.eq(201)
	})

	cy.contains(Cadastro_Empresas_Locators.mensagens.sucesso, mensagem, {
		timeout: 10000,
	})
		.should('be.visible')
		.and('contain', mensagem)
})