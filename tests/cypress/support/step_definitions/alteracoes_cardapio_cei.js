import { Given, When, Then, After } from 'cypress-cucumber-preprocessor/steps'
import dayjs from 'dayjs'

const inexistente = '00000000-0000-0000-0000-000000000000'
const perfis = { escola: 'usuario_diretor_ue', codae: 'usuario_codae', dre: 'usuario_dre' }
let criados = []
let modelo
let escolaAutenticada

function autenticar(perfil) {
	const usuario = perfil === 'escola'
		? Cypress.env('usuario_escola_cei_admin') || Cypress.env(perfis[perfil])
		: Cypress.env(perfis[perfil])
	expect(usuario, `Credencial do perfil ${perfil}`).to.be.a('string').and.not.be.empty
	return cy.autenticar_login(usuario, Cypress.env('senha'))
}

function requisitar(contexto, operacao, opcoes = {}) {
	return cy.requisitar_alteracoes_cardapio_cei(operacao, opcoes).then((response) => {
		contexto.response = response
		if (response.status === 201 && response.body.uuid) criados.push(response.body.uuid)
		return response
	})
}

function buscarModelo(offset = 0) {
	if (modelo) return cy.wrap(modelo, { log: false })
	return cy.requisitar_alteracoes_cardapio_cei('listar', { query: { limit: 100, offset } }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array')
		modelo = response.body.results.find((item) =>
			item.motivo?.nome === 'LPR - Lanche por Refeição' && item.escola?.uuid &&
			item.substituicoes?.some((sub) => sub.faixas_etarias?.length && sub.tipo_alimentacao_para?.uuid),
		)
		if (modelo) return modelo
		if (response.body.next && response.body.results.length) return buscarModelo(offset + response.body.results.length)
		throw new Error('Pre-condicao: nenhum modelo CEI LPR com substituicoes e faixas etarias foi encontrado em QA.')
	})
}

function montarDados(item) {
	let data = dayjs().add(14, 'day')
	while ([0, 6].includes(data.day())) data = data.add(1, 'day')
	expect(data.year(), 'Data CEI deve permanecer no ano corrente').to.eq(dayjs().year())
	const sub = item.substituicoes.find((s) => s.faixas_etarias?.length && s.tipo_alimentacao_para?.uuid)
	return {
		escola: item.escola.uuid,
		motivo: item.motivo.uuid,
		data: data.format('YYYY-MM-DD'),
		observacao: `Automacao CEI ${Date.now()}`,
		substituicoes: [{
			periodo_escolar: sub.periodo_escolar.uuid,
			tipos_alimentacao_de: sub.tipos_alimentacao_de.map((tipo) => tipo.uuid),
			tipo_alimentacao_para: sub.tipo_alimentacao_para.uuid,
			faixas_etarias: [{ faixa_etaria: sub.faixas_etarias[0].faixa_etaria.uuid, quantidade: 1 }],
		}],
	}
}

Given('que estou autenticado como escola para cardapio CEI', () => {
	criados = []
	return autenticar('escola')
})

After({ tags: '@cardapio_cei' }, () => {
	if (!criados.length) return
	autenticar('escola')
	for (const uuid of criados) {
		cy.requisitar_alteracoes_cardapio_cei('excluir', { uuid }).then((response) => {
			expect(response.status, `Limpeza do rascunho CEI ${uuid}`).to.eq(204)
		})
	}
})

Given('que criei um rascunho de cardapio CEI', function () {
	const consultarEscola = escolaAutenticada
		? cy.wrap(escolaAutenticada, { log: false })
		: cy.request({
			url: `${Cypress.config('baseUrl')}api/usuarios/meus-dados/`,
			headers: { Authorization: `JWT ${globalThis.token}` },
		}).then((response) => {
			escolaAutenticada = response.body.vinculo_atual.instituicao
			return escolaAutenticada
		})
	return consultarEscola.then((escola) => {
		if (!escola.eh_cei) {
			Cypress.log({ name: 'Pre-condicao CEI', message: 'Configure USUARIO_ESCOLA_CEI_ADMIN no .env com um usuario vinculado a CEI para executar os cenarios com rascunho.' })
			this.skip()
		}
		return buscarModelo()
	}).then((item) => {
		this.dados = montarDados(item)
		this.dados.escola = escolaAutenticada.uuid
		return requisitar(this, 'cadastrar', { dados: this.dados })
	}).then((response) => {
		expect(response.status, JSON.stringify(response.body)).to.eq(201)
		expect(response.body.uuid).to.be.a('string').and.not.be.empty
		this.uuid = response.body.uuid
	})
})

