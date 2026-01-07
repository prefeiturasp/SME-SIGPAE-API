describe('Validar rotas de Perfis Vinculados da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/perfis-vinculados/', () => {
		it('Validar GET com sucesso de Perfis Vinculados', () => {
			cy.consultar_perfis_vinculados().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('perfil_master')
				expect(response.body.results[0].perfil_master).to.have.property('nome')
				expect(response.body.results[0].perfil_master).to.have.property('visao')
				expect(response.body.results[0].perfil_master).to.have.property('uuid')
				expect(response.body.results[0]).to.have.property('perfis_subordinados')
				expect(
					response.body.results[0].perfis_subordinados[0],
				).to.have.property('nome')
				expect(
					response.body.results[0].perfis_subordinados[0],
				).to.have.property('visao')
				expect(
					response.body.results[0].perfis_subordinados[0],
				).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de Perfis Vinculados Por Perfil Master', () => {
			var perfil_master = 7
			cy.consultar_perfis_vinculados_por_perfil_master(perfil_master).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('perfil_master')
					expect(response.body.perfil_master).to.have.property('nome')
					expect(response.body.perfil_master).to.have.property('visao')
					expect(response.body.perfil_master).to.have.property('uuid')
					expect(response.body).to.have.property('perfis_subordinados')
					expect(response.body.perfis_subordinados).to.be.an('array')
					expect(response.body.perfis_subordinados[0]).to.have.property('nome')
					expect(response.body.perfis_subordinados[0]).to.have.property('visao')
					expect(response.body.perfis_subordinados[0]).to.have.property('uuid')
				},
			)
		})

		it('Validar GET de Perfis Vinculados Por Perfil Master Não Encontrado', () => {
			var perfil_master = 0
			cy.consultar_perfis_vinculados_por_perfil_master(perfil_master).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it.only('Validar GET com sucesso de Perfis Subordinados Por Perfil Master', () => {
			var perfil_master = ''
			var perfis_subordinados = ''
			cy.consultar_perfis_vinculados().then((response) => {
				expect(response.status).to.eq(200)
				perfil_master = response.body.results[0].perfil_master.nome
				perfis_subordinados =
					response.body.results[0].perfis_subordinados[0].nome
			})

			cy.consultar_perfis_subordinados_por_perfil_master().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.be.an('array')
				expect(response.body).to.contain(perfis_subordinados)
			})
		})

		it('Validar GET de Perfis Subordinados Por Perfil Master Não Encontrado', () => {
			var perfil_master = 'ABC'
			cy.consultar_perfis_subordinados_por_perfil_master(perfil_master).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body)
						.to.have.property('detail')
						.to.eq('Perfil ou Perfis Vinculados não encontrado')
				},
			)
		})
	})
})
