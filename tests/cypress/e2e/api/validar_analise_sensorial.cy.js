describe('Validar rotas de Analise Sensorial da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	function validarPaginacao(response) {
		expect(response.body).to.have.property('count')
		expect(response.body).to.have.property('next')
		expect(response.body).to.have.property('previous')
		expect(response.body).to.have.property('results')
		expect(response.body.results).to.be.an('array')
	}

	function validarAnaliseSensorial(analiseSensorial) {
		expect(analiseSensorial).to.have.property('homologacao_produto')
		expect(analiseSensorial).to.have.property('data')
		expect(analiseSensorial).to.have.property('hora')
		expect(analiseSensorial).to.have.property('anexos')
		expect(analiseSensorial.anexos).to.be.an('array')
		expect(analiseSensorial).to.have.property('responsavel_produto')
		expect(analiseSensorial).to.have.property('registro_funcional')
		expect(analiseSensorial).to.have.property('observacao')

		if (analiseSensorial.anexos.length > 0) {
			expect(analiseSensorial.anexos[0]).to.have.property('nome')
		}
	}

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/analise-sensorial/', () => {
		it('Validar GET com sucesso de Analise Sensorial', () => {
			cy.consultar_analise_sensorial().then((response) => {
				expect(response.status).to.eq(200)
				validarPaginacao(response)

				if (response.body.results.length > 0) {
					validarAnaliseSensorial(response.body.results[0])
				}
			})
		})

		it('Validar GET com sucesso de Analise Sensorial com limit', () => {
			cy.consultar_analise_sensorial_com_filtros('?limit=1').then((response) => {
				expect(response.status).to.eq(200)
				validarPaginacao(response)
				expect(response.body.results.length).to.be.at.most(1)

				if (response.body.results.length > 0) {
					validarAnaliseSensorial(response.body.results[0])
				}
			})
		})

		it('Validar GET com sucesso de Analise Sensorial com limit e offset', () => {
			var filtro = '?limit=1&offset=0'
			cy.consultar_analise_sensorial_com_filtros(filtro).then((response) => {
				expect(response.status).to.eq(200)
				validarPaginacao(response)
				expect(response.body.results.length).to.be.at.most(1)

				if (response.body.results.length > 0) {
					validarAnaliseSensorial(response.body.results[0])
				}
			})
		})
	})
})
