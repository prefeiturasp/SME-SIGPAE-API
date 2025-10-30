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

	context('Rota api/imr/formulario-supervisao/', () => {
		it('Validar GET com sucesso de IMR Formulário Supervisão Por Status EM_PREENCHIMENTO', () => {
			var status = 'EM_PREENCHIMENTO'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('uuid')
					expect(response.body.results[0]).property('diretoria_regional')
					expect(response.body.results[0]).property('unidade_educacional')
					expect(response.body.results[0]).property('data')
					expect(response.body.results[0])
						.property('status')
						.to.eq('Em Preenchimento')
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Por Status NUTRIMANIFESTACAO_A_VALIDAR', () => {
			var status = 'NUTRIMANIFESTACAO_A_VALIDAR'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).property('uuid')
					expect(response.body.results[0]).property('diretoria_regional')
					expect(response.body.results[0]).property('unidade_educacional')
					expect(response.body.results[0]).property('data')
					expect(response.body.results[0])
						.property('status')
						.to.eq('Enviado para CODAE')
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Por Status APROVADO', () => {
			var status = 'APROVADO'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Por Status COM_COMENTARIOS_DE_CODAE', () => {
			var status = 'COM_COMENTARIOS_DE_CODAE'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Por Status VALIDADO_POR_CODAE', () => {
			var status = 'VALIDADO_POR_CODAE'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Com Status Inválido', () => {
			var status = 'STATUS_INVALIDO'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.status[0]).to.eq(
						'Faça uma escolha válida. STATUS_INVALIDO não é uma das escolhas disponíveis.',
					)
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Com UUID Válido', () => {
			var status = 'EM_PREENCHIMENTO'
			var uuid_response = ''
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					uuid_response = response.body.results[0].uuid

					cy.consultar_imr_formulario_supervisao_por_uuid(uuid_response).then(
						(response) => {
							expect(response.status).to.eq(200)
							expect(response.body).to.have.property('diretoria_regional')
							expect(response.body).to.have.property('data')
							expect(response.body).to.have.property('escola')
							expect(response.body).to.have.property('periodo_visita')
							expect(response.body).to.have.property('formulario_base')
							expect(response.body).to.have.property('anexos').to.be.an('array')
							expect(response.body)
								.to.have.property('notificacoes_assinadas')
								.to.be.an('array')
							expect(response.body).to.have.property('criado_em')
							expect(response.body).to.have.property('alterado_em')
							expect(response.body).to.have.property('uuid')
							expect(response.body).to.have.property('status')
							expect(response.body).to.have.property(
								'nome_nutricionista_empresa',
							)
							expect(response.body).to.have.property('acompanhou_visita')
							expect(response.body).to.have.property(
								'maior_frequencia_no_periodo',
							)
						},
					)
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Respostas Com UUID Válido', () => {
			var status = 'EM_PREENCHIMENTO'
			var uuid_response = ''
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					uuid_response = response.body.results[0].uuid

					cy.consultar_imr_formulario_supervisao_respostas(uuid_response).then(
						(response) => {
							expect(response.status).to.eq(200)
							expect(response.body[0]).to.have.property('parametrizacao')
							expect(response.body[0].parametrizacao).to.have.property('uuid')
							expect(response.body[0].parametrizacao).to.have.property(
								'posicao',
							)
							expect(response.body[0].parametrizacao).to.have.property('titulo')
							expect(
								response.body[0].parametrizacao.tipo_pergunta,
							).to.have.property('uuid')
							expect(
								response.body[0].parametrizacao.tipo_pergunta,
							).to.have.property('nome')
							expect(response.body[0].parametrizacao).to.have.property(
								'tipo_ocorrencia',
							)
							expect(response.body[0]).to.have.property('criado_em')
							expect(response.body[0]).to.have.property('alterado_em')
							expect(response.body[0]).to.have.property('uuid')
							expect(response.body[0]).to.have.property('grupo')
							expect(response.body[0]).to.have.property('resposta')
							expect(response.body[0]).to.have.property('formulario_base')
						},
					)
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Respostas Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_respostas(uuid).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Respostas Não Se Aplica Com UUID Válido', () => {
			var status = 'EM_PREENCHIMENTO'
			var uuid_response = ''
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(200)
					uuid_response = response.body.results[0].uuid

					cy.consultar_imr_formulario_supervisao_respostas_nao_aplica(
						uuid_response,
					).then((response) => {
						expect(response.status).to.eq(200)
						expect(response.body).to.be.an('array')
					})
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Respostas Não Se Aplica Com UUID Inválido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_respostas_nao_aplica(uuid).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Dashboard', () => {
			cy.consultar_imr_formulario_supervisao_dashboard().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('status')
				expect(response.body.results[0]).property('label')
				expect(response.body.results[0]).property('total')
			})
		})

		it('Validar GET com sucesso de IMR Formulário Supervisão Lista Nomes Nutricionistas', () => {
			cy.consultar_imr_formulario_supervisao_lista_nomes_nutricionistas().then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					expect(response.body.results[0]).to.eq(
						'SUPER USUARIO NUTRICIONISTA SUPERVISAO',
					)
				},
			)
		})
	})
})
