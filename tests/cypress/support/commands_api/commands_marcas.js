/// <reference types='cypress' />

Cypress.Commands.add('consultar_marcas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/marcas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_marcas_por_edital', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/marcas/${param}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_marcas_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/marcas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_marcas_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/marcas/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_nomes_avaliar_reclamacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/marcas/lista-nomes-avaliar-reclamacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_nomes_nova_reclamacao', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/marcas/lista-nomes-nova-reclamacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_nomes_responder_reclamacao', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/marcas/lista-nomes-responder-reclamacao/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_lista_nomes_responder_reclamacao_escola',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/marcas/lista-nomes-responder-reclamacao-escola/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add(
	'consultar_lista_nomes_responder_reclamacao_nutrisupervisor',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/marcas/lista-nomes-responder-reclamacao-nutrisupervisor/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_lista_nomes_unicos', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/marcas/lista-nomes-unicos/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_marcas', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/marcas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			cnpj: dados_teste.cnpj,
			cep: dados_teste.cep,
			logradouro: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			credenciado: dados_teste.credenciado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome,
					telefone: dados_teste.contato_telefone,
					telefone2: dados_teste.contato_telefone,
					celular: dados_teste.contato_celular,
					email: dados_teste.contato_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
					crn_numero: dados_teste.contato_crn_numero,
				},
			],
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_marcas', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/marcas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('put_alterar_marcas', (uuid, dados_teste) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/marcas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			cnpj: dados_teste.cnpj,
			cep: dados_teste.cep,
			logradouro: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			credenciado: dados_teste.credenciado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome,
					telefone: dados_teste.contato_telefone,
					telefone2: dados_teste.contato_telefone,
					celular: dados_teste.contato_celular,
					email: dados_teste.contato_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
					crn_numero: dados_teste.contato_crn_numero,
				},
			],
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('patch_alterar_marcas', (uuid, dados_teste) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/marcas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			cnpj: dados_teste.cnpj,
			cep: dados_teste.cep,
			logradouro: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			credenciado: dados_teste.credenciado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome,
					telefone: dados_teste.contato_telefone,
					telefone2: dados_teste.contato_telefone,
					celular: dados_teste.contato_celular,
					email: dados_teste.contato_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
					crn_numero: dados_teste.contato_crn_numero,
				},
			],
		},
		failOnStatusCode: false,
	})
})
