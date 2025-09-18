/// <reference types='cypress' />

describe('Validar rotas de Diretorias Regionais da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dre')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/diretorias-regionais/', () => {
		it('Validar GET com sucesso de Diretorias Regionais com UUID válido', () => {
			var uuid = '8f1da4a7-11b6-4a09-9eaa-6633d066f26b'
			cy.consultar_dre_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.lotes).to.be.an('array')
				expect(response.body.escolas).to.be.an('array')
				expect(response.body).to.have.property('iniciais')
				expect(response.body).to.have.property('nome')
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('codigo_eol')
				expect(response.body).to.have.property('acesso_modulo_medicao_inicial')
			})
		})

		it('Validar GET de Diretorias Regionais com UUID inválido', () => {
			var uuid = '3fa85f64-5717-4562-b3fc-2c963f66afa6'
			cy.consultar_dre_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
