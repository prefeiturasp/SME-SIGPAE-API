/// <reference types='cypress' />

describe('Validar rotas de classificações de dieta da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_classificacoes_dieta') || '13318331325'
	const senha = Cypress.env('senha') || 'adminadmin'

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	
	context('Casos de teste para a rota api/classificacoes-dieta/', () => {
		it('Validar GET de classificações dieta com sucesso', () => {
			var id = ''
			cy.validar_solicitacoes_dieta(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response).to.have.property('body').that.is.an('array').and.not.to
					.be.empty
				response.body.forEach((classificacao) => {
					expect(classificacao).to.have.property('id').that.exist
					expect(classificacao).to.have.property('descricao').that.exist
					expect(classificacao).to.have.property('nome').that.exist
				})
				expect(response.body.map((classificacao) => classificacao.nome)).to.include
					.members(['Tipo A', 'Tipo A ENTERAL', 'Tipo B', 'Tipo C'])
			})
		})

		it('Validar GET por ID de classificações dieta com sucesso', () => {
			var id = '1/'
			cy.validar_solicitacoes_dieta(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('id').equals(1)
				expect(response.body).to.have.property('descricao').that.exist
				expect(response.body).to.have.property('nome').that.exist
			})
		})

		it('Validar GET por ID inválido de classificações dieta', () => {
			var id = '1111/'
			cy.validar_solicitacoes_dieta(id).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
