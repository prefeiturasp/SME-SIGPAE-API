import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'

const uuidInexistente = '00000000-0000-0000-0000-000000000000'

function dadosEmpresa() {
	const base = Array.from({ length: 12 }, () => Cypress._.random(0, 9))
	for (const pesos of [[5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]]) {
		const resto = base.reduce((soma, numero, indice) => soma + numero * pesos[indice], 0) % 11
		base.push(resto < 2 ? 0 : 11 - resto)
	}
	return {
		cnpj: base.join(''),
		nome_fantasia: `Automacao Cypress ${Date.now()}`,
		razao_social: 'Empresa de teste Cypress',
		tipo_empresa: 'CONVENCIONAL',
		tipo_servico: 'DISTRIBUIDOR_ARMAZEM',
		tipo_alimento: 'FLVO',
		contatos: [],
		contratos: [],
	}
}

function guardar(contexto, requisicao) {
	return requisicao.then((response) => {
		contexto.response = response
		if (response.status === 201 && response.body.uuid) {
			contexto.empresasCriadas = [...(contexto.empresasCriadas || []), response.body.uuid]
		}
	})
}

function cadastrar(contexto) {
	contexto.dadosEmpresa = dadosEmpresa()
	return guardar(contexto, cy.executar_empresas_nao_terceirizadas('POST', '', contexto.dadosEmpresa)).then(() => {
		expect(contexto.response.status, JSON.stringify(contexto.response.body)).to.eq(201)
		contexto.uuidEmpresa = contexto.response.body.uuid
		expect(contexto.uuidEmpresa).to.be.a('string').and.not.be.empty
	})
}

After({ tags: '@empresas_nao_terceirizadas' }, function () {
	for (const uuid of this.empresasCriadas || []) {
		cy.executar_empresas_nao_terceirizadas('DELETE', uuid).then((response) => {
			expect(response.status, 'Limpeza da empresa criada pelo cenario').to.eq(204)
		})
	}
})

Given('que estou autenticado como CODAE para empresas nao terceirizadas', () => {
	cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
})
Given('que cadastrei uma empresa nao terceirizada para o cenario', function () {
	return cadastrar(this)
})
When('cadastro uma empresa nao terceirizada', function () {
	return cadastrar(this)
})
When('atualizo a empresa nao terceirizada usando {string}', function (metodo) {
	expect(['PUT', 'PATCH']).to.include(metodo)
	this.dadosEmpresa.nome_fantasia = `Atualizada ${this.dadosEmpresa.nome_fantasia}`
	const body = metodo === 'PUT' ? this.dadosEmpresa : { nome_fantasia: this.dadosEmpresa.nome_fantasia }
	return guardar(this, cy.executar_empresas_nao_terceirizadas(metodo, this.uuidEmpresa, body))
})
When('excluo a empresa nao terceirizada criada', function () {
	cy.executar_empresas_nao_terceirizadas('DELETE', this.uuidEmpresa).then((response) => {
		this.response = response
		if (response.status === 204) this.empresasCriadas = this.empresasCriadas.filter((uuid) => uuid !== this.uuidEmpresa)
	})
})
Then('a empresa nao terceirizada nao pode ser excluida novamente', function () {
	cy.executar_empresas_nao_terceirizadas('DELETE', this.uuidEmpresa).then((response) => {
		expect(response.status).to.eq(404)
	})
})
When('executo {string} em empresas nao terceirizadas na rota {string} com acesso {string}', function (metodo, rota, acesso) {
	const autenticado = acesso === 'autenticado'
	if (!autenticado) cy.clearCookies()
	const body = ['POST', 'PUT', 'PATCH'].includes(metodo) ? dadosEmpresa() : undefined
	return guardar(this, cy.executar_empresas_nao_terceirizadas(metodo, rota === 'detalhe' ? uuidInexistente : '', body, autenticado))
})
When('cadastro uma empresa nao terceirizada sem CNPJ', function () {
	return guardar(this, cy.executar_empresas_nao_terceirizadas('POST', '', {}))
})
When('cadastro uma empresa nao terceirizada com CNPJ curto', function () {
	return guardar(this, cy.executar_empresas_nao_terceirizadas('POST', '', { ...dadosEmpresa(), cnpj: '123' }))
})
When('cadastro uma empresa nao terceirizada com CNPJ longo', function () {
	return guardar(this, cy.executar_empresas_nao_terceirizadas('POST', '', { ...dadosEmpresa(), cnpj: '1'.repeat(15) }))
})
When('atualizo a empresa nao terceirizada usando {string} com nome de 161 caracteres', function (metodo) {
	const body = { ...this.dadosEmpresa, nome_fantasia: 'A'.repeat(161) }
	return guardar(this, cy.executar_empresas_nao_terceirizadas(metodo, this.uuidEmpresa, body))
})
Then('a operacao de empresas nao terceirizadas retorna {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('a empresa nao terceirizada corresponde aos dados enviados', function () {
	const { cnpj, nome_fantasia, razao_social, tipo_empresa, tipo_servico, tipo_alimento } = this.dadosEmpresa
	expect(this.response.body).to.include({ uuid: this.uuidEmpresa, cnpj, nome_fantasia, razao_social, tipo_empresa, tipo_servico, tipo_alimento })
	expect(this.response.body.contatos).to.deep.eq([])
	expect(this.response.body.contratos).to.deep.eq([])
	expect(this.response.body.criado_em).to.be.a('string').and.not.be.empty
})
Then('empresas nao terceirizadas informa erro no campo {string}', function (campo) {
	expect(this.response.body[campo]).to.be.an('array').and.not.be.empty
})
