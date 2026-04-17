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

function preencherCampoPorRotulo(rotulo, valor) {
	cy.contains('label', rotulo, { timeout: 15000 })
		.should('be.visible')
		.parent()
		.find('input')
		.filter(':visible')
		.first()
		.scrollIntoView()
		.should('be.visible')
		.clear({ force: true })
		.type(valor, { force: true })
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

function preencherCampoData(seletor, valor) {
	cy.get(seletor, { timeout: 15000 })
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
		})

	cy.get('body').click(0, 0, { force: true })
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

function preencherOuValidarCampoBloqueado(seletor, valorEsperado) {
	cy.get(seletor, { timeout: 15000 })
		.filter(':visible')
		.first()
		.should('be.visible')
		.then(($input) => {
			const campo = cy.wrap($input)

			if ($input.is(':disabled') || $input.is('[readonly]')) {
				campo.invoke('val').then((valorAtual) => {
					const normalizar = (valor) =>
						String(valor || '')
							.normalize('NFD')
							.replace(/[\u0300-\u036f]/g, '')
							.toLowerCase()

					expect(normalizar(valorAtual)).to.include(normalizar(valorEsperado))
				})
				return
			}

			campo.clear().type(valorEsperado)
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

Dado('acesso o menu Cadastros > Empresas', function () {
	acessarSubmenuEmpresas()
})

Quando(/preencho os campos obrigat[óo]rios de cadastro da empresa/, function () {
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

	cy.contains('Dados do Representante do Contrato')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get('input').eq(0).clear().type('Representante Teste')
			cy.get('input').eq(1).clear().type(cpfFake)
			cy.get('input').eq(2).clear().type('Gerente')
			cy.get('input').eq(3).clear().type('11988888888')
			cy.get('input').eq(4).clear().type(`representante${timestamp}@teste.com`)
		})

	cy.contains('Contatos')
		.scrollIntoView()
		.parent()
		.within(() => {
			cy.get('input').eq(0).clear().type('Contato Teste')
			cy.get('input').eq(1).clear().type('11977777777')
			cy.get('input').eq(2).clear().type(`contato${timestamp}@teste.com`)
		})

	cy.contains('Contratos').scrollIntoView()
	preencherCamposContrato(`${timestamp}`, `CONT-${timestamp}`)
	preencherCampoDataPorPlaceholder('De', '01/01/2025')
	preencherCampoDataPorPlaceholder('Até', '31/12/2025')
	selecionarPorRotulo('Modalidade', 'Emergencial')
	selecionarPorRotulo('Programa', 'Alimentação Escolar')
	selecionarPorRotulo('Situação', 'Ativo')
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