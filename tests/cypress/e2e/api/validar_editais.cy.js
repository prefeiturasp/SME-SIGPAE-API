/// <reference types='cypress' />

describe('Validar rotas da aplicação SIGPAE - ', () => {
	var usuario = Cypress.config('usuario_dre')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para as rotas /api/editais/', () => {
		it('Validar GET com sucesso de Editais', () => {
			cy.consultar_editais().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('numero')
				expect(response.body.results[0]).to.have.property('tipo_contratacao')
				expect(response.body.results[0]).to.have.property('processo')
				expect(response.body.results[0]).to.have.property('objeto')
				expect(response.body.results[0]).to.have.property('eh_imr')
			})
		})

		it('Validar GET de Editais com UUID válido', () => {
			var uuid = 'e40ccae2-2080-4510-aeee-d1b8dcacc3b8'
			cy.consultar_editais_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('numero')
				expect(response.body).to.have.property('tipo_contratacao')
				expect(response.body).to.have.property('processo')
				expect(response.body).to.have.property('objeto')
				expect(response.body).to.have.property('eh_imr')
			})
		})

		it('Validar GET de Editais com UUID inválido', () => {
			var uuid = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
			cy.consultar_editais_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET da Lista de Números de Editais', () => {
			cy.consultar_lista_numeros_editais().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('uuid')
				expect(response.body.results[0]).to.have.property('numero')
			})
		})
	})
})
