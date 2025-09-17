/// <reference types='cypress' />

Cypress.Commands.add('validar_alimentos_da_guia', (id) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/alimentos-da-guia/${id}`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_alimentos_da_guia', (alimento) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/alimentos-da-guia/',
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			codigo_suprimento: alimento.codigo_suprimento,
			codigo_papa: alimento.codigo_papa,
			nome_alimento: alimento.nome_alimento,
			guia: alimento.guia
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('excluir_alimentos_da_guia', (id) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/alimentos-da-guia/${id}/`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('alterar_alimentos_da_guia', (id,alimento_alterado) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/alimentos-da-guia/${id}/`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			codigo_suprimento: alimento_alterado.codigo_suprimento,
			codigo_papa: alimento_alterado.codigo_papa,
			nome_alimento: alimento_alterado.nome_alimento,
			guia: alimento_alterado.guia
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('alterar_alimentos_da_guia_patch', (id,alimento_alterado) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/alimentos-da-guia/${id}/`,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			codigo_suprimento: alimento_alterado.codigo_suprimento,
			codigo_papa: alimento_alterado.codigo_papa,
			nome_alimento: alimento_alterado.nome_alimento,
			guia: alimento_alterado.guia
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('Validar_lista_de_nomes_alimentos_da_guia', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/alimentos-da-guia/lista-nomes/',
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})