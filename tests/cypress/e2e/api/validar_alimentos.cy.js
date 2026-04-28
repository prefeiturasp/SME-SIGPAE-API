/// <reference types='cypress' />

describe('Validar rotas de alimentos da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_coordenador_logistica')
	var senha = Cypress.config('senha')
	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/alimentos/', () => {
		it('Validar GET de todos os alimentos do tipo Edital com sucesso', () => {
			var id = '?tipo=E'
			cy.validar_alimentos(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array').and.not.to.be.empty
				const lista = response.body[0]
				expect(lista.ativo, 'O alimento deve estar ativo').to.be.true
				expect(lista).to.have.property('id').that.is.a('number')
				expect(lista).to.have.property('nome').that.is.a('string')
				expect(lista).to.have.property('outras_informacoes').that.is.a('string')
				expect(lista)
					.to.have.property('tipo_listagem_protocolo')
					.that.equals('SO_ALIMENTOS')
				expect(lista)
					.to.have.property('uuid')
					.that.is.a('string')
					.and.have.length.greaterThan(0)
				expect(lista.nome).to.eq('ABACATE')
			})
		})
		it('Validar GET de todos os alimentos do tipo Proprio com sucesso', () => {
			var id = '?tipo=P'
			cy.validar_alimentos(id).then((response) => {
				cy.log(response)
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array').and.not.to.be.empty
				const lista = response.body[0]
				expect(lista.ativo, 'O alimento deve estar ativo').to.be.true
				expect(lista).to.have.property('id').that.is.a('number')
				expect(lista).to.have.property('nome').that.is.a('string')
				expect(lista).to.have.property('outras_informacoes').that.is.a('string')
				expect(lista)
					.to.have.property('tipo_listagem_protocolo')
					.that.equals('SO_ALIMENTOS')
				expect(lista)
					.to.have.property('uuid')
					.that.is.a('string')
					.and.have.length.greaterThan(0)
				expect(lista.nome).to.eq('Alga')
			})
		})
		it('Validar GET de todos os alimentos com sucesso', () => {
			var id = ''
			cy.validar_alimentos(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array').and.not.to.be.empty
				const lista = response.body[0]
				expect(lista.ativo, 'O alimento deve estar ativo').to.be.true
				expect(lista).to.have.property('id').that.is.a('number')
				expect(lista).to.have.property('nome').that.is.a('string')
				expect(lista).to.have.property('outras_informacoes').that.is.a('string')
				expect(lista)
					.to.have.property('tipo_listagem_protocolo')
					.that.equals('SO_ALIMENTOS')
				expect(lista)
					.to.have.property('uuid')
					.that.is.a('string')
					.and.have.length.greaterThan(0)
				expect(lista.nome).to.eq('ABACATE')
			})
		})
		it('Validar GET com parametro invalido de alimento', () => {
			var id = '?tipo=batata'
			cy.validar_alimentos(id).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.have.property('tipo')
				expect(response.body.tipo).to.be.an('array')
				expect(response.body.tipo[0]).to.be.eq(
					'Faça uma escolha válida. batata não é uma das escolhas disponíveis.',
				)
			})
		})
	})

	context('Casos de teste para a rota api/alimentos/id/', () => {
		it('Validar GET com parametro unico valido com sucesso', () => {
			var id = '489/'
			cy.validar_alimentos(id).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.all.keys(
					'ativo',
					'id',
					'marca',
					'nome',
					'outras_informacoes',
					'tipo',
					'tipo_listagem_protocolo',
					'uuid',
				)
				expect(response.body.ativo).to.eq(true)
				expect(response.body.id).to.eq(489)
				expect(response.body.marca).to.be.null
				expect(response.body.nome).to.eq('ABACATE')
				expect(response.body.outras_informacoes).to.eq('')
				expect(response.body.tipo).to.eq('E')
				expect(response.body.tipo_listagem_protocolo).to.eq('SO_ALIMENTOS')
				expect(response.body.uuid).to.eq('b48dc997-2cbd-4c10-9766-711f41637922')
			})
		})

		it('Validar GET com parametro numerico invalido de alimento', () => {
			var id = '54'
			cy.validar_alimentos(id).then((response) => {
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
