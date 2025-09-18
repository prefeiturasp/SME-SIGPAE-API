/// <reference types='cypress' />

describe('Validar rotas de classificações de dieta da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_cronograma')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/calendario-cronogramas/', () => {
		it('Validar GET de calendário cronogramas com sucesso', () => {
			var parametros = '/?mes=3&ano=2025'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				expect(response.body.results[0]).to.have.property('uuid').that.exist
				expect(response.body.results[0]).to.have.property('nome_produto').that
					.exist
				expect(response.body.results[0]).to.have.property('uuid_cronograma')
					.that.exist
				expect(response.body.results[0]).to.have.property('numero_cronograma')
					.that.exist
				expect(response.body.results[0]).to.have.property('nome_fornecedor')
					.that.exist
				expect(response.body.results[0]).to.have.property('data_programada')
					.that.exist
				expect(response.body.results[0]).to.have.property('numero_empenho').that
					.exist
				expect(response.body.results[0]).to.have.property('etapa').that.exist
				expect(response.body.results[0]).to.have.property('parte')
				expect(response.body.results[0]).to.have.property('quantidade').that
					.exist
				expect(response.body.results[0]).to.have.property('status').that.exist
				expect(response.body.results[0]).to.have.property('unidade_medida').that
					.exist
			})
		})

		it('Validar GET de calendário cronogramas sem parâmetros', () => {
			var parametros = ''
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq(
					'Os parâmetros mes e ano são parametros obrigatórios',
				)
			})
		})

		it('Validar GET de calendário cronogramas com ano inválido', () => {
			var parametros = '/?mes=3&ano=202'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq(
					'Informe um ano valido, deve ser um número inteiro de 4 dígitos (Ex.: 2023)',
				)
			})
		})

		it('Validar GET de calendário cronogramas com mês inválido', () => {
			var parametros = '/?mes=13&ano=2025'
			cy.validar_calendario_cronogramas(parametros).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body[0]).to.eq(
					'Informe um mês valido, deve ser um número inteiro entre 1 e 12',
				)
			})
		})
	})
})
