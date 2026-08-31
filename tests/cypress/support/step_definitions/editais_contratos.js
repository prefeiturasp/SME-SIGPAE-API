import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const campos = ['uuid', 'numero', 'tipo_contratacao', 'processo', 'objeto', 'eh_imr']
function dados(sufixo = 'Teste', datas = ['25/06/2025', '25/06/2026']) {
	return {
		numero: `AUTOMACAO${Date.now()}`,
		lotes: '1f06b334-cbd1-40c5-85c4-6a3d1926805b',
		terceirizada: 'cfc9a71f-fd63-461e-93e8-7020169d3563',
		diretorias_regionais: '20549e43-ff46-4f1e-936d-89086732c76d',
		data_inicial: datas[0], data_final: datas[1], processo: '123456',
		data_proposta: '21/08/2025', encerrado: false,
		data_hora_encerramento: null, ata: '', numero_pregao: '',
		numero_chamada_publica: '', edital: 31, modalidade: null,
		tipo_contratacao: 'Teste', objeto: `Objeto ${sufixo}`, eh_imr: sufixo !== 'Teste',
	}
}
Given('que estou autenticado como DRE para gerenciar editais e contratos', () => {
	cy.autenticar_login(Cypress.config('usuario_dre'), Cypress.config('senha'))
})
When('consulto a lista de editais e contratos', function () {
	cy.consultar_editais_contratos().then((response) => { this.response = response })
})
When('consulto edital e contrato pelo UUID {string}', function (uuid) {
	const comando = uuid.startsWith('e40') ? 'consultar_editais_contratos_por_uuid' : 'consultar_editais_por_uuid'
	cy[comando](uuid).then((response) => { this.response = response })
})
When('cadastro um edital e contrato valido', function () {
	cy.cadastrar_editais_contratos(dados()).then((criado) => {
		this.response = criado
		if (criado.status === 201) {
			cy.deletar_editais_contratos(criado.body.uuid).then((exclusao) => {
				this.exclusao = exclusao
			})
		}
	})
})
When('cadastro e excluo um edital e contrato valido', function () {
	cy.cadastrar_editais_contratos(dados()).then((criado) => {
		expect(criado.status).to.eq(201)
		cy.deletar_editais_contratos(criado.body.uuid).then((response) => {
			this.response = response
		})
	})
})
When('excluo um edital e contrato por UUID inexistente', function () {
	cy.deletar_editais_contratos('b2dbaff4-dbd3-45b8-b67c-57ff4b5ad35b/')
		.then((response) => { this.response = response })
})
function atualizar(contexto, datas) {
	const original = dados('Teste', datas)
	cy.cadastrar_editais_contratos(original).then((criado) => {
		expect(criado.status).to.eq(201)
		const alterado = { ...dados('Alterado', datas), numero: original.numero }
		cy.atualizar_editais_contratos(
			criado.body.uuid, criado.body.contratos[0].uuid, alterado,
		).then((response) => {
			contexto.response = response
			contexto.uuid = criado.body.uuid
			contexto.numero = alterado.numero
			cy.deletar_editais_contratos(criado.body.uuid).then((exclusao) => {
				contexto.exclusao = exclusao
			})
		})
	})
}
When('atualizo um edital e contrato valido por PUT', function () {
	atualizar(this, ['25/06/2025', '25/06/2026'])
})
When('atualizo um edital e contrato pelo fluxo PATCH existente', function () {
	atualizar(this, ['25/10/2025', '25/10/2026'])
})
Then('a lista de editais e contratos retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	expect(this.response.body.results[0]).to.include.all.keys(...campos)
})
Then('a consulta de edital e contrato retorna status {int}', function (status) {
	expect(this.response.status).to.eq(status)
})
Then('quando encontrado apresenta os campos esperados', function () {
	if (this.response.status === 200) expect(this.response.body).to.include.all.keys(...campos)
})
Then('o edital e contrato e criado e removido com sucesso', function () {
	expect(this.response.status).to.eq(201)
	expect(this.exclusao.status).to.eq(204)
})
Then('a exclusao do edital e contrato retorna status 204', function () {
	expect(this.response.status).to.eq(204)
})
Then('a exclusao do edital e contrato retorna status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.body).to.exist
})
Then('o edital e contrato e atualizado e removido com sucesso', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
	expect(this.response.body.numero).to.eq(this.numero)
	expect(this.response.body.eh_imr).to.eq(true)
	expect(this.exclusao.status).to.eq(204)
})
