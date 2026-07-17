/// <reference types='cypress' />

describe('Validar rota CODAE da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_codae')
	const senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/codae/', () => {
		it('Valida GET paginado com sucesso', () => {
			cy.consultar_codae().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number').and.to.be.greaterThan(0)
				expect(response.body.results).to.be.an('array').and.not.to.be.empty

				response.body.results.forEach((codae) => {
					expect(codae).to.include.all.keys(
						'id',
						'quantidade_alunos',
						'nome',
						'uuid',
						'acesso_modulo_medicao_inicial',
					)
					expect(codae.id).to.be.a('number')
					expect(codae.quantidade_alunos).to.be.a('number')
					expect(codae.nome).to.be.a('string').and.not.to.be.empty
					expect(codae.uuid).to.be.a('string').and.not.to.be.empty
					expect(codae.acesso_modulo_medicao_inicial).to.be.a('boolean')
				})
			})
		})
	})
})
