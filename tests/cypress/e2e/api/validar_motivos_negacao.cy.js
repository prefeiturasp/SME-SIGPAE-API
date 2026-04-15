<<<<<<< HEAD
﻿describe('Validar rotas de Motivos de Negação da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')
=======
﻿describe('Validar rotas de Motivos de Negacao da aplicacao SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')
>>>>>>> upstream/testes

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/motivos-negacao/', () => {
		it('Validar GET com sucesso de Motivos de Negação', () => {
			cy.consultar_motivos_negacao().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('id')
				expect(response.body[0]).to.have.property('descricao')
				expect(response.body[0]).to.have.property('processo')
			})
		})

		it('Validar GET com sucesso de Motivos de Negação por Processo', () => {
			var processo = Math.random() < 0.5 ? 'INCLUSAO' : 'CANCELAMENTO' // NOSONAR
			var param = '?processo=' + processo
			cy.consultar_motivos_negacao_por_processo(param).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('id')
				expect(response.body[0]).to.have.property('descricao')
				expect(response.body[0]).to.have.property('processo').to.eq(processo)
			})
		})

<<<<<<< HEAD
		it('Validar GET de Motivos de Negação com Processo Inválido', () => {
=======
		it('Validar GET de Motivos de Negacao com Processo Invalido', () => {
>>>>>>> upstream/testes
			var param = '?processo=NomeInvalidoParaoTeste'
			cy.consultar_motivos_negacao_por_processo(param).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.have.property('processo')
				expect(response.body.processo).to.be.an('array')
				expect(response.body.processo).to.eql([
					'Faça uma escolha válida. NomeInvalidoParaoTeste não é uma das escolhas disponíveis.',
				])
			})
		})

<<<<<<< HEAD
		it('Validar GET com sucesso de Motivos de Negação Com ID Válido', () => {
=======
		it('Validar GET com sucesso de Motivos de Negacao Com ID Valido', () => {
>>>>>>> upstream/testes
			var id_response = ''
			cy.consultar_motivos_negacao().then((response) => {
				expect(response.status).to.eq(200)
				id_response = response.body[0].id

				cy.consultar_motivos_negacao_por_id(id_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('id').eq(id_response)
					expect(response.body).to.have.property('descricao')
					expect(response.body).to.have.property('processo')
				})
			})
		})

<<<<<<< HEAD
		it('Validar GET de Motivos de Negação Com ID Inválido', () => {
=======
		it('Validar GET de Motivos de Negacao Com ID Invalido', () => {
>>>>>>> upstream/testes
			var id = '3ac751e'
			cy.consultar_motivos_negacao_por_id(id).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})

