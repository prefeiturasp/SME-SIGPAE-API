/// <reference types='cypress' />

Cypress.Commands.add('validar_cronogramas', (parametros) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + `api/cronogramas/?page_size=2/&${parametros}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_cronogramas_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/cronogramas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_dados_cronograma_ficha_recebimento', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/cronogramas/${uuid}/dados-cronograma-ficha-recebimento/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_detalhar_com_log', (uuid) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + `api/cronogramas/${uuid}/detalhar-com-log/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_dashboard', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/cronogramas/dashboard/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_dashboard_com_filtro', (filtro) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			`api/cronogramas/dashboard-com-filtro/${filtro}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_lista_cronogramas_cadastro', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/cronogramas/lista-cronogramas-cadastro/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_lista_cronogramas_ficha_recebimento', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/cronogramas/lista-cronogramas-ficha-recebimento/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_listagem_relatorio', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/cronogramas/listagem-relatorio/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_opcoes_etapas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/cronogramas/opcoes-etapas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_rascunhos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/cronogramas/rascunhos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_cronogramas', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/cronogramas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			armazem: dados_teste.armazem,
			empresa: dados_teste.empresa,
			contrato: dados_teste.contrato,
			unidade_medida: dados_teste.unidade_medida,
			qtd_total_programada: dados_teste.qtd_total_programada,
			etapas: [
				{
					numero_empenho: dados_teste.etapas.numero_empenho,
					etapa: dados_teste.etapas.etapa,
					parte: dados_teste.etapas.parte,
					data_programada: dados_teste.etapas.data_programada,
					quantidade: dados_teste.etapas.quantidade,
					total_embalagens: dados_teste.etapas.total_embalagens,
					qtd_total_empenho: dados_teste.etapas.qtd_total_empenho,
					uuid: dados_teste.etapas.uuid,
				},
			],
			programacoes_de_recebimento: [
				{
					data_programada:
						dados_teste.programacoes_de_recebimento.data_programada,
					tipo_carga: dados_teste.programacoes_de_recebimento.tipo_carga,
					uuid: dados_teste.programacoes_de_recebimento.uuid,
				},
			],
			ficha_tecnica: dados_teste.ficha_tecnica,
			tipo_embalagem_secundaria: dados_teste.tipo_embalagem_secundaria,
			custo_unitario_produto: dados_teste.custo_unitario_produto,
			uuid: dados_teste.uuid,
			observacoes: dados_teste.observacoes,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_cronograma', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/cronogramas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

export const rotasComplementaresCronogramas = {
	atualizar: ['PUT', '{uuid}/'], parcial: ['PATCH', '{uuid}/'],
	assinar_abastecimento: ['PATCH', '{uuid}/abastecimento-assina/'],
	assinar_codae: ['PATCH', '{uuid}/codae-assina/'],
	assinar_fornecedor: ['PATCH', '{uuid}/fornecedor-assina-cronograma/'],
	dados_pos_recebimento: ['GET', '{uuid}/dados-cronograma-pos-recebimento/'],
	pdf_cronograma: ['GET', '{uuid}/gerar-pdf-cronograma/'],
	relatorio_pdf: ['GET', 'gerar-relatorio-pdf-async/'],
	relatorio_xlsx: ['GET', 'gerar-relatorio-xlsx-async/'],
	lista_pos_recebimento: ['GET', 'lista-cronogramas-pos-recebimento/'],
}
Cypress.Commands.add('requisitar_complemento_cronogramas', (operacao, opcoes = {}) => {
	const rota = rotasComplementaresCronogramas[operacao]
	if (!rota) throw new Error(`Operacao de cronograma desconhecida: ${operacao}`)
	if (rota[1].includes('{uuid}') && !opcoes.uuid) throw new Error('Informe UUID do cronograma')
	return cy.request({
		method: rota[0],
		url: `${Cypress.config('baseUrl')}api/cronogramas/${rota[1].replace('{uuid}', opcoes.uuid)}`,
		qs: opcoes.query, body: opcoes.dados,
		headers: opcoes.autenticado === false ? {} : { Authorization: `JWT ${globalThis.token}` },
		encoding: operacao === 'pdf_cronograma' ? 'binary' : 'utf8',
		timeout: 120000, failOnStatusCode: false,
	})
})
