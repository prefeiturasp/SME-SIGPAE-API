/// <reference types='cypress' />

Cypress.Commands.add('validar_alteracoes_cardapio', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}`,
		timeout: 60000,
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
			'api/alteracoes-cardapio/minhas-solicitacoes/',
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
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
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
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('excluir_alteracoes_cardapio', (id) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/alteracoes-cardapio/${id}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
