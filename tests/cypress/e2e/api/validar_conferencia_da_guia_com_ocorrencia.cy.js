/// <reference types='cypress' />

describe('Validar conferência da guia com ocorrência da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_abastecimento')
	const senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota GET api/conferencia-da-guia-com-ocorrencia/', () => {
		it('Valida a listagem paginada com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number').and.to.be.greaterThan(0)
				expect(response.body.results).to.be.an('array').and.not.to.be.empty

				response.body.results.forEach((conferencia) => {
					expect(conferencia).to.have.property('criado_por').that.is.an('object')
					expect(conferencia.criado_por).to.include.all.keys(
						'uuid',
						'cpf',
						'nome',
						'email',
					)
					expect(conferencia)
						.to.have.property('conferencia_dos_alimentos')
						.that.is.an('array')
				})
			})
		})
	})
})