When('consulto {string} de cardapio CEI como {string}', function (operacao, perfil) {
	autenticar(perfil)
	return requisitar(this, operacao, { query: { limit: 2, offset: 0 } })
})
Then('a listagem de cardapio CEI retorna status 200 e resultados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array')
	this.response.body.results.forEach((item) => {
		expect(item.uuid).to.be.a('string').and.not.be.empty
		expect(item.substituicoes).to.be.an('array')
	})
})
When('consulto a segunda pagina de cardapio CEI com limite 2', function () {
	return requisitar(this, 'listar', { query: { limit: 2, offset: 2 } })
})
Then('a pagina de cardapio CEI respeita o limite informado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number')
	expect(this.response.body.results).to.be.an('array').and.have.length.at.most(2)
})
Then('o rascunho CEI foi criado com os dados enviados', function () {
	expect(this.response.status).to.eq(201)
	expect(this.response.body).to.include({ escola: this.dados.escola, motivo: this.dados.motivo, observacao: this.dados.observacao })
	expect(this.response.body.substituicoes).to.have.length(1)
	expect(this.response.body.substituicoes[0].faixas_etarias[0].quantidade).to.eq(1)
})
When('consulto o detalhe do rascunho CEI como CODAE', function () {
	autenticar('codae')
	return requisitar(this, 'detalhar', { uuid: this.uuid })
})
Then('o detalhe CEI corresponde ao rascunho criado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include({ uuid: this.uuid, status: 'RASCUNHO', observacao: this.dados.observacao })
	expect(this.response.body.escola.uuid).to.eq(this.dados.escola)
})
When('altero a observacao do rascunho CEI usando {string}', function (operacao) {
	autenticar('codae')
	this.dados.observacao = `Atualizacao CEI ${operacao} ${Date.now()}`
	// O serializer atual exige substituicoes tambem na atualizacao parcial.
	return requisitar(this, operacao, { uuid: this.uuid, dados: this.dados })
})
Then('a alteracao CEI e persistida', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body.observacao).to.eq(this.dados.observacao)
	return cy.requisitar_alteracoes_cardapio_cei('detalhar', { uuid: this.uuid }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.observacao).to.eq(this.dados.observacao)
	})
})
When('excluo o rascunho de cardapio CEI', function () {
	return requisitar(this, 'excluir', { uuid: this.uuid }).then((response) => {
		if (response.status === 204) criados = criados.filter((uuid) => uuid !== this.uuid)
	})
})
Then('a exclusao CEI retorna 204 e o registro deixa de existir', function () {
	expect(this.response.status).to.eq(204)
	return cy.requisitar_alteracoes_cardapio_cei('detalhar', { uuid: this.uuid }).then((response) => expect(response.status).to.eq(404))
})
When('solicito o relatorio de uma solicitacao CEI existente', function () {
	return buscarModelo().then((item) => requisitar(this, 'relatorio', { uuid: item.uuid }))
})
Then('o relatorio CEI retorna um PDF', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.headers['content-type']).to.contain('application/pdf')
	expect(this.response.body.slice(0, 5)).to.eq('%PDF-')
})
When('cadastro cardapio CEI com {string}', function (caso) {
	return buscarModelo().then((item) => {
		const dados = montarDados(item)
		const campo = caso.split(' ')[0]
		if (caso.endsWith('ausente') || caso.endsWith('ausentes')) delete dados[campo]
		else if (caso === 'data passada') dados.data = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
		else dados[campo] = 'invalido'
		return requisitar(this, 'cadastrar', { dados })
	})
})
Then('o cadastro CEI retorna 400 no campo {string}', function (campo) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(400)
	expect(this.response.body).to.have.property(campo).that.is.not.empty
})
When('atualizo cardapio CEI com data invalida usando {string}', function (operacao) {
	autenticar('codae')
	return requisitar(this, operacao, { uuid: this.uuid, dados: { ...this.dados, data: 'invalida' } })
})
When('acesso {string} de cardapio CEI com UUID inexistente como {string}', function (operacao, perfil) {
	autenticar(perfil)
	return requisitar(this, operacao, { uuid: inexistente })
})
Then('a operacao de cardapio CEI retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if ([401, 403].includes(status)) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
When('tento {string} no rascunho CEI como {string}', function (operacao, perfil) {
	autenticar(perfil)
	return requisitar(this, operacao, { uuid: this.uuid, dados: { justificativa: 'Teste de transicao invalida', observacao_questionamento_codae: 'Teste de transicao invalida' } })
})
Then('a transicao CEI retorna 400 e preserva o rascunho', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(400)
	expect(this.response.body.detail).to.contain('transição')
	autenticar('codae')
	return cy.requisitar_alteracoes_cardapio_cei('detalhar', { uuid: this.uuid }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.status).to.eq('RASCUNHO')
	})
})
When('acesso {string} de cardapio CEI como escola sem permissao', function (operacao) {
	return requisitar(this, operacao, { uuid: inexistente })
})
When('acesso {string} de cardapio CEI sem autenticacao', function (operacao) {
	return requisitar(this, operacao, { uuid: inexistente, autenticado: false })
})
