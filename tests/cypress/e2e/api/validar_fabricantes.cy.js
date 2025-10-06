/// <reference types='cypress' />

describe('Validar rotas de Fabricantes da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/fabricantes/', () => {
		it('Validar GET com sucesso de Fabricantes', () => {
			var uuid = ''
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes com UUID válido', () => {
			var uuid = '79a6ac62-559b-478d-a1e8-f07298d2bbcb'
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('uuid')
				expect(response.body).to.have.property('nome')
			})
		})

		it('Validar GET de Fabricantes com UUID inválido', () => {
			var uuid = '79a6ac62-559b-478d-a1e8-f07298d2aaaa'
			cy.consultar_fabricantes(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes', () => {
			cy.consultar_fabricantes_lista_nomes().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Avaliar Reclamação', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Nova Reclamação', () => {
			cy.consultar_fabricantes_lista_nomes_avaliar_reclamacao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder Reclamação', () => {
			cy.consultar_lista_nomes_responder_reclamacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('nome')
				expect(response.body.results[0]).property('uuid')
			})
		})

		it('Validar GET com sucesso de Fabricantes Lista Nomes Responder Reclamação Escola', () => {
			usuario = Cypress.config('usuario_diretor_ue')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)
			cy.consultar_lista_nomes_responder_reclamacao_escola().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('nome')
					expect(response.body.results[0]).property('uuid')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Responder Reclamação Nutrisupervisor', () => {
			cy.consultar_nomes_responder_reclamacao_nutrisupervisao().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de Lista Nomes Únicos', () => {
			cy.consultar_lista_nomes_unicos().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
			})
		})
	})
})
