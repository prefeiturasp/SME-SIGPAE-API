/// <reference types='cypress' />

Cypress.Commands.add('consultar_terceirizadas', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/?limit=2',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_nome', (param) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/?nome=${param}&limit=2`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_por_uuid', (uuid) => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_terceirizadas', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_emails_modulos', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/terceirizadas/emails-por-modulo/?limit=2',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_lista_cnpjs', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-cnpjs/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_empresas_cronogramas', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') +
			'api/terceirizadas/lista-empresas-cronograma/?limit=2',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_lista_nomes', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-nomes/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add(
	'consultar_terceirizadas_lista_nomes_distribuidores',
	() => {
		cy.request({
			method: 'GET',
			url:
				Cypress.config('baseUrl') +
				'api/terceirizadas/lista-nomes-distribuidores/',
			timeout: 60000,
			headers: {
				Authorization: 'JWT ' + globalThis.token,
			},
			failOnStatusCode: false,
		})
	},
)

Cypress.Commands.add('consultar_terceirizadas_lista_simples', () => {
	cy.request({
		method: 'GET',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/lista-simples/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('consultar_terceirizadas_relatorio_quantitativo', () => {
	cy.request({
		method: 'GET',
		url:
			Cypress.config('baseUrl') + 'api/terceirizadas/relatorio-quantitativo/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('cadastrar_terceirizadas', (dados_teste) => {
	cy.request({
		method: 'POST',
		url: Cypress.config('baseUrl') + 'api/terceirizadas/',
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome_fantasia: dados_teste.nome_fantasia,
			razao_social: dados_teste.razao_social,
			cnpj: dados_teste.cnpj,
			representante_legal: dados_teste.representante_legal,
			representante_telefone: dados_teste.representante_telefone,
			representante_email: dados_teste.representante_email,
			cep: dados_teste.cep,
			endereco: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome_nutri,
					crn_numero: dados_teste.crn_numero,
					super_admin_terceirizadas: dados_teste.super_admin_terceirizadas,
					telefone: dados_teste.nutri_telefone,
					email: dados_teste.nutri_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
				},
			],
			responsavel_cargo: dados_teste.responsavel_cargo,
			responsavel_cpf: dados_teste.responsavel_cpf,
			responsavel_nome: dados_teste.responsavel_nome,
			responsavel_telefone: dados_teste.responsavel_telefone,
			responsavel_email: dados_teste.responsavel_email,
			lotes: dados_teste.lotes,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('alterar_terceirizadas_put', (uuid, dados_teste) => {
	cy.request({
		method: 'PUT',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome_fantasia: dados_teste.nome_fantasia,
			razao_social: dados_teste.razao_social,
			cnpj: dados_teste.cnpj,
			representante_legal: dados_teste.representante_legal,
			representante_telefone: dados_teste.representante_telefone,
			representante_email: dados_teste.representante_email,
			cep: dados_teste.cep,
			endereco: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome_nutri,
					crn_numero: dados_teste.crn_numero,
					super_admin_terceirizadas: dados_teste.super_admin_terceirizadas,
					telefone: dados_teste.nutri_telefone,
					email: dados_teste.nutri_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
				},
			],
			responsavel_cargo: dados_teste.responsavel_cargo,
			responsavel_cpf: dados_teste.responsavel_cpf,
			responsavel_nome: dados_teste.responsavel_nome,
			responsavel_telefone: dados_teste.responsavel_telefone,
			responsavel_email: dados_teste.responsavel_email,
			lotes: dados_teste.lotes,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('alterar_terceirizadas_patch', (uuid, dados_teste) => {
	cy.request({
		method: 'PATCH',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		body: {
			nome_fantasia: dados_teste.nome_fantasia,
			razao_social: dados_teste.razao_social,
			cnpj: dados_teste.cnpj,
			representante_legal: dados_teste.representante_legal,
			representante_telefone: dados_teste.representante_telefone,
			representante_email: dados_teste.representante_email,
			cep: dados_teste.cep,
			endereco: dados_teste.logradouro,
			numero: dados_teste.numero,
			bairro: dados_teste.bairro,
			cidade: dados_teste.cidade,
			estado: dados_teste.estado,
			complemento: dados_teste.complemento,
			contatos: [
				{
					nome: dados_teste.contato_nome_nutri,
					crn_numero: dados_teste.crn_numero,
					super_admin_terceirizadas: dados_teste.super_admin_terceirizadas,
					telefone: dados_teste.nutri_telefone,
					email: dados_teste.nutri_email,
					eh_nutricionista: dados_teste.contato_eh_nutricionista,
				},
			],
			responsavel_cargo: dados_teste.responsavel_cargo,
			responsavel_cpf: dados_teste.responsavel_cpf,
			responsavel_nome: dados_teste.responsavel_nome,
			responsavel_telefone: dados_teste.responsavel_telefone,
			responsavel_email: dados_teste.responsavel_email,
			lotes: dados_teste.lotes,
		},
		failOnStatusCode: false,
	})
})

Cypress.Commands.add('deletar_terceirizadas', (uuid) => {
	cy.request({
		method: 'DELETE',
		url: Cypress.config('baseUrl') + `api/terceirizadas/${uuid}/`,
		timeout: 60000,
		headers: {
			Authorization: 'JWT ' + globalThis.token,
		},
		failOnStatusCode: false,
	})
})
