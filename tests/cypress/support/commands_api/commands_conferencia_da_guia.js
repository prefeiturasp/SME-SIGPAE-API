/// <reference types='cypress' />

Cypress.Commands.add('consultar_conferencia_da_guia', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/conferencia-da-guia/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_por_id_conferencia_da_guia', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/conferencia-da-guia/${uuid}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_conferencia_da_guia', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/conferencia-da-guia/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			guia: dados_teste.guia,
			nome_motorista: dados_teste.nome_motorista,
			placa_veiculo: dados_teste.placa_veiculo,
			data_recebimento: dados_teste.data_recebimento,
			hora_recebimento: dados_teste.hora_recebimento,
			eh_reposicao: dados_teste.eh_reposicao,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('excluir_conferencia_da_guia', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/conferencia-da-guia/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('alterar_conferencia_da_guia', (dados_teste, uuid) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/conferencia-da-guia/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			guia: dados_teste.guia,
			nome_motorista: dados_teste.nome_motorista,
			placa_veiculo: dados_teste.placa_veiculo,
			data_recebimento: dados_teste.data_recebimento,
			hora_recebimento: dados_teste.hora_recebimento,
			eh_reposicao: dados_teste.eh_reposicao,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'alterar_conferencia_da_guia_patch',
	(dados_teste, uuid) => {
		cy.request({
			method: 'PATCH',
			url: Cypress.config('baseUrl') + `api/conferencia-da-guia/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			body: {
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
