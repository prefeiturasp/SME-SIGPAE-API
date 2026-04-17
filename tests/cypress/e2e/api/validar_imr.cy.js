/// <reference types='cypress' />

describe('Validar rotas de IMR da aplicacao SIGPAE', () => {
	var usuario = Cypress.config('usuario_codae')
	var senha = Cypress.config('senha')

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail').that.is.not.empty
	}

	function validarListaOuPermissao(response, validarItem) {
		expect([200, 403]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
			return false
		}

		expect(response.body).to.have.property('results')
		expect(response.body.results).to.be.an('array')

		if (response.body.results.length > 0 && validarItem) {
			validarItem(response.body.results[0])
		}

		return true
	}

	function validarDetalheOuPermissao(response, validarDetalhe) {
		expect([200, 403]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
			return false
		}

		if (validarDetalhe) {
			validarDetalhe(response.body)
		}

		return true
	}

	function validarUuidInvalidoOuPermissao(response) {
		expect([403, 404]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
		}
	}

	function validarItemComStatus(item) {
		expect(item).to.have.property('nome')
		expect(item).to.have.property('status')
		expect(item).to.have.property('criado_em')
		expect(item).to.have.property('alterado_em')
		expect(item).to.have.property('uuid')
	}

	function validarItemSimples(item) {
		expect(item).to.have.property('nome')
		expect(item).to.have.property('criado_em')
		expect(item).to.have.property('alterado_em')
		expect(item).to.have.property('uuid')
	}

	function validarFormularioListaOuPermissao(response, statusEsperado) {
		expect([200, 403]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
			return false
		}

		expect(response.body).to.have.property('count')
		expect(response.body).to.have.property('next')
		expect(response.body).to.have.property('previous')
		expect(response.body).to.have.property('results')
		expect(response.body.results).to.be.an('array')

		if (response.body.results.length > 0) {
			expect(response.body.results[0]).to.have.property('uuid')
			expect(response.body.results[0]).to.have.property('diretoria_regional')
			expect(response.body.results[0]).to.have.property('unidade_educacional')
			expect(response.body.results[0]).to.have.property('data')

			if (statusEsperado) {
				expect(response.body.results[0]).to.have.property('status').to.eq(statusEsperado)
			}
		}

		return true
	}

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota api/imr/equipamentos/', () => {
		it('Validar GET com sucesso de IMR Equipamentos', () => {
			cy.consultar_imr_equipamentos('').then((response) => {
				validarListaOuPermissao(response, validarItemComStatus)
			})
		})

		it('Validar GET com sucesso de IMR Equipamentos Com UUID Valido', () => {
			cy.consultar_imr_equipamentos('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemComStatus)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_equipamentos(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('status')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Equipamentos Com UUID Invalido', () => {
			cy.consultar_imr_equipamentos('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/insumos/', () => {
		it('Validar GET com sucesso de IMR Insumos', () => {
			cy.consultar_imr_insumos('').then((response) => {
				validarListaOuPermissao(response, validarItemComStatus)
			})
		})

		it('Validar GET com sucesso de IMR Insumos Com UUID Valido', () => {
			cy.consultar_imr_insumos('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemComStatus)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_insumos(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('status')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Insumos Com UUID Invalido', () => {
			cy.consultar_imr_insumos('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/mobiliarios/', () => {
		it('Validar GET com sucesso de IMR Mobiliarios', () => {
			cy.consultar_imr_mobiliarios('').then((response) => {
				validarListaOuPermissao(response, validarItemComStatus)
			})
		})

		it('Validar GET com sucesso de IMR Mobiliarios Com UUID Valido', () => {
			cy.consultar_imr_mobiliarios('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemComStatus)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_mobiliarios(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('status')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Mobiliarios Com UUID Invalido', () => {
			cy.consultar_imr_mobiliarios('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/periodos-de-visita/', () => {
		it('Validar GET com sucesso de IMR Periodos de Visita', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_imr_periodos_visita('').then((response) => {
				validarListaOuPermissao(response, validarItemSimples)
			})
		})

		it('Validar GET com sucesso de IMR Periodos de Visita Com UUID Valido', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_imr_periodos_visita('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemSimples)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_periodos_visita(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Periodos de Visita Com UUID Invalido', () => {
			usuario = Cypress.config('usuario_coordenador_supervisao_nutricao')
			senha = Cypress.config('senha')
			cy.autenticar_login(usuario, senha)

			cy.consultar_imr_periodos_visita('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/reparos-e-adaptacoes/', () => {
		it('Validar GET com sucesso de IMR Reparos e Adaptacoes', () => {
			cy.consultar_imr_reparos_adaptacoes('').then((response) => {
				validarListaOuPermissao(response, validarItemSimples)
			})
		})

		it('Validar GET com sucesso de IMR Reparos e Adaptacoes Com UUID Valido', () => {
			cy.consultar_imr_reparos_adaptacoes('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemSimples)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_reparos_adaptacoes(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Reparos e Adaptacoes Com UUID Invalido', () => {
			cy.consultar_imr_reparos_adaptacoes('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/utensilios-cozinha/', () => {
		it('Validar GET com sucesso de IMR Utensilios Cozinha', () => {
			cy.consultar_imr_utensilios_cozinha('').then((response) => {
				validarListaOuPermissao(response, validarItemSimples)
			})
		})

		it('Validar GET com sucesso de IMR Utensilios Cozinha Com UUID Valido', () => {
			cy.consultar_imr_utensilios_cozinha('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemSimples)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_utensilios_cozinha(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Utensilios Cozinha Com UUID Invalido', () => {
			cy.consultar_imr_utensilios_cozinha('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/utensilios-mesa/', () => {
		it('Validar GET com sucesso de IMR Utensilios Mesa', () => {
			cy.consultar_imr_utensilios_mesa('').then((response) => {
				validarListaOuPermissao(response, validarItemSimples)
			})
		})

		it('Validar GET com sucesso de IMR Utensilios Mesa Com UUID Valido', () => {
			cy.consultar_imr_utensilios_mesa('').then((response) => {
				if (!validarListaOuPermissao(response, validarItemSimples)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_utensilios_mesa(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('nome')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Utensilios Mesa Com UUID Invalido', () => {
			cy.consultar_imr_utensilios_mesa('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})
	})

	context('Rota api/imr/formulario-supervisao/', () => {
		it('Validar GET com sucesso de IMR Formulario Supervisao Por Status EM_PREENCHIMENTO', () => {
			cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO').then((response) => {
				validarFormularioListaOuPermissao(response, 'Em Preenchimento')
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Por Status NUTRIMANIFESTACAO_A_VALIDAR', () => {
			cy.consultar_imr_formulario_supervisao_por_status('NUTRIMANIFESTACAO_A_VALIDAR').then((response) => {
				validarFormularioListaOuPermissao(response, 'Enviado para CODAE')
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Por Status APROVADO', () => {
			cy.consultar_imr_formulario_supervisao_por_status('APROVADO').then((response) => {
				validarFormularioListaOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Por Status COM_COMENTARIOS_DE_CODAE', () => {
			cy.consultar_imr_formulario_supervisao_por_status('COM_COMENTARIOS_DE_CODAE').then((response) => {
				validarFormularioListaOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Por Status VALIDADO_POR_CODAE', () => {
			cy.consultar_imr_formulario_supervisao_por_status('VALIDADO_POR_CODAE').then((response) => {
				validarFormularioListaOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Com Status Invalido', () => {
			cy.consultar_imr_formulario_supervisao_por_status('STATUS_INVALIDO').then((response) => {
				expect([400, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body).to.have.property('status')
				expect(String(response.body.status[0]).toLowerCase()).to.contain('escolha')
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Com UUID Valido', () => {
			cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO').then((response) => {
				if (!validarFormularioListaOuPermissao(response)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_formulario_supervisao_por_uuid(uuid_response).then((responseUuid) => {
					validarDetalheOuPermissao(responseUuid, (body) => {
						expect(body).to.have.property('diretoria_regional')
						expect(body).to.have.property('data')
						expect(body).to.have.property('escola')
						expect(body).to.have.property('periodo_visita')
						expect(body).to.have.property('formulario_base')
						expect(body).to.have.property('anexos').to.be.an('array')
						expect(body).to.have.property('notificacoes_assinadas').to.be.an('array')
						expect(body).to.have.property('criado_em')
						expect(body).to.have.property('alterado_em')
						expect(body).to.have.property('uuid')
						expect(body).to.have.property('status')
						expect(body).to.have.property('nome_nutricionista_empresa')
						expect(body).to.have.property('acompanhou_visita')
						expect(body).to.have.property('maior_frequencia_no_periodo')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Com UUID Invalido', () => {
			cy.consultar_imr_formulario_supervisao_por_uuid('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Respostas Com UUID Valido', () => {
			cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO').then((response) => {
				if (!validarFormularioListaOuPermissao(response)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_formulario_supervisao_respostas(uuid_response).then((responseRespostas) => {
					validarDetalheOuPermissao(responseRespostas, (body) => {
						expect(body).to.be.an('array')
						if (body.length > 0) {
							expect(body[0]).to.have.property('parametrizacao')
							expect(body[0].parametrizacao).to.have.property('uuid')
							expect(body[0].parametrizacao).to.have.property('posicao')
							expect(body[0].parametrizacao).to.have.property('titulo')
							expect(body[0].parametrizacao.tipo_pergunta).to.have.property('uuid')
							expect(body[0].parametrizacao.tipo_pergunta).to.have.property('nome')
							expect(body[0].parametrizacao).to.have.property('tipo_ocorrencia')
							expect(body[0]).to.have.property('criado_em')
							expect(body[0]).to.have.property('alterado_em')
							expect(body[0]).to.have.property('uuid')
							expect(body[0]).to.have.property('grupo')
							expect(body[0]).to.have.property('resposta')
							expect(body[0]).to.have.property('formulario_base')
						}
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Respostas Com UUID Invalido', () => {
			cy.consultar_imr_formulario_supervisao_respostas('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Respostas Nao Se Aplica Com UUID Valido', () => {
			cy.consultar_imr_formulario_supervisao_por_status('EM_PREENCHIMENTO').then((response) => {
				if (!validarFormularioListaOuPermissao(response)) {
					return
				}

				expect(response.body.results).to.not.be.empty
				var uuid_response = response.body.results[0].uuid

				cy.consultar_imr_formulario_supervisao_respostas_nao_aplica(uuid_response).then((responseNaoAplica) => {
					validarDetalheOuPermissao(responseNaoAplica, (body) => {
						expect(body).to.be.an('array')
					})
				})
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Respostas Nao Se Aplica Com UUID Invalido', () => {
			cy.consultar_imr_formulario_supervisao_respostas_nao_aplica('3ac751ee-f95d-4d5b-80da-437506b1906j').then((response) => {
				validarUuidInvalidoOuPermissao(response)
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Dashboard', () => {
			cy.consultar_imr_formulario_supervisao_dashboard().then((response) => {
				if (!validarListaOuPermissao(response, (item) => {
					expect(item).to.have.property('status')
					expect(item).to.have.property('label')
					expect(item).to.have.property('total')
				})) {
					return
				}
			})
		})

		it('Validar GET com sucesso de IMR Formulario Supervisao Lista Nomes Nutricionistas', () => {
			cy.consultar_imr_formulario_supervisao_lista_nomes_nutricionistas().then((response) => {
				if (!validarListaOuPermissao(response)) {
					return
				}

				if (response.body.results.length > 0) {
					expect(response.body.results[0]).to.be.a('string')
				}
			})
		})
	})
})
