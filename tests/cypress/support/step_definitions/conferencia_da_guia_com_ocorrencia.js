import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
const inexistente = '00000000-0000-0000-0000-000000000000'
function enumNormalizado(valor) {
	return String(valor).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase()
}
function dataApi(data) {
	const partes = String(data).match(/^(\d{2})\/(\d{2})\/(\d{4})$/)
	return partes ? `${partes[3]}-${partes[2]}-${partes[1]}` : data
}
function dadosPut(conferencia) {
	return {
		conferencia_dos_alimentos: conferencia.conferencia_dos_alimentos.map((alimento) => ({
			conferencia: conferencia.uuid,
			tipo_embalagem: enumNormalizado(alimento.tipo_embalagem),
			nome_alimento: alimento.nome_alimento,
			qtd_recebido: alimento.qtd_recebido,
			status_alimento: enumNormalizado(alimento.status_alimento),
			ocorrencia: alimento.ocorrencia, observacao: alimento.observacao,
			tem_ocorrencia: alimento.tem_ocorrencia,
		})),
		guia: conferencia.guia.uuid, nome_motorista: conferencia.nome_motorista,
		placa_veiculo: conferencia.placa_veiculo,
		data_recebimento: dataApi(conferencia.data_recebimento),
		hora_recebimento: conferencia.hora_recebimento,
		eh_reposicao: conferencia.eh_reposicao,
	}
}
Given('que estou autenticado como abastecimento para conferencia com ocorrencia', () => {
	cy.autenticar_login(Cypress.env('usuario_abastecimento'), Cypress.env('senha'))
})
When('consulto a lista de conferencias com ocorrencia', function () {
	cy.consultar_conferencia_da_guia_com_ocorrencia().then((response) => {
		this.response = response
	})
})
When('consulto uma conferencia com ocorrencia existente por UUID', function () {
	cy.consultar_conferencia_da_guia_com_ocorrencia('limit=1&offset=0').then((lista) => {
		this.uuid = lista.body.results[0].uuid
		cy.consultar_conferencia_da_guia_com_ocorrencia_por_uuid(this.uuid)
			.then((response) => { this.response = response })
	})
})
When('consulto uma conferencia com ocorrencia por UUID inexistente', function () {
	cy.consultar_conferencia_da_guia_com_ocorrencia_por_uuid(inexistente)
		.then((response) => { this.response = response })
})
function atualizarPut(contexto, predicado) {
	cy.consultar_conferencia_da_guia_com_ocorrencia('limit=100&offset=0').then((lista) => {
		const conferencia = lista.body.results.find(predicado)
		expect(conferencia).to.exist
		contexto.uuid = conferencia.uuid
		cy.atualizar_conferencia_da_guia_com_ocorrencia(conferencia.uuid, dadosPut(conferencia))
			.then((response) => { contexto.response = response })
	})
}
When('atualizo por PUT uma conferencia com ocorrencia ativa', function () {
	atualizarPut(this, (item) => item.guia.situacao === 'ATIVA' &&
		item.guia.status === 'Recebida' && item.eh_reposicao === false)
})
When('atualizo por PUT uma conferencia vinculada a guia arquivada', function () {
	atualizarPut(this, (item) => item.guia.situacao === 'ARQUIVADA')
})
When('atualizo por PATCH uma conferencia com ocorrencia ativa', function () {
	cy.consultar_conferencia_da_guia_com_ocorrencia('limit=100&offset=0').then((lista) => {
		const conferencia = lista.body.results.find((item) =>
			item.guia.situacao === 'ATIVA' && item.guia.status === 'Recebida')
		expect(conferencia).to.exist
		this.uuid = conferencia.uuid
		cy.atualizar_conferencia_da_guia_com_ocorrencia_patch(
			conferencia.uuid, { nome_motorista: conferencia.nome_motorista },
		).then((response) => { this.response = response })
	})
})
When('atualizo por PATCH uma conferencia com ocorrencia inexistente', function () {
	cy.atualizar_conferencia_da_guia_com_ocorrencia_patch(
		inexistente, { nome_motorista: 'Motorista inexistente' },
	).then((response) => { this.response = response })
})
When('excluo uma conferencia com ocorrencia inexistente', function () {
	cy.excluir_conferencia_da_guia_com_ocorrencia(inexistente)
		.then((response) => { this.response = response })
})
When('cadastro uma conferencia da guia com ocorrencia valida', function () {
	cy.consultar_conferencia_da_guia_com_ocorrencia('limit=10&offset=0').then((lista) => {
		const conferencia = lista.body.results.find((item) =>
			item.conferencia_dos_alimentos.some((alimento) => alimento.tem_ocorrencia))
		expect(conferencia).to.exist
		const alimento = conferencia.conferencia_dos_alimentos.find((item) => item.tem_ocorrencia)
		this.dados = {
			conferencia_dos_alimentos: [{
				conferencia: conferencia.uuid,
				tipo_embalagem: enumNormalizado(alimento.tipo_embalagem),
				nome_alimento: alimento.nome_alimento, qtd_recebido: alimento.qtd_recebido,
				status_alimento: enumNormalizado(alimento.status_alimento),
				ocorrencia: alimento.ocorrencia,
				observacao: 'Cadastro criado pelo teste automatizado', tem_ocorrencia: true,
			}],
			guia: conferencia.guia.uuid, nome_motorista: `Motorista teste ${Date.now()}`,
			placa_veiculo: 'TES1A23', data_recebimento: new Date().toISOString().slice(0, 10),
			hora_recebimento: new Date().toTimeString().slice(0, 8), eh_reposicao: false,
		}
		cy.cadastrar_conferencia_da_guia_com_ocorrencia(this.dados).then((response) => {
			this.response = response
		})
	})
})
When('cadastro uma conferencia com ocorrencia invalida', function () {
	cy.cadastrar_conferencia_da_guia_com_ocorrencia({
		conferencia_dos_alimentos: [], guia: 'uuid-invalido', nome_motorista: '',
		placa_veiculo: '', data_recebimento: '', hora_recebimento: '', eh_reposicao: false,
	}).then((response) => { this.response = response })
})
Then('a lista de conferencias com ocorrencia retorna dados validos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.include.all.keys('count', 'next', 'previous', 'results')
	expect(this.response.body.count).to.be.a('number').and.greaterThan(0)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((item) => {
		expect(item.criado_por).to.include.all.keys('uuid', 'cpf', 'nome', 'email')
		expect(item.conferencia_dos_alimentos).to.be.an('array')
	})
})
Then('a conferencia com ocorrencia retorna os dados esperados', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
	expect(this.response.body).to.include.all.keys(
		'criado_por', 'conferencia_dos_alimentos', 'guia', 'data_recebimento',
		'hora_recebimento', 'nome_motorista', 'placa_veiculo', 'eh_reposicao',
	)
})
Then('a conferencia com ocorrencia retorna status 404', function () {
	expect(this.response.status).to.eq(404)
})
Then('a atualizacao da conferencia retorna status 200 e o UUID esperado', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(200)
	expect(this.response.body.uuid).to.eq(this.uuid)
})
Then('a atualizacao da conferencia arquivada retorna status 400', function () {
	expect(this.response.status).to.eq(400)
	expect(JSON.stringify(this.response.body)).to.contain('guia arquivada')
})
Then('o cadastro da conferencia com ocorrencia retorna status 201 e dados validos', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(201)
	expect(this.response.body).to.include({
		nome_motorista: this.dados.nome_motorista,
		placa_veiculo: this.dados.placa_veiculo, eh_reposicao: false,
	})
	expect(this.response.body.uuid).to.be.a('string').and.not.be.empty
})
Then('o cadastro da conferencia com ocorrencia retorna status 400', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.be.an('object').and.not.be.empty
})
