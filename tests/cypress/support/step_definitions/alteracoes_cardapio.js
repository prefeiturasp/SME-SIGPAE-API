import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'
import dayjs from 'dayjs'
import { validar_dia_semana } from '../utils/data_utils'

const esperaApi = Cypress.env('wait_api_alteracoes_cardapio') || 3000
const uuidAlteracaoExistente = '3f42cdc6-f524-4364-af62-13a831abae5d'

function aguardarApi() {
	cy.wait(esperaApi)
}

function dataLetiva(dataBase) {
	const feriadosFixos = [
		'01-01',
		'04-21',
		'05-01',
		'09-07',
		'10-12',
		'11-02',
		'11-15',
		'12-25',
	]
	let data = validar_dia_semana(dataBase, 6)

	while (feriadosFixos.includes(data.format('MM-DD'))) {
		data = validar_dia_semana(data, 1)
	}

	return data
}

function dataNaoLetivaFutura() {
	let data = dayjs().add(1, 'day')

	while ([1, 7, 12].includes(data.month() + 1) || ![0, 6].includes(data.day())) {
		data = data.add(1, 'day')
	}

	return data.format('YYYY-MM-DD')
}

function dadosValidos(data = validar_dia_semana(dayjs(), 5).format('YYYY-MM-DD')) {
	return {
		motivo: '1ddec320-cd24-4cf4-9666-3e7b3a2b903c',
		escola: '671f5641-b1d4-4736-be38-7115590b7018',
		periodo_escolar: '5067e137-e5f3-4876-a63f-7f58cce93f33',
		tipos_alimentacao_de: '65f11f11-630b-4629-bb17-07c875c548f1',
		alteracao_cardapio: '6595ebe5-dc21-48b0-bb05-6347341f9797',
		tipos_alimentacao_para: '5d1304c8-77a8-4c96-badb-dd2e8c1b76d5',
		qtd_alunos: 10,
		cancelado: true,
		cancelado_justificativa: 'teste automatizado api',
		cancelado_em: null,
		cancelado_por: null,
		observacao: '<p>teste automatizado api</p>',
		foi_solicitado_fora_do_prazo: true,
		terceirizada_conferiu_gestao: true,
		eh_alteracao_com_lanche_repetida: true,
		criado_por: null,
		data,
	}
}

function dadosDoCaso(caso) {
	const dados = dadosValidos()
	const alteracoes = {
		motivo_branco: { motivo: '' },
		motivo_uuid_invalido: { motivo: '671f5641-ds54-4736-dsa4-7115590b7018' },
		escola_branco: { escola: '' },
		escola_uuid_invalido: { escola: '1ddec320-dss2-45ds-9666-3e7b3a2b903c' },
		periodo_escolar_branco: { periodo_escolar: '' },
		periodo_escolar_uuid_invalido: {
			periodo_escolar: '671f5641-54ds-56s4-5d6s-7115590b7018',
		},
		tipo_alimentacao_de_branco: { tipos_alimentacao_de: '' },
		tipo_alimentacao_de_uuid_invalido: {
			tipos_alimentacao_de: '5067e137-ds54-ds45-ds54-7f58cce93f33',
		},
		alteracao_cardapio_branco: { alteracao_cardapio: '' },
		alteracao_cardapio_uuid_invalido: {
			alteracao_cardapio: '65f11f11-ds51-ds54-ds4-07c875c548f1',
		},
		tipo_alimentacao_para_branco: { tipos_alimentacao_para: '' },
		tipo_alimentacao_para_uuid_invalido: {
			tipos_alimentacao_para: '6595ebe5-fd54-ds56-ds56-6347341f9797',
		},
		quantidade_alunos_negativa: { qtd_alunos: -1 },
		quantidade_alunos_branco: { qtd_alunos: '' },
		cancelado_branco: { cancelado: '' },
		cancelado_em_texto: { cancelado_em: 'a' },
		cancelado_em_formato_invalido: {
			cancelado_em: dayjs().format('DD-MM-YYYY'),
		},
		cancelado_em_branco: { cancelado_em: '' },
		cancelado_por_texto: { cancelado_por: 'a' },
		cancelado_por_formato_invalido: {
			cancelado_por: validar_dia_semana(dayjs(), 5).format('DD-MM-YYYY'),
		},
		fora_prazo_branco: { foi_solicitado_fora_do_prazo: '' },
		terceirizada_conferiu_branco: { terceirizada_conferiu_gestao: '' },
		data_branco: { data: '' },
		data_passado: { data: dayjs().subtract(1, 'day').format('YYYY-MM-DD') },
		data_nao_letivo: { data: dataNaoLetivaFutura() },
		data_formato_invalido: { data: dayjs().format('DD-MM-YYYU') },
	}

	expect(alteracoes, `Caso nao mapeado: ${caso}`).to.have.property(caso)
	return { ...dados, ...alteracoes[caso] }
}

