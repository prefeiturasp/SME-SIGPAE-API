import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
import { Menu_Lateral_Locators } from '../locators/menu_lateral_locators'
import { Cadastro_Empresas_Locators } from '../locators/cadastro_empresas_locators'

const Dado = Given
const Quando = When
const Entao = Then

function preencherCampo(seletor, valor) {
	cy.get(seletor, { timeout: 15000 })
		.filter(':visible')
		.first()
		.scrollIntoView()
		.should('be.visible')
		.clear({ force: true })
		.type(valor, { force: true })
}

function preencherCampoControlado(seletor, valor) {
	cy.get(seletor, { timeout: 15000 })
		.filter(':visible')
		.first()
		.scrollIntoView()
		.should('be.visible')
		.then(($input) => {
			if ($input.is(':disabled')) {
				const input = $input[0]
				const nativeSetter = Object.getOwnPropertyDescriptor(
					window.HTMLInputElement.prototype,
					'value',
				).set

				input.removeAttribute('disabled')
				input.focus()
				nativeSetter.call(input, valor)
				input.dispatchEvent(new Event('input', { bubbles: true }))
				input.dispatchEvent(new Event('change', { bubbles: true }))
				input.dispatchEvent(new Event('blur', { bubbles: true }))
				return
			}

			cy.wrap($input)
				.click({ force: true })
				.type('{selectall}{backspace}', { force: true })
				.type(valor, { force: true, delay: 0 })
				.trigger('blur')
		})

	cy.get('body').click(0, 0, { force: true })
}

function preencherCampoSeExistir(seletor, valor) {
	cy.get('body').then(($body) => {
		if ($body.find(seletor).length) {
			preencherCampo(seletor, valor)
		}
	})
}

function selecionarPorRotulo(rotulo, valor) {
	cy.contains('label', rotulo, { timeout: 15000 })
		.should('be.visible')
		.parent()
		.find('select')
		.first()
		.should('be.visible')
		.select(valor)
}

function selecionarPrimeiraOpcaoValidaPorRotulo(rotulo) {
	cy.contains('label', rotulo, { timeout: 15000 })
		.should('be.visible')
		.parent()
		.find('select')
		.first()
		.should('be.visible')
		.then(($select) => {
			const opcaoValida = [...$select[0].options].find((option) => {
				const texto = (option.text || '').trim().toLowerCase()
				return option.value && !texto.includes('selecione')
			})

			expect(opcaoValida, `opcao valida para ${rotulo}`).to.exist
			cy.wrap($select).select(opcaoValida.value)
		})
}

function preencherCampoDataPorPlaceholder(placeholder, valor) {
	cy.contains('Contratos')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get(`input[placeholder="${placeholder}"]`, { timeout: 15000 })
				.filter(':visible')
				.first()
				.scrollIntoView()
				.should('be.visible')
				.then(($input) => {
					const input = $input[0]
					const nativeSetter = Object.getOwnPropertyDescriptor(
						window.HTMLInputElement.prototype,
						'value',
					).set

					input.removeAttribute('readonly')
					input.focus()
					nativeSetter.call(input, valor)
					input.dispatchEvent(new Event('input', { bubbles: true }))
					input.dispatchEvent(new Event('change', { bubbles: true }))
					input.dispatchEvent(new Event('blur', { bubbles: true }))
				})
		})

	cy.get('body').click(0, 0, { force: true })
}

function preencherCamposContrato(numeroProcesso, numeroContrato) {
	cy.contains('Contratos')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get('input:not([placeholder="De"]):not([placeholder="Até"])', {
				timeout: 15000,
			})
				.filter(':visible')
				.then(($inputs) => {
					cy.wrap($inputs.eq(0))
						.should('be.visible')
						.clear({ force: true })
						.type(numeroProcesso, { force: true })

					cy.wrap($inputs.eq(1))
						.should('be.visible')
						.clear({ force: true })
						.type(numeroContrato, { force: true })
				})
		})
}

