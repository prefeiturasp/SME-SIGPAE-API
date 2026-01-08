describe('Validar rotas de Periodos Escolares da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/periodos-escolares/', () => {
		it('Validar GET com sucesso de Periodos Escolares', () => {
			cy.consultar_periodos_escolares().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('tipos_alimentacao')
				expect(response.body.results[0].tipos_alimentacao[0]).to.have.property(
					'nome',
				)
				expect(response.body.results[0].tipos_alimentacao[0]).to.have.property(
					'uuid',
				)
				expect(response.body.results[0].tipos_alimentacao[0]).to.have.property(
					'posicao',
				)
				expect(response.body.results[0]).to.have.property(
					'possui_alunos_regulares',
				)
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('posicao')
				expect(response.body.results[0]).to.have.property('tipo_turno')
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Por Nome', () => {
			cy.consultar_periodos_escolares().then((response) => {
				expect(response.status).to.eq(200)
				var nome_periodo = response.body.results[0].nome

				cy.consultar_periodos_escolares_por_nome(nome_periodo).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('count').to.be.greaterThan(0)
						expect(response.body).to.have.property('next')
						expect(response.body).to.have.property('previous')
						expect(response.body).to.have.property('results')
						expect(response.body.results).to.be.an('array')
						expect(response.body.results[0]).to.have.property(
							'tipos_alimentacao',
						)
						expect(response.body.results[0])
							.to.have.property('nome')
							.to.eq(nome_periodo)
						expect(
							response.body.results[0].tipos_alimentacao[0],
						).to.have.property('uuid')
						expect(
							response.body.results[0].tipos_alimentacao[0],
						).to.have.property('posicao')
						expect(response.body.results[0]).to.have.property(
							'possui_alunos_regulares',
						)
						expect(response.body.results[0]).to.have.property('nome')
						expect(response.body.results[0]).to.have.property('uuid')
						expect(response.body.results[0]).to.have.property('posicao')
						expect(response.body.results[0]).to.have.property('tipo_turno')
					},
				)
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Por Nome Inválido', () => {
			var nome_periodo = 'Nome Inválido Para Teste'
			cy.consultar_periodos_escolares_por_nome(nome_periodo).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count').to.eq(0)
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array').empty
				},
			)
		})

		it('Validar GET com sucesso de Periodos Escolares Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_periodos_escolares().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_periodos_escolares_por_uuid(uuid_response).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body)
							.to.have.property('tipos_alimentacao')
							.to.be.an('array')
						expect(response.body.tipos_alimentacao[0]).to.have.property('nome')
						expect(response.body.tipos_alimentacao[0]).to.have.property('uuid')
						expect(response.body.tipos_alimentacao[0]).to.have.property(
							'posicao',
						)
						expect(response.body).to.have.property('possui_alunos_regulares')
						expect(response.body).to.have.property('nome')
						expect(response.body).to.have.property('uuid').eq(uuid_response)
						expect(response.body).to.have.property('posicao')
						expect(response.body).to.have.property('tipo_turno')
					},
				)
			})
		})

		it('Validar GET de Periodos Escolares Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_periodos_escolares_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Por UUID e Alunos Por Faixa Etária', () => {
			var usuario = Cypress.config('usuario_diretor_ue')
			var senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = '5067e137-e5f3-4876-a63f-7f58cce93f33'
			var data_referencia = '2025-10-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('faixa_etaria')
				expect(response.body.results[0].faixa_etaria).to.have.property(
					'__str__',
				)
				expect(response.body.results[0].faixa_etaria).to.have.property('uuid')
				expect(response.body.results[0].faixa_etaria).to.have.property('inicio')
				expect(response.body.results[0].faixa_etaria).to.have.property('fim')
				expect(response.body.results[0]).to.have.property('count')
			})
		})

		it('Validar GET de Periodos Escolares Por UUID e Alunos Por Faixa Etária com Data Inválida', () => {
			var uuid = '5067e137-e5f3-4876-a63f-7f58cce93f33'
			var data_referencia = '2025-13-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('data_referencia')
				expect(response.body.data_referencia[0]).to.equal(
					'Informe uma data válida.',
				)
			})
		})

		it('Validar GET de Periodos Escolares Por UUID e Alunos Por Faixa Etária com UUID Inválido', () => {
			var uuid = '5067e137-e5f3-4876-a63f-0a00aaa00a00'
			var data_referencia = '2025-12-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Inclusão Contínua Por Mês', () => {
			var usuario = Cypress.config('usuario_diretor_ue')
			var senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			var param = '?mes=10&ano=2025'
			cy.consultar_inclusao_continua_por_mes(param).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('periodos')
			})
		})
	})
})
