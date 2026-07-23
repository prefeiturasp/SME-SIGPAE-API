/// <reference types='cypress' />

Cypress.Commands.add(
	'consultar_conferencia_da_guia_com_ocorrencia',
	(parametros = 'limit=10&offset=1') => {
		return cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/conferencia-da-guia-com-ocorrencia/?${parametros}`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_conferencia_da_guia_com_ocorrencia_por_uuid',
	(uuid) => {
		return cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				`api/conferencia-da-guia-com-ocorrencia/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'cadastrar_conferencia_da_guia_com_ocorrencia',
	(dados_teste) => {
		const conferenciaDosAlimentos = dados_teste.conferencia_dos_alimentos.map(
			(alimento) => {
				const alimentoDaConferencia = {
					conferencia: alimento.conferencia,
					tipo_embalagem: alimento.tipo_embalagem,
					nome_alimento: alimento.nome_alimento,
					qtd_recebido: alimento.qtd_recebido,
					status_alimento: alimento.status_alimento,
					ocorrencia: alimento.ocorrencia,
					observacao: alimento.observacao,
					tem_ocorrencia: alimento.tem_ocorrencia,
				}

				if (alimento.arquivo) {
					alimentoDaConferencia.arquivo = alimento.arquivo
				}

				return alimentoDaConferencia
			},
		)

		return cy.request({
			method: 'POST',
			url:
				Cypress.config('baseUrl') +
				'api/conferencia-da-guia-com-ocorrencia/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			body: {
				conferencia_dos_alimentos: conferenciaDosAlimentos,
				guia: dados_teste.guia,
				nome_motorista: dados_teste.nome_motorista,
				placa_veiculo: dados_teste.placa_veiculo,
				data_recebimento: dados_teste.data_recebimento,
				hora_recebimento: dados_teste.hora_recebimento,
				eh_reposicao: dados_teste.eh_reposicao,
			},
			failOnStatusCode: false,
		})
	},
)