function adicionarContratoEFecharLinhaVazia() {
	cy.contains('button', 'Adicionar', { timeout: 15000 })
		.scrollIntoView()
		.should('be.visible')
		.click()

	cy.contains('Contratos')
		.parent()
		.within(() => {
			cy.get('input[placeholder="De"]').then(($datasInicio) => {
				if ($datasInicio.length > 1) {
					cy.contains('button', 'Remover')
						.last()
						.scrollIntoView()
						.should('be.visible')
						.click()
				}
			})
		})
}

function acessarSubmenuEmpresas() {
	cy.get('body', { timeout: 15000 }).then(($body) => {
		const itemEmpresasVisivel =
			$body.find(`${Menu_Lateral_Locators.cadastros_empresas}:visible`).length > 0

		if (!itemEmpresasVisivel) {
			const menuConfiguracoesVisivel =
				$body.find(`${Menu_Lateral_Locators.configuracoes}:visible`).length > 0

			if (menuConfiguracoesVisivel) {
				cy.get(Menu_Lateral_Locators.configuracoes, { timeout: 15000 })
					.filter(':visible')
					.first()
					.click({ force: true })
			}

			cy.get(Menu_Lateral_Locators.cadastros, { timeout: 15000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.click({ force: true })
		}
	})

	cy.get('body', { timeout: 15000 }).then(($body) => {
		const possuiLinkPorLocator =
			$body.find(`${Menu_Lateral_Locators.cadastros_empresas}:visible`).length > 0

		if (possuiLinkPorLocator) {
			cy.get(Menu_Lateral_Locators.cadastros_empresas, { timeout: 15000 })
				.filter(':visible')
				.first()
				.should('exist')
				.click({ force: true })
			return
		}

		cy.visit('/configuracoes/cadastros/empresa')
	})

	cy.location('pathname', { timeout: 20000 }).should(
		'include',
		'/configuracoes/cadastros/empresa',
	)
}

Dado('que acesso o sistema', function () {
	const usuario = Cypress.env('usuario_dilog_cronograma')
	const senha = Cypress.env('senha')

	cy.clearCookies()
	cy.clearLocalStorage()
	cy.login_sme('web')

	cy.location('pathname', { timeout: 15000 }).then((pathname) => {
		if (pathname === '/login') {
			cy.get('[data-cy="login"]', { timeout: 15000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.clear()
				.type(usuario)

			cy.get('[data-cy="password"]', { timeout: 15000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.clear()
				.type(senha, { log: false })

			cy.get('[data-cy="Acessar"]', { timeout: 15000 })
				.filter(':visible')
				.first()
				.should('be.visible')
				.click()
		}
	})

	cy.url({ timeout: 20000 }).should('not.include', '/login')
})

Quando('acesso o menu Cadastros > Empresas', function () {
	acessarSubmenuEmpresas()
})

Quando('preencho os campos obrigatorios de cadastro da empresa', function () {
	const timestamp = new Date().getTime()
	const cpfFake = Math.floor(Math.random() * 99999999999)
		.toString()
		.padStart(11, '0')

	cy.get(Cadastro_Empresas_Locators.inputs.nomeEmpresa).type(`Cypress ${timestamp}`)
	cy.get(Cadastro_Empresas_Locators.inputs.nome_usual).type(`Cypress ${timestamp}`)

	cy.get(Cadastro_Empresas_Locators.inputs.cnpj).type(
		'11' +
			Math.floor(Math.random() * 999999999)
				.toString()
				.padStart(9, '0') +
			'0001',
	)

	cy.get(Cadastro_Empresas_Locators.inputs.cep)
		.filter(':visible')
		.first()
		.clear({ force: true })
		.type('01001000', { force: true })
		.blur()

	preencherCampoControlado(Cadastro_Empresas_Locators.inputs.endereco, 'Praca da Se')
	preencherCampoControlado(Cadastro_Empresas_Locators.inputs.bairro, 'Se')
	preencherCampoControlado(Cadastro_Empresas_Locators.inputs.cidade, 'Sao Paulo')
	preencherCampoControlado(Cadastro_Empresas_Locators.inputs.estado, 'SP')

	cy.get(Cadastro_Empresas_Locators.inputs.endereco, { timeout: 10000 })
		.filter(':visible')
		.first()
		.should('have.value', 'Praca da Se')

	cy.get(Cadastro_Empresas_Locators.inputs.bairro)
		.filter(':visible')
		.first()
		.should('have.value', 'Se')

	cy.get(Cadastro_Empresas_Locators.inputs.cidade)
		.filter(':visible')
		.first()
		.should('have.value', 'Sao Paulo')

	cy.get(Cadastro_Empresas_Locators.inputs.estado)
		.filter(':visible')
		.first()
		.should('have.value', 'SP')

	cy.get(Cadastro_Empresas_Locators.inputs.numero).type('100')
	cy.get(Cadastro_Empresas_Locators.inputs.complemento).type('Sala 1')
	selecionarPrimeiraOpcaoValidaPorRotulo('Tipo de Serviço')
	selecionarPrimeiraOpcaoValidaPorRotulo('Tipo de Empresa')
	selecionarPrimeiraOpcaoValidaPorRotulo('Tipo de Alimento')

	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.telefone_empresa,
		'11999999999',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.email_empresa,
		`empresa${timestamp}@teste.com`,
	)

	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.responsavel_email,
		'responsavel@teste.com',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.responsavel_nome,
		'Responsavel Teste',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.responsavel_cpf,
		cpfFake,
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.responsavel_telefone,
		'49999056098',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.responsavel_cargo,
		'Gerente Teste',
	)

	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.rep_legal_nome,
		'Representante Legal Teste',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.rep_legal_telefone,
		'11977777777',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.rep_legal_email,
		'representante@teste.com',
	)

	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.nutri_responsavel_nome,
		'Nutricionista Responsavel Teste',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.nutri_responsavel_crn,
		'CRN12345',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.nutri_responsavel_telefone,
		'11966666666',
	)
	preencherCampoSeExistir(
		Cadastro_Empresas_Locators.inputs.nutri_responsavel_email,
		'nutricionista@teste.com',
	)

	cy.contains('Dados do Representante do Contrato')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get('input:visible').then(($inputs) => {
				cy.wrap($inputs.eq(0)).clear().type('Representante Teste')
				cy.wrap($inputs.eq(1)).clear().type(cpfFake)
				cy.wrap($inputs.eq(2)).clear().type('Gerente')
				cy.wrap($inputs.eq(3)).clear().type('11988888888')
				cy.wrap($inputs.eq(4))
					.clear()
					.type(`representante${timestamp}@teste.com`)
			})
		})

	cy.contains('Contatos')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get('input:visible').then(($inputs) => {
				cy.wrap($inputs.eq(0)).clear().type('Contato Teste')
				cy.wrap($inputs.eq(1)).clear().type('11977777777')
				cy.wrap($inputs.eq(2)).clear().type(`contato${timestamp}@teste.com`)
			})
		})

	cy.contains('Contratos').scrollIntoView()
	preencherCamposContrato(`${timestamp}`, `CONT-${timestamp}`)
	preencherCampoDataPorPlaceholder('De', '01/01/2025')
	preencherCampoDataPorPlaceholder('Até', '31/12/2025')
	selecionarPorRotulo('Modalidade', 'Emergencial')
	selecionarPorRotulo('Programa', 'Alimentação Escolar')
	selecionarPorRotulo('Situação', 'Ativo')
	adicionarContratoEFecharLinhaVazia()
})

Quando('clico no botao Salvar', function () {
	cy.intercept('POST', '**/api/empresas-nao-terceirizadas/**').as('postEmpresa')

	cy.get(Cadastro_Empresas_Locators.buttons.salvar, { timeout: 30000 })
		.scrollIntoView()
		.should('be.visible')
		.should(($botao) => {
			expect($botao).not.to.be.disabled
		})
		.click()
})

Quando('confirmo a acao no modal de confirmacao', function () {
	cy.get(Cadastro_Empresas_Locators.modais.confirmacao, { timeout: 15000 })
		.should('be.visible')
		.click()
})

Entao('devo visualizar a mensagem {string}', function (mensagem) {
	cy.wait('@postEmpresa').then(({ response }) => {
		cy.log(`STATUS: ${response.statusCode}`)
		cy.log(`BODY: ${JSON.stringify(response.body)}`)
	})
	cy.get(Cadastro_Empresas_Locators.mensagens.sucesso, { timeout: 15000 })
		.should('be.visible')
		.and('contain', mensagem)
})