function corpoDaResposta(response) {
	return response.allRequestResponses?.[0]?.['Response Body'] || response.body
}

function valorNoCaminho(objeto, caminho) {
	return caminho.reduce((valor, chave) => valor?.[chave], objeto)
}

function caminhosDeErro(caso) {
	const substituicao = ['substituicoes', 0]
	const intervalo = ['datas_intervalo', 0]
	const caminhos = {
		motivo_branco: [['motivo', 0]],
		motivo_uuid_invalido: [['motivo', 0]],
		escola_branco: [['escola', 0]],
		escola_uuid_invalido: [['escola', 0]],
		periodo_escolar_branco: [[...substituicao, 'periodo_escolar', 0]],
		periodo_escolar_uuid_invalido: [[...substituicao, 'periodo_escolar', 0]],
		tipo_alimentacao_de_branco: [[...substituicao, 'tipos_alimentacao_de', 0]],
		tipo_alimentacao_de_uuid_invalido: [
			[...substituicao, 'tipos_alimentacao_de', 0],
		],
		alteracao_cardapio_branco: [
			[...intervalo, 'alteracao_cardapio', 0],
			[...substituicao, 'alteracao_cardapio', 0],
		],
		alteracao_cardapio_uuid_invalido: [
			[...intervalo, 'alteracao_cardapio', 0],
			[...substituicao, 'alteracao_cardapio', 0],
		],
		tipo_alimentacao_para_branco: [
			[...substituicao, 'tipos_alimentacao_para', 0],
		],
		tipo_alimentacao_para_uuid_invalido: [
			[...substituicao, 'tipos_alimentacao_para', 0],
		],
		quantidade_alunos_negativa: [[...substituicao, 'qtd_alunos', 0]],
		quantidade_alunos_branco: [[...substituicao, 'qtd_alunos', 0]],
		cancelado_branco: [[...intervalo, 'cancelado', 0]],
		cancelado_em_texto: [[...intervalo, 'cancelado_em', 0]],
		cancelado_em_formato_invalido: [[...intervalo, 'cancelado_em', 0]],
		cancelado_em_branco: [[...intervalo, 'cancelado_em', 0]],
		cancelado_por_texto: [[...intervalo, 'cancelado_por', 0]],
		cancelado_por_formato_invalido: [[...intervalo, 'cancelado_por', 0]],
		fora_prazo_branco: [['foi_solicitado_fora_do_prazo', 0]],
		terceirizada_conferiu_branco: [['terceirizada_conferiu_gestao', 0]],
		data_branco: [
			['data_final', 0],
			['data_inicial', 0],
			[...intervalo, 'data', 0],
		],
		data_passado: [['non_field_errors', 0]],
		data_nao_letivo: [[0]],
		data_formato_invalido: [
			['data_final', 0],
			['data_inicial', 0],
			[...intervalo, 'data', 0],
		],
	}
	return caminhos[caso]
}

function validarListagem(results) {
	expect(results).to.exist
	results.forEach((result) => {
		expect(result.escola.codigo_eol).to.exist
		expect(result.escola.nome).to.exist
		expect(result.escola.lote.nome).to.exist
		result.escola.lote.contratos_do_lote.forEach((contrato) => {
			expect(contrato.uuid).to.exist
		})
		result.datas_intervalo.forEach((data) => {
			expect(data.alteracao_cardapio).to.exist
		})
	})
}

Given('que estou autenticado como diretor para alteracoes de cardapio', () => {
	cy.autenticar_login(Cypress.env('usuario_diretor_ue'), Cypress.env('senha'))
	aguardarApi()
})

