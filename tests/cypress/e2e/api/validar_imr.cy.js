/// <reference types='cypress' />

describe('Validar rotas de IMR da aplicaÃ§Ã£o SIGPAE', () => {
	var usuario = Cypress.env('usuario_codae')
	var senha = Cypress.env('senha')

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

		it('Validar GET com sucesso de IMR Equipamentos Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR Equipamentos Com UUID InvÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR Insumos Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR Insumos Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_insumos(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/mobiliarios/', () => {
		it('Validar GET com sucesso de IMR MobiliÃ¡rios', () => {
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

		it('Validar GET com sucesso de IMR MobiliÃ¡rios Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR MobiliÃ¡rios Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_mobiliarios(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/periodos-de-visita/', () => {
		it('Validar GET com sucesso de IMR PerÃ­odos de Visita', () => {
			usuario = Cypress.env('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.env('senha')
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

		it('Validar GET com sucesso de IMR PerÃ­odos de Visita Com UUID VÃ¡lido', () => {
			usuario = Cypress.env('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.env('senha')
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

		it('Validar GET com sucesso de IMR PerÃ­odos de Visita Com UUID InvÃ¡lido', () => {
			usuario = Cypress.env('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.env('senha')
			cy.autenticar_login(usuario, senha)

			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_periodos_visita(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/reparos-e-adaptacoes/', () => {
		it('Validar GET com sucesso de IMR Reparos e AdaptaÃ§Ãµes', () => {
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

		it('Validar GET com sucesso de IMR Reparos e AdaptaÃ§Ãµes Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR Reparos e AdaptaÃ§Ãµes Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_reparos_adaptacoes(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/utensilios-cozinha/', () => {
		it('Validar GET com sucesso de IMR UtensÃ­lios Cozinha', () => {
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

		it('Validar GET com sucesso de IMR UtensÃ­lios Cozinha Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR UtensÃ­lios Cozinha Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_utensilios_cozinha(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/utensilios-mesa/', () => {
		it('Validar GET com sucesso de IMR UtensÃ­lios Mesa', () => {
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

		it('Validar GET com sucesso de IMR UtensÃ­lios Mesa Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR UtensÃ­lios Mesa Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_utensilios_mesa(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota api/imr/formulario-supervisao/', () => {
		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Por Status EM_PREENCHIMENTO', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Por Status NUTRIMANIFESTACAO_A_VALIDAR', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Por Status APROVADO', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Por Status COM_COMENTARIOS_DE_CODAE', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Por Status VALIDADO_POR_CODAE', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Com Status InvÃ¡lido', () => {
			var status = 'STATUS_INVALIDO'
			cy.consultar_imr_formulario_supervisao_por_status(status).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body).to.have.property('status')
					expect(response.body.status).to.be.an('array').and.not.be.empty

					const mensagemStatus = response.body.status[0]
					const mensagemNormalizada = mensagemStatus
						.normalize('NFD')
						.replace(/[\u0300-\u036f]/g, '')
						.toLowerCase()

					expect(mensagemNormalizada).to.include('faca uma escolha valida')
					expect(mensagemNormalizada).to.include('status_invalido')
					expect(mensagemNormalizada).to.include(
						'nao e uma das escolhas disponiveis',
					)
				},
			)
		})

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_por_uuid(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Respostas Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Respostas Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_respostas(uuid).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Respostas NÃ£o Se Aplica Com UUID VÃ¡lido', () => {
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

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Respostas NÃ£o Se Aplica Com UUID InvÃ¡lido', () => {
			var uuid = '3ac751ee-f95d-4d5b-80da-437506b1906j'
			cy.consultar_imr_formulario_supervisao_respostas_nao_aplica(uuid).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Dashboard', () => {
			cy.consultar_imr_formulario_supervisao_dashboard().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				expect(response.body.results[0]).property('status')
				expect(response.body.results[0]).property('label')
				expect(response.body.results[0]).property('total')
			})
		})

		it('Validar GET com sucesso de IMR FormulÃ¡rio SupervisÃ£o Lista Nomes Nutricionistas', () => {
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

