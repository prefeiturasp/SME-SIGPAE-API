describe('Validar rotas de Terceirizadas da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/terceirizadas/', () => {
		it('Validar GET com sucesso de Terceirizadas', () => {
			cy.consultar_terceirizadas().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property(
					'tipo_alimento_display',
				)
				expect(response.body.results[0]).to.have.property(
					'tipo_empresa_display',
				)
				expect(response.body.results[0]).to.have.property(
					'tipo_servico_display',
				)
				expect(response.body.results[0])
					.to.have.property('nutricionistas')
					.to.be.an('array')

				expect(response.body.results[0].contatos).to.be.an('array')
				expect(response.body.results[0].contratos).to.be.an('array')
				expect(response.body.results[0].lotes).to.be.an('array')
				expect(response.body.results[0]).to.have.property('quantidade_alunos')
				expect(response.body.results[0]).to.have.property('id_externo')
				expect(response.body.results[0])
					.to.have.property('ativo')
					.to.be.a('boolean')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome_fantasia')
				expect(response.body.results[0]).to.have.property('razao_social')
				expect(response.body.results[0]).to.have.property('cnpj')
				expect(response.body.results[0]).to.have.property('representante_legal')
				expect(response.body.results[0]).to.have.property(
					'representante_telefone',
				)
				expect(response.body.results[0]).to.have.property('representante_email')
				expect(response.body.results[0]).to.have.property('endereco')
				expect(response.body.results[0]).to.have.property('numero')
				expect(response.body.results[0]).to.have.property('complemento')
				expect(response.body.results[0]).to.have.property('bairro')
				expect(response.body.results[0]).to.have.property('cidade')
				expect(response.body.results[0]).to.have.property('estado')
				expect(response.body.results[0]).to.have.property('cep')
				expect(response.body.results[0]).to.have.property('responsavel_nome')
				expect(response.body.results[0]).to.have.property('responsavel_cpf')
				expect(response.body.results[0]).to.have.property(
					'responsavel_telefone',
				)
				expect(response.body.results[0]).to.have.property('responsavel_email')
				expect(response.body.results[0]).to.have.property('responsavel_cargo')
				expect(response.body.results[0]).to.have.property('tipo_empresa')
				expect(response.body.results[0]).to.have.property('tipo_servico')
				expect(response.body.results[0]).to.have.property('tipo_alimento')
				expect(response.body.results[0]).to.have.property('criado_em')
			})
		})

		it('Validar GET com sucesso de Terceirizadas Por Nome', () => {
			cy.consultar_terceirizadas().then((response) => {
				expect(response.status).to.eq(200)
				var nome_terceirizada = response.body.results[0].nome_fantasia

				cy.consultar_terceirizadas_por_nome(nome_terceirizada).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('count').to.be.greaterThan(0)
						expect(response.body).to.have.property('next')
						expect(response.body).to.have.property('previous')
						expect(response.body).to.have.property('results')
						expect(response.body.results).to.be.an('array')
						expect(response.body.results[0]).to.have.property(
							'tipo_alimento_display',
						)
						expect(response.body.results[0]).to.have.property(
							'tipo_empresa_display',
						)
						expect(response.body.results[0]).to.have.property(
							'tipo_servico_display',
						)
						expect(response.body.results[0])
							.to.have.property('nutricionistas')
							.to.be.an('array')

						expect(response.body.results[0].contatos).to.be.an('array')
						expect(response.body.results[0].contratos).to.be.an('array')
						expect(response.body.results[0].lotes).to.be.an('array')
						expect(response.body.results[0]).to.have.property(
							'quantidade_alunos',
						)
						expect(response.body.results[0]).to.have.property('id_externo')
						expect(response.body.results[0])
							.to.have.property('ativo')
							.to.be.a('boolean')
						expect(response.body.results[0]).to.have.property('uuid')
						expect(response.body.results[0]).to.have.property('nome_fantasia')
						expect(response.body.results[0]).to.have.property('razao_social')
						expect(response.body.results[0]).to.have.property('cnpj')
						expect(response.body.results[0]).to.have.property(
							'representante_legal',
						)
						expect(response.body.results[0]).to.have.property(
							'representante_telefone',
						)
						expect(response.body.results[0]).to.have.property(
							'representante_email',
						)
						expect(response.body.results[0]).to.have.property('endereco')
						expect(response.body.results[0]).to.have.property('numero')
						expect(response.body.results[0]).to.have.property('complemento')
						expect(response.body.results[0]).to.have.property('bairro')
						expect(response.body.results[0]).to.have.property('cidade')
						expect(response.body.results[0]).to.have.property('estado')
						expect(response.body.results[0]).to.have.property('cep')
						expect(response.body.results[0]).to.have.property(
							'responsavel_nome',
						)
						expect(response.body.results[0]).to.have.property('responsavel_cpf')
						expect(response.body.results[0]).to.have.property(
							'responsavel_telefone',
						)
						expect(response.body.results[0]).to.have.property(
							'responsavel_email',
						)
						expect(response.body.results[0]).to.have.property(
							'responsavel_cargo',
						)
						expect(response.body.results[0]).to.have.property('tipo_empresa')
						expect(response.body.results[0]).to.have.property('tipo_servico')
						expect(response.body.results[0]).to.have.property('tipo_alimento')
						expect(response.body.results[0]).to.have.property('criado_em')
					},
				)
			})
		})

		it('Validar GET com sucesso de Terceirizadas Por UUID', () => {
			cy.consultar_terceirizadas().then((response) => {
				expect(response.status).to.eq(200)
				var uuid_terceirizada = response.body.results[0].uuid

				cy.consultar_terceirizadas_por_uuid(uuid_terceirizada).then(
					(response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.have.property('tipo_alimento_display')
						expect(response.body).to.have.property('tipo_empresa_display')
						expect(response.body).to.have.property('tipo_servico_display')
						expect(response.body)
							.to.have.property('nutricionistas')
							.to.be.an('array')

						expect(response.body.contatos).to.be.an('array')
						expect(response.body.contratos).to.be.an('array')
						expect(response.body.lotes).to.be.an('array')
						expect(response.body).to.have.property('quantidade_alunos')
						expect(response.body).to.have.property('id_externo')
						expect(response.body).to.have.property('ativo').to.be.a('boolean')
						expect(response.body).to.have.property('uuid')
						expect(response.body).to.have.property('nome_fantasia')
						expect(response.body).to.have.property('razao_social')
						expect(response.body).to.have.property('cnpj')
						expect(response.body).to.have.property('representante_legal')
						expect(response.body).to.have.property('representante_telefone')
						expect(response.body).to.have.property('representante_email')
						expect(response.body).to.have.property('endereco')
						expect(response.body).to.have.property('numero')
						expect(response.body).to.have.property('complemento')
						expect(response.body).to.have.property('bairro')
						expect(response.body).to.have.property('cidade')
						expect(response.body).to.have.property('estado')
						expect(response.body).to.have.property('cep')
						expect(response.body).to.have.property('responsavel_nome')
						expect(response.body).to.have.property('responsavel_cpf')
						expect(response.body).to.have.property('responsavel_telefone')
						expect(response.body).to.have.property('responsavel_email')
						expect(response.body).to.have.property('responsavel_cargo')
						expect(response.body).to.have.property('tipo_empresa')
						expect(response.body).to.have.property('tipo_servico')
						expect(response.body).to.have.property('tipo_alimento')
						expect(response.body).to.have.property('criado_em')
					},
				)
			})
		})

		it('Validar GET de Terceirizadas Por UUID Inválido', () => {
			var uuid_terceirizada = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_terceirizadas_por_uuid(uuid_terceirizada).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})
	})
})
