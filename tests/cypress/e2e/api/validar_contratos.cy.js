/// <reference types='cypress' />

describe('Validar rota de contratos da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_coordenador_logistica')
	const senha = Cypress.env('senha')

	context('Rota api/contratos/', () => {
		it('Validar GET paginado de contratos com sucesso', () => {
			const limit = 2
			const offset = 0

			cy.consultar_contratos({ limit, offset, usuario, senha }).then(
				(response) => {
					expect(response.status, JSON.stringify(response.body)).to.eq(200)
					expect(response.body).to.have.all.keys(
						'count',
						'next',
						'previous',
						'results',
					)
					expect(response.body.count).to.be.a('number').and.be.greaterThan(0)
					expect(response.body.results).to.be.an('array').and.have.length(limit)

					response.body.results.forEach((contrato) => {
						expect(contrato).to.include.all.keys(
							'edital',
							'vigencias',
							'lotes',
							'terceirizada',
							'diretorias_regionais',
							'uuid',
							'numero',
							'processo',
							'encerrado',
							'programa',
						)
						expect(contrato.uuid).to.be.a('string').and.not.be.empty
						expect(contrato.vigencias).to.be.an('array')
						expect(contrato.lotes).to.be.an('array')
						expect(contrato.diretorias_regionais).to.be.an('array')
						expect(contrato.terceirizada).to.be.an('object')
					})
				},
			)
		})

		it('Validar GET de contratos sem autenticação', () => {
			cy.consultar_contratos({ limit: 2, offset: 0 }).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(401)
				expect(response.body.detail).to.eq(
					'As credenciais de autenticação não foram fornecidas.',
				)
			})
		})
	})

	context('Rota api/contratos/{uuid}/', () => {
		it('Validar GET de contrato por UUID com sucesso', () => {
			const uuid = '3fa85f64-5717-4562-b3fc-2c963f66afa6'

			cy.consultar_contrato_por_uuid(uuid, usuario, senha).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.include.all.keys(
					'edital',
					'vigencias',
					'lotes',
					'terceirizada',
					'diretorias_regionais',
					'modalidade',
					'uuid',
					'numero',
					'processo',
					'encerrado',
					'programa',
				)
				expect(response.body.uuid).to.eq(uuid)
				expect(response.body.vigencias).to.be.an('array')
				expect(response.body.lotes).to.be.an('array')
				expect(response.body.diretorias_regionais).to.be.an('array')
				expect(response.body.terceirizada).to.be.an('object')
			})
		})

		it('Validar GET de contrato com UUID inexistente', () => {
			const uuidInexistente = 'ffffffff-ffff-4fff-bfff-ffffffffffff'

			cy.consultar_contrato_por_uuid(uuidInexistente, usuario, senha).then(
				(response) => {
					expect(response.status).to.eq(404)
					expect(response.headers['content-type']).to.include('text/html')
					expect(response.body).to.include('Página não encontrada!')
					expect(response.body).to.include('Código do erro: 404')
				},
			)
		})
	})
})
