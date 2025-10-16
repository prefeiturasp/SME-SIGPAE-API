/// <reference types='cypress' />

describe('Validar rotas de IMR da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/imr/equipamentos/', () => {
		it('Validar GET com sucesso de IMR Equipamentos', () => {
			var uuid = ''
			cy.consultar_imr_equipamentos(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('status')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Equipamentos Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_equipamentos(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_equipamentos(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('status')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Equipamentos Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_equipamentos(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/insumos/', () => {
		it('Validar GET com sucesso de IMR Insumos', () => {
			var uuid = ''
			cy.consultar_imr_insumos(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('status')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Insumos Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_insumos(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_insumos(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('status')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Insumos Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_insumos(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/mobiliarios/', () => {
		it('Validar GET com sucesso de IMR Mobiliários', () => {
			var uuid = ''
			cy.consultar_imr_mobiliarios(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('status')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Mobiliários Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_mobiliarios(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_mobiliarios(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('status')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Mobiliários Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_mobiliarios(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/periodos-de-visita/', () => {
		it('Validar GET com sucesso de IMR Períodos de Visita', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = ''
			cy.consultar_imr_periodos_visita(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Períodos de Visita Com UUID Válido', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_periodos_visita(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_periodos_visita(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Períodos de Visita Com UUID Inválido', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_periodos_visita(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/reparos-e-adaptacoes/', () => {
		it('Validar GET com sucesso de IMR Reparos e Adaptações', () => {
			var uuid = ''
			cy.consultar_imr_reparos_adaptacoes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Reparos e Adaptações Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_reparos_adaptacoes(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_reparos_adaptacoes(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Reparos e Adaptações Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_reparos_adaptacoes(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/utensilios-cozinha/', () => {
		it('Validar GET com sucesso de IMR Utensílios Cozinha', () => {
			var uuid = ''
			cy.consultar_imr_utensilios_cozinha(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Utensílios Cozinha Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_utensilios_cozinha(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_utensilios_cozinha(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Utensílios Cozinha Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_utensilios_cozinha(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/utensilios-mesa/', () => {
		it('Validar GET com sucesso de IMR Utensílios Mesa', () => {
			var uuid = ''
			cy.consultar_imr_utensilios_mesa(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).to.have.property('nome')
				expect(response.body.results[0]).to.have.property('criado_em')
				expect(response.body.results[0]).to.have.property('alterado_em')
				expect(response.body.results[0]).to.have.property('uuid')
			})
		})

		it('Validar GET com sucesso de IMR Utensílios Mesa Com UUID Válido', () => {
			var uuid = ''
			var uuid_response = ''
			cy.consultar_imr_utensilios_mesa(uuid).then((response) => {
				expect(response.status).to.eq(200)
				uuid_response = response.body.results[0].uuid

				cy.consultar_imr_utensilios_mesa(uuid_response).then((response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('nome')
					expect(response.body).to.have.property('criado_em')
					expect(response.body).to.have.property('alterado_em')
					expect(response.body).to.have.property('uuid')
				})
			})
		})

		it('Validar GET com sucesso de IMR Utensílios Mesa Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_utensilios_mesa(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})
})
