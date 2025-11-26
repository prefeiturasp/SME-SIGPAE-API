describe('Validar rotas de Laboratórios da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_qualidade')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/laboratorios/', () => {
		it('Validar GET com sucesso de Laboratórios', () => {
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0].contatos[0]).to.have.property('nome')
				expect(response.body.results[0].contatos[0]).to.have.property(
					'telefone',
				)
				expect(response.body.results[0].contatos[0]).to.have.property('email')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('cnpj')
				expect(response.body.results[0]).to.have.property('cep')
				expect(response.body.results[0]).to.have.property('logradouro')
				expect(response.body.results[0]).to.have.property('numero')
				expect(response.body.results[0]).to.have.property('complemento')
				expect(response.body.results[0]).to.have.property('bairro')
				expect(response.body.results[0]).to.have.property('cidade')
				expect(response.body.results[0]).to.have.property('estado')
				expect(response.body.results[0]).to.have.property('credenciado')
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro Nome Válido', () => {
			var nome_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				nome_filtro = response.body.results[0].nome

				var filtro = '?nome=' + nome_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('cnpj')
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro Nome Inválido', () => {
			var filtro = '?nome=NomeInválido Para o Teste'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro CNPJ', () => {
			var cnpj_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				cnpj_filtro = response.body.results[0].cnpj

				var filtro = '?cnpj=' + cnpj_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0]).to.have.property('uuid')
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0])
						.to.have.property('cnpj')
						.to.eq(cnpj_filtro)
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro CNPJ Inválido', () => {
			var filtro = '?cnpj=11110000000000'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios com filtro UUID Válido', () => {
			var uuid_filtro = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				uuid_filtro = response.body.results[0].uuid

				var filtro = '?uuid=' + uuid_filtro
				cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0].contatos[0]).to.have.property('nome')
					expect(response.body.results[0].contatos[0]).to.have.property(
						'telefone',
					)
					expect(response.body.results[0].contatos[0]).to.have.property('email')
					expect(response.body.results[0]).to.have.property('criado_em')
					expect(response.body.results[0]).to.have.property('alterado_em')
					expect(response.body.results[0])
						.to.have.property('uuid')
						.to.eq(uuid_filtro)
					expect(response.body.results[0]).to.have.property('nome')
					expect(response.body.results[0]).to.have.property('cnpj')
					expect(response.body.results[0]).to.have.property('cep')
					expect(response.body.results[0]).to.have.property('logradouro')
					expect(response.body.results[0]).to.have.property('numero')
					expect(response.body.results[0]).to.have.property('complemento')
					expect(response.body.results[0]).to.have.property('bairro')
					expect(response.body.results[0]).to.have.property('cidade')
					expect(response.body.results[0]).to.have.property('estado')
					expect(response.body.results[0]).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios com filtro UUID Inválido', () => {
			var filtro = '?uuid=bd08e0a0-b0b0-0ab0-b000-a05c000f00c0'
			cy.consultar_laboratorios_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').eq(0)
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array').empty
			})
		})

		it('Validar GET com sucesso de Laboratórios Com UUID Válido', () => {
			var uuid_response = ''
			cy.consultar_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_laboratorios_por_uuid(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body.contatos[0]).to.have.property('nome')
					expect(response.body.contatos[0]).to.have.property('telefone')
					expect(response.body.contatos[0]).to.have.property('email')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid').to.eq(uuid_response)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('cnpj')
					expect(response.body).to.have.property('cep')
					expect(response.body).to.have.property('logradouro')
					expect(response.body).to.have.property('numero')
					expect(response.body).to.have.property('complemento')
					expect(response.body).to.have.property('bairro')
					expect(response.body).to.have.property('cidade')
					expect(response.body).to.have.property('estado')
					expect(response.body).to.have.property('credenciado')
				})
			})
		})

		it('Validar GET de Laboratórios Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b00000'
			cy.consultar_laboratorios_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Lista Laboratórios', () => {
			cy.consultar_lista_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('cnpj')
			})
		})

		it('Validar GET com sucesso de Lista Laboratórios Credenciados', () => {
			cy.consultar_lista_laboratorios_credenciados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('nome')
			})
		})

		it('Validar GET com sucesso de Lista Nomes Laboratórios', () => {
			cy.consultar_lista_nomes_laboratorios().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results).to.have.length.greaterThan(0)
			})
		})
	})
})
