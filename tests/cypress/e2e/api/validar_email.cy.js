/// <reference types='cypress' />

describe('Validar rota de Email da aplicacao SIGPAE', () => {
	const parametros = {
		limit: 10,
		offset: 0,
	}

	context('Rota GET api/email/', () => {
		it('Validar GET paginado de Email com sucesso', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))

			cy.consultar_email(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number')
				expect(response.body.results).to.be.an('array')

				response.body.results.forEach((email) => {
					expect(email).to.include.all.keys(
						'host',
						'port',
						'username',
						'password',
						'from_email',
						'use_tls',
						'use_ssl',
						'timeout',
					)
					expect(email.host).to.be.a('string').and.not.be.empty
					expect(email.port).to.be.a('number')
					expect(email.username).to.be.a('string')
					expect(email.password).to.be.a('string')
					expect(email.from_email).to.be.a('string')
					expect(email.use_tls).to.be.a('boolean')
					expect(email.use_ssl).to.be.a('boolean')
					expect(email.timeout).to.be.a('number')
				})
			})
		})

		it('Validar GET de Email sem autenticacao', () => {
			cy.consultar_email(parametros, false).then((response) => {
				expect(response.status).to.eq(401)
				expect(response.body).to.have.property('detail')
			})
		})
	})

	context('Rota POST api/email/', () => {
		// Temporariamente desabilitado: o POST altera a configuracao SMTP do QA.
		it.skip('Validar POST de Email com sucesso', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))

			cy.consultar_email({ limit: 1, offset: 0 }).then((responseLista) => {
				expect(responseLista.status).to.eq(200)
				expect(responseLista.body.results).to.be.an('array').and.not.be.empty

				const dadosEmail = responseLista.body.results[0]

				cy.cadastrar_email(dadosEmail).then((response) => {
					expect(response.status).to.eq(201)
					expect(response.body).to.include.all.keys(
						'host',
						'port',
						'username',
						'password',
						'from_email',
						'use_tls',
						'use_ssl',
						'timeout',
					)
				})
			})
		})

		it('Validar POST de Email com dados invalidos', () => {
			cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))

			cy.cadastrar_email({
				host: '',
				port: 'invalida',
				username: '',
				password: '',
				from_email: 'email-invalido',
				use_tls: 'invalido',
				use_ssl: 'invalido',
				timeout: 'invalido',
			}).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.be.an('object').and.not.be.empty
			})
		})

		it('Validar POST de Email sem autenticacao', () => {
			cy.cadastrar_email(
				{
					host: 'smtp.teste.local',
					port: 587,
					username: 'usuario.teste',
					password: 'senha-teste',
					from_email: 'teste@example.com',
					use_tls: true,
					use_ssl: false,
					timeout: 30,
				},
				false,
			).then((response) => {
				expect(response.status).to.eq(401)
				expect(response.body).to.have.property('detail')
			})
		})
	})
})