When('consulto todas as alteracoes de cardapio como supervisao de nutricao', function () {
	cy.autenticar_login(
		Cypress.env('usuario_coordenador_supervisao_nutricao'),
		Cypress.env('senha'),
	)
	aguardarApi()
	cy.validar_alteracoes_cardapio('').then((response) => {
		this.response = response
	})
})

When('cadastro uma alteracao de cardapio com dados validos', function () {
	this.dados = dadosValidos(dataLetiva(dayjs()).format('YYYY-MM-DD'))
	cy.cadastrar_alteracoes_cardapio(this.dados).then((response) => {
		this.response = response
	})
})

When(
	'tento cadastrar uma alteracao de cardapio com {string} invalido',
	function (caso) {
		this.caso = caso
		if (caso === 'data_nao_letivo' && [1, 7, 12].includes(dayjs().month() + 1)) {
			this.ignorarCasoSazonal = true
			return
		}
		cy.cadastrar_alteracoes_cardapio(dadosDoCaso(caso)).then((response) => {
			this.response = response
		})
	},
)

When('consulto uma alteracao de cardapio como diretor', function () {
	cy.validar_alteracoes_cardapio(`${uuidAlteracaoExistente}/`).then((response) => {
		this.response = response
	})
})

When('consulto uma alteracao de cardapio por id inexistente', function () {
	cy.autenticar_login(
		Cypress.env('usuario_coordenador_supervisao_nutricao'),
		Cypress.env('senha'),
	)
	aguardarApi()
	cy.validar_alteracoes_cardapio(
		'3f42cdc6-f524-4364-af62-13a831abaecd/',
	).then((response) => {
		this.response = response
	})
})

When('consulto uma alteracao de cardapio por id sem barra final', function () {
	cy.autenticar_login(
		Cypress.env('usuario_coordenador_supervisao_nutricao'),
		Cypress.env('senha'),
	)
	aguardarApi()
	cy.validar_alteracoes_cardapio(uuidAlteracaoExistente).then((response) => {
		this.response = response
	})
})

When('consulto uma alteracao de cardapio existente', function () {
	cy.validar_alteracoes_cardapio_minhas_solicitacoes().then((lista) => {
		expect(lista.status).to.eq(200)
		expect(lista.body.results).to.be.an('array').and.not.be.empty
		this.uuid = lista.body.results[0].uuid
		cy.validar_alteracoes_cardapio(`${this.uuid}/`).then((response) => {
			this.response = response
		})
	})
})

When('cadastro e excluo uma alteracao de cardapio', function () {
	cy.autenticar_login(
		Cypress.env('usuario_coordenador_logistica'),
		Cypress.env('senha'),
	)
	aguardarApi()
	cy.cadastrar_alteracoes_cardapio(dadosValidos()).then((cadastro) => {
		this.cadastro = cadastro
		if (cadastro.status === 403) return
		const id = cadastro.body.substituicoes[0].alteracao_cardapio
		cy.excluir_alteracoes_cardapio(id).then((response) => {
			this.response = response
		})
	})
})

When('excluo uma alteracao de cardapio com id invalido', function () {
	cy.excluir_alteracoes_cardapio('1ddec320-cd24-4cf4-9666-3e7b3ds5903c').then(
		(response) => {
			this.response = response
		},
	)
})

When('consulto o relatorio de uma alteracao de cardapio existente', function () {
	cy.validar_alteracoes_cardapio_relatorio(uuidAlteracaoExistente).then(
		(response) => {
			this.response = response
		},
	)
})

When('consulto o relatorio de uma alteracao de cardapio inexistente', function () {
	cy.validar_alteracoes_cardapio_relatorio(
		'3f42cdc6-f524-4364-af62-13a831adde5d',
	).then((response) => {
		this.response = response
	})
})

When('consulto minhas solicitacoes de alteracao de cardapio', function () {
	cy.validar_alteracoes_cardapio_minhas_solicitacoes().then((response) => {
		this.response = response
	})
})

Then('deve retornar a listagem de alteracoes de cardapio permitida ao perfil', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		expect(this.response.body.detail).to.exist
		return
	}
	validarListagem(this.response.body.results || [])
})

