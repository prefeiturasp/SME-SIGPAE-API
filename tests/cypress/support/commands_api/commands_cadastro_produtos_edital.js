/// <reference types='cypress' />

Cypress.Commands.add('consultar_produtos_edital', (parametros) => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + `api/cadastro-produtos-edital/${parametros}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_produto_edital', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/cadastro-produtos-edital/${uuid}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_produto_edital', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/cadastro-produtos-edital/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			ativo: dados_teste.ativo,
			tipo_produto: dados_teste.tipo_produto,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_lista_completa_logistica', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/cadastro-produtos-edital/lista-completa-logistica/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/cadastro-produtos-edital/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_lista_nomes_logistica', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/cadastro-produtos-edital/lista-nomes-logistica/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('validar_produtos_logistica', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/cadastro-produtos-edital/produtos-logistica/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('atualizar_produto_edital', (uuid, dados_teste) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/cadastro-produtos-edital/${uuid}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			ativo: dados_teste.ativo,
			tipo_produto: dados_teste.tipo_produto,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('excluir_produto_edital', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/cadastro-produtos-edital/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('atualizar_produto_edital_patch', (uuid, dados_teste) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/cadastro-produtos-edital/${uuid}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome: dados_teste.nome,
			ativo: dados_teste.ativo,
			tipo_produto: dados_teste.tipo_produto,
		},
		failOnStatusCode: false,
	})
})
