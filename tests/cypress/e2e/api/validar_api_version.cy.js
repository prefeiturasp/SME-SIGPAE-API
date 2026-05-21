/// <reference types='cypress' />

describe('Validar rota de API Version da aplicacao SIGPAE', () => {
	context('Rota api/api-version/', () => {
		it('Validar GET com sucesso de API Version', () => {
			cy.consultar_api_version().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('API_Version').that.is.not.empty
			})
		})
	})
})
