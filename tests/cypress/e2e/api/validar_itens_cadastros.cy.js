describe('Validar rotas de Itens Cadastros da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/itens-cadastros/', () => {
		it('Validar GET com sucesso de Itens Cadastros', () => {
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('tipo')
				expect(response.body.results[0]).to.have.property('tipo_display')
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Nome Válido', () => {
			var nome_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome

				var filtro = '?nome=' + nome_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Nome Inválido', () => {
			var filtro = '?nome=NomeInválido Para o Teste'
			cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Tipo Válido', () => {
			var tipo_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				tipo_filtro = response.body.results[0].tipo

				var filtro = '?tipo=' + tipo_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtro Tipo Inválido', () => {
			var filtro = '?tipo=TipoInválido Para o Teste'
			cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Itens Cadastros com filtros Nome e Tipo Válidos', () => {
			var nome_filtro = ''
			var tipo_filtro = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome
				tipo_filtro = response.body.results[0].tipo

				var filtro = '?nome=' + nome_filtro + '&tipo=' + tipo_filtro
				cy.consultar_itens_cadastros_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('tipo')
					expect(response.body.results[0]).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_itens_cadastros().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_itens_cadastros_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('uuid')
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('tipo')
					expect(response.body).to.have.property('tipo_display')
				})
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_itens_cadastros_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Lista Nomes', () => {
			cy.consultar_itens_cadastros_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results).to.have.length.greaterThan(0)
			})
		})

		it('Validar GET com sucesso de Itens Cadastros Tipos', () => {
			cy.consultar_itens_cadastros_tipos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('tipo')
				expect(response.body[0]).to.have.property('tipo_display')
			})
		})
	})
})