Then('a alteracao de cardapio deve ser cadastrada com sucesso', function () {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(201)
	expect(this.response.body.motivo).to.eq(this.dados.motivo)
	expect(this.response.body.escola).to.eq(this.dados.escola)
	expect(this.response.body.substituicoes[0].periodo_escolar).to.eq(
		this.dados.periodo_escolar,
	)
	expect(this.response.body.substituicoes[0].tipos_alimentacao_de[0]).to.eq(
		this.dados.tipos_alimentacao_de,
	)
	expect(this.response.body.substituicoes[0].tipos_alimentacao_para[0]).to.eq(
		this.dados.tipos_alimentacao_para,
	)
	expect(this.response.body.criado_em).to.contain(dayjs().format('DD/MM/YYYY'))
	expect(this.response.body.data_final).to.contain(
		dayjs(this.dados.data).format('DD/MM/YYYY'),
	)
})

Then(
	'o cadastro da alteracao deve ser rejeitado por {string} invalido',
	function (caso) {
		if (this.ignorarCasoSazonal) return
		expect(caso).to.eq(this.caso)
		expect(this.response.status).to.eq(400)
		const corpo = corpoDaResposta(this.response)
		caminhosDeErro(caso).forEach((caminho) => {
			expect(valorNoCaminho(corpo, caminho), caminho.join('.')).to.exist
		})
	},
)

Then('a consulta deve retornar o registro ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 200) {
		expect(this.response.body.uuid).to.eq(uuidAlteracaoExistente)
		return
	}
	expect(this.response.body.detail).to.exist
})

Then('a consulta da alteracao deve retornar status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.statusText).to.eq('Not Found')
})

Then('a consulta da alteracao deve redirecionar para a barra final', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.allRequestResponses[0]['Response Status']).to.eq(301)
	expect(this.response.redirects[0]).to.contain('301: https://')
	expect(this.response.redirects[0]).to.contain(
		`/alteracoes-cardapio/${uuidAlteracaoExistente}/`,
	)
})

Then('deve retornar os dados completos da alteracao ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		expect(this.response.body.detail).to.exist
		return
	}
	expect(this.response.body.uuid).to.eq(this.uuid)
	expect(this.response.body.criado_em).to.exist
	expect(this.response.body.criado_por).to.exist
	expect(this.response.body.data_final).to.exist
	expect(this.response.body.datas_intervalo).to.be.an('array').that.is.not.empty
	expect(this.response.body.foi_solicitado_fora_do_prazo).to.eq(false)
	expect(this.response.body.id_externo).to.be.a('string').and.not.be.empty
	expect(this.response.body.logs).to.be.an('array').that.is.not.empty
	expect(this.response.body.motivo.ativo).to.eq(true)
	expect(this.response.body.motivo.nome).to.be.a('string').and.not.be.empty
	expect(this.response.body.motivo.uuid).to.exist
	expect(this.response.body.rastro_terceirizada.contatos).to.be.an('array').that.is
		.not.empty
	expect(this.response.body.rastro_terceirizada.contratos).to.be.an('array').that
		.is.not.empty
	expect(this.response.body.substituicoes).to.be.an('array').that.is.not.empty
})

Then('a operacao de exclusao deve ser aceita pelo perfil', function () {
	expect([201, 403]).to.include(this.cadastro.status)
	if (this.cadastro.status === 403) {
		expect(this.cadastro.body.detail).to.exist
		return
	}
	expect([204, 403]).to.include(
		this.response.allRequestResponses[0]['Response Status'],
	)
})

Then('a exclusao invalida deve retornar status 403 ou 404', function () {
	expect([403, 404]).to.include(
		this.response.allRequestResponses[0]['Response Status'],
	)
})

Then('deve retornar o relatorio PDF da alteracao', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.allRequestResponses).to.be.an('array').that.is.not.empty
	expect(this.response.allRequestResponses[0]['Response Body']).to.contain('%PDF')
})

Then('a consulta do relatorio deve retornar status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.allRequestResponses).to.be.an('array').that.is.not.empty
	expect(this.response.statusText).to.eq('Not Found')
})

Then('deve retornar a listagem das minhas solicitacoes', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.exist
	validarListagem(this.response.body.results)
})
