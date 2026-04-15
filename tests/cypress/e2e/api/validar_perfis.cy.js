describe('Validar rotas de Perfis da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/perfis/', () => {
		it('Validar GET com sucesso de Perfis', () => {
			cy.consultar_perfis().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('visao')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de Perfis Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_perfis().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_perfis_por_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('visao')
					expect(response.body).to.have.property('uuid').eq(uuid_response)
				})
			})
		})

		it('Validar GET de Perfis Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_perfis_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Perfis Visões', () => {
			cy.consultar_perfis_visoes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('id')
				expect(response.body[0]).to.have.property('nome')
			})
		})
	})
})
