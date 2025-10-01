/// <reference types='cypress' />

describe('Validar rotas de classificações de dieta da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_diretor_ue')
	var senha = Cypress.config('senha')

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
				expect(response.body[0]).to.have.property('id').that.exist
				expect(response.body[0]).to.have.property('descricao').that.exist
				expect(response.body[0]).to.have.property('nome').that.exist
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
