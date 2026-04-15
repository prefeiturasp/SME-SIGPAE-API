/// <reference types='cypress' />

Cypress.Commands.add('consultar_laboratorios', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_laboratorios_com_filtros', (filtros) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/laboratorios/${filtros}`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_laboratorios_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/laboratorios/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_laboratorios', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/laboratorios/lista-laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_laboratorios_credenciados', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/laboratorios/lista-laboratorios-credenciados/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_lista_nomes_laboratorios', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/laboratorios/lista-nomes-laboratorios/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_laboratorios', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/laboratorios/',
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

Cypress.Commands.add('deletar_laboratorios', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/laboratorios/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('put_alterar_laboratorios', (uuid, dados_teste) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/laboratorios/${uuid}/`,
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

Cypress.Commands.add('patch_alterar_laboratorios', (uuid, dados_teste) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/laboratorios/${uuid}/`,
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
