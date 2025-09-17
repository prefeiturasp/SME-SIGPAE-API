/// <reference types='cypress' />

Cypress.Commands.add('consultar_editais_contratos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/editais-contratos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_editais_contratos_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/editais-contratos/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_editais_contratos', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/editais-contratos/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_editais_contratos', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/editais-contratos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			contratos: [
				{
					numero: dados_teste.numero,
					lotes: [dados_teste.lotes],
					terceirizada: dados_teste.terceirizada,
					diretorias_regionais: [dados_teste.diretorias_regionais],
					vigencias: [
						{
							data_inicial: dados_teste.data_inicial,
							data_final: dados_teste.data_final,
						},
					],
					processo: dados_teste.processo,
					data_proposta: dados_teste.data_proposta,
					encerrado: dados_teste.encerrado,
					data_hora_encerramento: dados_teste.data_hora_encerramento,
					ata: dados_teste.ata,
					numero_pregao: dados_teste.numero_pregao,
					numero_chamada_publica: dados_teste.numero_chamada_publica,
					edital: dados_teste.edital,
					modalidade: dados_teste.modalidade,
				},
			],
			numero: dados_teste.numero,
			tipo_contratacao: dados_teste.tipo_contratacao,
			processo: dados_teste.processo,
			objeto: dados_teste.objeto,
			eh_imr: dados_teste.eh_imr,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'atualizar_editais_contratos',
	(uuid, uuid_lotes, dados_teste) => {
		cy.request({
			method: 'PUT',
			url: Cypress.config('baseUrl') + `api/editais-contratos/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			body: {
				contratos: [
					{
						uuid: uuid_lotes,
						numero: dados_teste.numero,
						lotes: [dados_teste.lotes],
						terceirizada: dados_teste.terceirizada,
						diretorias_regionais: [dados_teste.diretorias_regionais],
						vigencias: [
							{
								data_inicial: dados_teste.data_inicial,
								data_final: dados_teste.data_final,
							},
						],
						processo: dados_teste.processo,
						data_proposta: dados_teste.data_proposta,
						encerrado: dados_teste.encerrado,
						data_hora_encerramento: dados_teste.data_hora_encerramento,
						ata: dados_teste.ata,
						numero_pregao: dados_teste.numero_pregao,
						numero_chamada_publica: dados_teste.numero_chamada_publica,
						edital: dados_teste.edital,
						modalidade: dados_teste.modalidade,
					},
				],
				numero: dados_teste.numero,
				tipo_contratacao: dados_teste.tipo_contratacao,
				processo: dados_teste.processo,
				objeto: dados_teste.objeto,
				eh_imr: dados_teste.eh_imr,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'atualizar_editais_contratos',
	(uuid, uuid_lotes, dados_teste) => {
		cy.request({
			method: 'PATCH',
			url: Cypress.config('baseUrl') + `api/editais-contratos/${uuid}/`,
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			body: {
				contratos: [
					{
						uuid: uuid_lotes,
						numero: dados_teste.numero,
						lotes: [dados_teste.lotes],
						terceirizada: dados_teste.terceirizada,
						diretorias_regionais: [dados_teste.diretorias_regionais],
						vigencias: [
							{
								data_inicial: dados_teste.data_inicial,
								data_final: dados_teste.data_final,
							},
						],
						processo: dados_teste.processo,
						data_proposta: dados_teste.data_proposta,
						encerrado: dados_teste.encerrado,
						data_hora_encerramento: dados_teste.data_hora_encerramento,
						ata: dados_teste.ata,
						numero_pregao: dados_teste.numero_pregao,
						numero_chamada_publica: dados_teste.numero_chamada_publica,
						edital: dados_teste.edital,
						modalidade: dados_teste.modalidade,
					},
				],
				numero: dados_teste.numero,
				tipo_contratacao: dados_teste.tipo_contratacao,
				processo: dados_teste.processo,
				objeto: dados_teste.objeto,
				eh_imr: dados_teste.eh_imr,
			},
			failOnStatusCode: false,
		})
	},
)
