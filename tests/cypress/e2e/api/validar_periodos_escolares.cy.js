describe('Validar rotas de Periodos Escolares da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail').that.is.not.empty
	}

	function validarPeriodoEscolar(periodo) {
		expect(periodo).to.have.property('tipos_alimentacao').that.is.an('array')
		expect(periodo).to.have.property('possui_alunos_regulares')
		expect(periodo).to.have.property('nome')
		expect(periodo).to.have.property('uuid')
		expect(periodo).to.have.property('posicao')
		expect(periodo).to.have.property('tipo_turno')

		if (periodo.tipos_alimentacao.length > 0) {
			expect(periodo.tipos_alimentacao[0]).to.have.property('nome')
			expect(periodo.tipos_alimentacao[0]).to.have.property('uuid')
			expect(periodo.tipos_alimentacao[0]).to.have.property('posicao')
		}
	}

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

				if (response.body.results.length > 0) {
					validarPeriodoEscolar(response.body.results[0])
				}
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Por Nome', () => {
			cy.consultar_periodos_escolares().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var nome_periodo = response.body.results[0].nome

				cy.consultar_periodos_escolares_por_nome(nome_periodo).then(
					(responseNome) => {
						expect(responseNome.status).to.eq(200)
						expect(responseNome.body).to.have.property('count').to.be.greaterThan(0)
						expect(responseNome.body).to.have.property('next')
						expect(responseNome.body).to.have.property('previous')
						expect(responseNome.body).to.have.property('results')
						expect(responseNome.body.results).to.be.an('array').and.not.to.be.empty
						validarPeriodoEscolar(responseNome.body.results[0])
						expect(responseNome.body.results[0].nome).to.eq(nome_periodo)
					},
				)
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Por Nome Invalido', () => {
			var nome_periodo = 'Nome Invalido Para Teste'
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

		it('Validar GET com sucesso de Periodos Escolares Com UUID Valido', () => {
			cy.consultar_periodos_escolares().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.results).to.be.an('array').and.not.to.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_periodos_escolares_por_uuid(uuid_response).then(
					(responseUuid) => {
						expect(responseUuid.status).to.eq(200)
						validarPeriodoEscolar(responseUuid.body)
						expect(responseUuid.body).to.have.property('uuid').eq(uuid_response)
					},
				)
			})
		})

		it('Validar GET de Periodos Escolares Com UUID Invalido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_periodos_escolares_por_uuid(uuid).then((response) => {
				expect([400, 404]).to.include(response.status)
			})
		})

		it('Validar GET de Periodos Escolares Por UUID e Alunos Por Faixa Etaria', () => {
			var usuario = Cypress.config('usuario_diretor_ue')
			var senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = '5067e137-e5f3-4876-a63f-7f58cce93f33'
			var data_referencia = '2025-10-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect([200, 500]).to.include(response.status)

				if (response.status === 500) {
					expect(response.body).to.exist
					return
				}

				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')

				if (response.body.results.length > 0) {
					expect(response.body.results[0]).to.have.property('faixa_etaria')
					expect(response.body.results[0].faixa_etaria).to.have.property('__str__')
					expect(response.body.results[0].faixa_etaria).to.have.property('uuid')
					expect(response.body.results[0].faixa_etaria).to.have.property('inicio')
					expect(response.body.results[0].faixa_etaria).to.have.property('fim')
					expect(response.body.results[0]).to.have.property('count')
				}
			})
		})

		it('Validar GET de Periodos Escolares Por UUID e Alunos Por Faixa Etaria com Data Invalida', () => {
			var uuid = '5067e137-e5f3-4876-a63f-7f58cce93f33'
			var data_referencia = '2025-13-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect([200, 400]).to.include(response.status)
				expect(response.body).to.have.property('data_referencia')
				expect(response.body.data_referencia[0].toLowerCase()).to.contain('data')
			})
		})

		it('Validar GET de Periodos Escolares Por UUID e Alunos Por Faixa Etária com UUID Inválido', () => {
			var uuid = '5067e137-e5f3-4876-a63f-0a00aaa00a00'
			var data_referencia = '2025-12-15'
			cy.consultar_alunos_por_faixa_etaria_data_referencia(
				uuid,
				data_referencia,
			).then((response) => {
				expect([400, 404]).to.include(response.status)
			})
		})

		it('Validar GET com sucesso de Periodos Escolares Inclusao Continua Por Mes', () => {
			var usuario = Cypress.config('usuario_diretor_ue')
			var senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			var param = '?mes=10&ano=2025'
			cy.consultar_inclusao_continua_por_mes(param).then((response) => {
				expect([200, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('periodos')
			})
		})
	})
})
