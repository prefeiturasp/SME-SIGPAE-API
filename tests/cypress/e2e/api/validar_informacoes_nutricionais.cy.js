describe('Validar rotas de Informações Nutricionais da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/informacoes-nutricionais/', () => {
		it('Validar GET com sucesso de Informações Nutricionais', () => {
			var uuid = ''
			cy.consultar_informacoes_nutricionais(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('tipo_nutricional')
				expect(response.body.results[0].tipo_nutricional).to.have.property(
					'nome',
				)
				expect(response.body.results[0].tipo_nutricional).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('eh_dependente')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('medida')
				expect(response.body.results[0]).to.have.property('eh_fixo')
			})
		})

		it('Validar GET com sucesso de Informações Nutricionais Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_informacoes_nutricionais(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_informacoes_nutricionais(uuid_response).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('tipo_nutricional')
						expect(response.body.tipo_nutricional).to.have.property('nome')
						expect(response.body.tipo_nutricional).to.have.property('uuid')
						expect(response.body).to.have.property('eh_dependente')
						expect(response.body).to.have.property('nome')
						expect(response.body).to.have.property('uuid')
						expect(response.body).to.have.property('medida')
						expect(response.body).to.have.property('eh_fixo')
					},
				)
			})
		})

		it('Validar GET com sucesso de Informações Nutricionais Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_informacoes_nutricionais(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Informações Nutricionais Agrupadas', () => {
			cy.consultar_informacoes_nutricionais_agrupadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property(
					'informacoes_nutricionais',
				)
				expect(
					response.body.results[0].informacoes_nutricionais[0],
				).to.have.property('nome')
				expect(
					response.body.results[0].informacoes_nutricionais[0],
				).to.have.property('uuid')
				expect(
					response.body.results[0].informacoes_nutricionais[0],
				).to.have.property('medida')
			})
		})

		it('Validar GET com sucesso de Informações Nutricionais Ordenadas', () => {
			cy.consultar_informacoes_nutricionais_ordenadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('tipo_nutricional')
				expect(response.body.results[0].tipo_nutricional).to.have.property(
					'nome',
				)
				expect(response.body.results[0].tipo_nutricional).to.have.property(
					'uuid',
				)
				expect(response.body.results[0]).to.have.property('eh_dependente')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('medida')
				expect(response.body.results[0]).to.have.property('eh_fixo')
			})
		})
	})
})
