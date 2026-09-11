/// <reference types='cypress' />

Cypress.Commands.add('validar_alteracoes_cardapio', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}`,
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_alteracoes_cardapio_relatorio', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}/relatorio/`,
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_alteracoes_cardapio_minhas_solicitacoes', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/alteracoes-cardapio/minhas-solicitacoes/?limit=1&offset=0',
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_alteracoes_cardapio', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/alteracoes-cardapio/',
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: corpo_alteracoes_cardapio(dados_teste),
		failOnStatusCode: false,
	})
})

function corpo_alteracoes_cardapio(dados_teste) {
	return {
		motivo: dados_teste.motivo,
		escola: dados_teste.escola,
		substituicoes: [
			{
				periodo_escolar: dados_teste.periodo_escolar,
				tipos_alimentacao_de: [dados_teste.tipos_alimentacao_de],
				alteracao_cardapio: dados_teste.alteracao_cardapio,
				tipos_alimentacao_para: [dados_teste.tipos_alimentacao_para],
				qtd_alunos: dados_teste.qtd_alunos,
			},
		],
		datas_intervalo: [
			{
				alteracao_cardapio: dados_teste.alteracao_cardapio,
				data: dados_teste.data,
				cancelado: dados_teste.cancelado,
				cancelado_justificativa: dados_teste.cancelado_justificativa,
				cancelado_em: dados_teste.cancelado_em,
				cancelado_por: dados_teste.cancelado_por,
			},
		],
		data_inicial: dados_teste.data,
		data_final: dados_teste.data,
		observacao: dados_teste.observacao,
		foi_solicitado_fora_do_prazo: dados_teste.foi_solicitado_fora_do_prazo,
		terceirizada_conferiu_gestao: dados_teste.terceirizada_conferiu_gestao,
		eh_alteracao_com_lanche_repetida:
			dados_teste.eh_alteracao_com_lanche_repetida,
		criado_por: dados_teste.criado_por,
	}
}

Cypress.Commands.add('excluir_alteracoes_cardapio', (id) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}/`,
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

function solicitar_alteracoes_cardapio(method, url, body) {
	return cy.request({
		method,
		url,
		timeout: 120000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		...(body === undefined ? {} : { body }),
		failOnStatusCode: false,
	})
}

Cypress.Commands.add('atualizar_alteracoes_cardapio', (id, dados) =>
	solicitar_alteracoes_cardapio(
		'PUT',
		Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}/`,
		corpo_alteracoes_cardapio(dados),
	),
)

Cypress.Commands.add('atualizar_parcial_alteracoes_cardapio', (id, dados) =>
	solicitar_alteracoes_cardapio(
		'PATCH',
		Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}/`,
		corpo_alteracoes_cardapio(dados),
	),
)

const acoesAlteracaoCardapio = [
	'codae-autoriza-pedido',
	'codae-cancela-pedido',
	'codae-questiona-pedido',
	'diretoria-regional-nao-valida-pedido',
	'diretoria-regional-valida-pedido',
	'escola-cancela-pedido-48h-antes',
	'inicio-pedido',
	'marcar-conferida',
	'terceirizada-responde-questionamento',
	'terceirizada-toma-ciencia',
]

acoesAlteracaoCardapio.forEach((acao) => {
	Cypress.Commands.add(
		`executar_${acao.replaceAll('-', '_')}_alteracao_cardapio`,
		(id, dados) =>
			solicitar_alteracoes_cardapio(
				'PATCH',
				Cypress.config('baseUrl') +
					`api/alteracoes-cardapio/${id}/${acao}/`,
				dados,
			),
	)
})

Cypress.Commands.add(
	'consultar_pedidos_codae_alteracoes_cardapio',
	(filtro_aplicado, parametros = '') =>
		solicitar_alteracoes_cardapio(
			'GET',
			Cypress.config('baseUrl') +
				`api/alteracoes-cardapio/pedidos-codae/${filtro_aplicado}/${parametros}`,
		),
)

Cypress.Commands.add(
	'consultar_pedidos_diretoria_regional_alteracoes_cardapio',
	(filtro_aplicado, parametros = '') =>
		solicitar_alteracoes_cardapio(
			'GET',
			Cypress.config('baseUrl') +
				`api/alteracoes-cardapio/pedidos-diretoria-regional/${filtro_aplicado}/${parametros}`,
		),
)
