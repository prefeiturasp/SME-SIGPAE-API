import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
import { Cadastro_Empresas_Locators } from '../locators/cadastro_empresas_locators'
import { Menu_Lateral_Locators } from '../locators/menu_lateral_locators'

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

Quando('acesso o menu Cadastros > Empresas', function () {
	acessarSubmenuEmpresas()
})

Quando('preencho os campos obrigatorios de cadastro da empresa', function () {
	const timestamp = new Date().getTime()

	const cnpjFake =
		'11' +
		Math.floor(Math.random() * 999999999)
			.toString()
			.padStart(9, '0') +
		'0001'

	const cpfFake = Math.floor(Math.random() * 99999999999)
		.toString()
		.padStart(11, '0')

	cy.get(Cadastro_Empresas_Locators.inputs.nomeEmpresa, { timeout: 15000 })
		.should('be.visible')
		.type(`Empresa Cypress ${timestamp}`)

	cy.get(Cadastro_Empresas_Locators.inputs.nome_usual, { timeout: 15000 })
		.should('be.visible')
		.type(`Fantasia ${timestamp}`)

	cy.get(Cadastro_Empresas_Locators.inputs.cnpj, { timeout: 15000 })
		.should('be.visible')
		.type(cnpjFake)

	cy.get('select').eq(0).select(1)
	cy.get('select').eq(1).select(1)
	cy.get('select').eq(2).select(1)

	cy.get(Cadastro_Empresas_Locators.inputs.cep, { timeout: 15000 })
		.should('be.visible')
		.clear()
		.type('01001000')
		.blur()

	cy.wait(1000)

	cy.get(Cadastro_Empresas_Locators.inputs.endereco, { timeout: 15000 })
		.should('be.visible')

	preencherOuValidarCampoBloqueado(
		Cadastro_Empresas_Locators.inputs.endereco,
		'Pra',
	)

	cy.get(Cadastro_Empresas_Locators.inputs.numero, { timeout: 15000 })
		.should('be.visible')
		.type('100')

	cy.get(Cadastro_Empresas_Locators.inputs.complemento, { timeout: 15000 })
		.should('be.visible')
		.type('Sala 1')

	preencherOuValidarCampoBloqueado(
		Cadastro_Empresas_Locators.inputs.bairro,
		'S',
	)

	preencherOuValidarCampoBloqueado(
		Cadastro_Empresas_Locators.inputs.cidade,
		'Sao Paulo',
	)

	preencherOuValidarCampoBloqueado(
		Cadastro_Empresas_Locators.inputs.estado,
		'SP',
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


Quando('clico no botao Salvar', function () {
	cy.intercept('POST', '**/api/empresas-nao-terceirizadas/**').as('postEmpresa')

	cy.get(Cadastro_Empresas_Locators.buttons.salvar, { timeout: 15000 })
		.scrollIntoView()
		.should('be.visible')
		.and('not.be.disabled')
		.click()
})

Quando('confirmo a acao no modal de confirmacao', function () {
	cy.get(Cadastro_Empresas_Locators.modais.confirmacao, { timeout: 15000 })
		.should('be.visible')
		.click()
})


Entao('devo visualizar a mensagem {string}', function (mensagem) {
	cy.wait('@postEmpresa', { timeout: 20000 })
		.its('response.statusCode')
		.should('eq', 201)

	cy.get(Cadastro_Empresas_Locators.mensagens.sucesso, { timeout: 15000 })
		.should('be.visible')
		.and('contain', mensagem)
})
