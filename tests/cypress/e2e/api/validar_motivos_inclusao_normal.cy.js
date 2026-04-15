<<<<<<< HEAD
﻿describe('Validar rotas de Motivos Inclusão Normal da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
﻿describe('Validar rotas de Motivos InclusÃ£o Normal da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/motivos-inclusao-normal/', () => {
		it('Validar GET com sucesso de Motivos InclusÃ£o Normal', () => {
			cy.consultar_motivos_inclusao_normal().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de Motivos InclusÃ£o Normal Com UUID VÃ¡lido', () => {
			var uuid_response = ''
			cy.consultar_motivos_inclusao_normal().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_motivos_inclusao_normal_por_uuid(uuid_response).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('nome')
						expect(response.body).to.have.property('uuid').eq(uuid_response)
					},
				)
			})
		})

		it('Validar GET de Motivos InclusÃ£o Normal Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_motivos_inclusao_normal_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})

