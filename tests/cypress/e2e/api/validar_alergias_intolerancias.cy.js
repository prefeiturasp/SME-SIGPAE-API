/// <reference types='cypress' />

describe('Validar rotas de alergias intolerancias da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_coordenador_logistica')
	var senha = Cypress.config('senha')
	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/alergias-intolerancias/', () => {
		it('Validar GET de todas as alergias intolerancias com sucesso', () => {
			var id = ''
			cy.validar_alergias_intolerancias(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array').and.not.to.be.empty
				expect(response.body[0]).to.have.property('descricao').that.is.a('string')
				expect(response.body[0].descricao).to.include('ARGININEMIA')
				expect(response.body[0]).to.have.property('id').that.equals(127)
			})
		})
	})

	context('Casos de teste para a rota api/alergias-intolerancias/id/', () => {
		it('Validar GET de todas as alergias intolerancias com sucesso', () => {
			var id = '127/'
			cy.validar_alergias_intolerancias(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('descricao').that.is.a('string')
				expect(response.body).to.have.property('id').that.is.a('number')
				expect(response.body.descricao).to.eq('ARGININEMIA')
				expect(response.body.id).to.eq(127)
			})
		})

		it('Validar GET com id invalido sem a /', () => {
			var id = '1'
			cy.validar_alergias_intolerancias(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.redirects[0]).to.contain('301:')
				expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
				expect(response.allRequestResponses[0])
					.to.have.property('Response Status')
					.that.equals(301)
				expect(response.redirects).to.be.an('array').that.is.not.empty
			})
		})

		it('Validar GET com id invalido em texto', () => {
			var id = 'açe'
			cy.validar_alergias_intolerancias(id).then((response) => {
				expect(response.allRequestResponses[0]['Response Status']).to.eq(301)
				expect(response.status).to.eq(200)
				expect(response.body).to.exist
				expect(response.redirects[0]).to.contain('301:')
				expect(response.allRequestResponses).to.be.an('array').that.is.not.empty
				expect(response.allRequestResponses[0])
					.to.have.property('Response Status')
					.that.equals(301)
				expect(response.redirects).to.be.an('array').that.is.not.empty
			})
		})
	})
})
