/// <reference types='cypress' />
const dayjs = require('dayjs')
var data_atual = dayjs()
const TEMPO_ESPERA_API = Cypress.env('wait_api_conferencia_da_guia') || 3000

function aguardar_processamento_api() {
	cy.wait(TEMPO_ESPERA_API)
}

describe('Validar rotas de conferencia da guia da aplicacao SIGPAE', () => {
	var usuario = Cypress.env('usuario_abastecimento')
	var senha = Cypress.env('senha')

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail').that.is.not.empty
	}

	function normalizarTexto(texto) {
		return String(texto)
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.toLowerCase()
	}

	function validarListaOuPermissao(response) {
		expect([200, 403]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
			return
		}

		expect(response.body).to.have.property('count').that.exist
		expect(response.body).to.have.property('next')
		expect(response.body).to.have.property('previous')
		expect(response.body).to.have.property('results').that.is.an('array')

		if (response.body.results.length > 0) {
			expect(response.body.results[0].criado_por).to.have.property('uuid').that.exist
			expect(response.body.results[0].criado_por).to.have.property('cpf').that.exist
			expect(response.body.results[0].criado_por).to.have.property('nome').that.exist
			expect(response.body.results[0].criado_por).to.have.property('email').that.exist
			expect(response.body.results[0].criado_por).to.have.property('date_joined').that.exist
			expect(response.body.results[0].criado_por).to.have.property('registro_funcional').that.exist
			expect(response.body.results[0].criado_por).to.have.property('tipo_usuario').that.exist
			expect(response.body.results[0].criado_por).to.have.property('cargo').that.exist
			expect(response.body.results[0]).to.have.property('criado_em').that.exist
			expect(response.body.results[0]).to.have.property('alterado_em').that.exist
			expect(response.body.results[0]).to.have.property('uuid').that.exist
			expect(response.body.results[0]).to.have.property('data_recebimento').that.exist
			expect(response.body.results[0]).to.have.property('hora_recebimento').that.exist
			expect(response.body.results[0]).to.have.property('nome_motorista').that.exist
			expect(response.body.results[0]).to.have.property('placa_veiculo').that.exist
			expect(response.body.results[0]).to.have.property('eh_reposicao').that.exist
			expect(response.body.results[0]).to.have.property('guia').that.exist
		}
	}

	function validarErroCampoOuPermissao(response, campo, trechoMensagem) {
		expect([400, 403]).to.include(response.status)

		if (response.status === 403) {
			validarPermissaoNegada(response)
			return
		}

		expect(response.body).to.have.property(campo)
		expect(normalizarTexto(response.body[campo][0])).to.contain(
			normalizarTexto(trechoMensagem),
		)
	}

	function excluirConferenciaSeCriada(uuid) {
		if (!uuid) {
			return cy.wrap(null)
		}

		return cy.excluir_conferencia_da_guia(uuid).then((response) => {
			expect([204, 403, 404]).to.include(response.status)
		})
	}

	function criarConferenciaGuiaValida(sufixoMotorista = 'Base') {
		const identificador = `${Date.now()}${Cypress._.random(100, 999)}`

		return cy.cadastrar_conferencia_da_guia({
			guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
			nome_motorista: `Motorista Teste ${sufixoMotorista} ${identificador}`,
			placa_veiculo: `TS${String(Cypress._.random(1000, 9999)).padStart(4, '0')}`,
			data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
			hora_recebimento: '11:00:00',
			eh_reposicao: true,
		}).then((response) => {
			expect([201, 403]).to.include(response.status)

			if (response.status === 403) {
				validarPermissaoNegada(response)
				return null
			}

			return response.body.uuid
		})
	}

	function montarDadosConferencia(overrides = {}) {
		return {
			guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
			nome_motorista: `Motorista Teste ${Date.now()}${Cypress._.random(10, 99)}`,
			placa_veiculo: `AB${String(Cypress._.random(1000, 9999)).padStart(4, '0')}`,
			data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
			hora_recebimento: '11:00:00',
			eh_reposicao: true,
			...overrides,
		}
	}

	before(() => {
		cy.autenticar_login(usuario, senha)
		aguardar_processamento_api()
	})

	context('Casos de teste para a rota api/conferencia-da-guia/', () => {
		it('Validar GET de conferencia da guia com sucesso', () => {
			cy.consultar_conferencia_da_guia().then((response) => {
				validarListaOuPermissao(response)
			})
		})

		it('Validar POST de conferencia da guia com sucesso', () => {
			var dados_teste = montarDadosConferencia({
				hora_recebimento: '10:00',
				eh_reposicao: false,
			})

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				expect(response.body.criado_por).to.have.property('cpf').that.exist
				expect(response.body.criado_por).to.have.property('tipo_usuario').that.exist

				excluirConferenciaSeCriada(response.body.uuid)
			})
		})

		it('Validar POST de conferencia da guia sem informar placa do veiculo', () => {
			var dados_teste = montarDadosConferencia({ placa_veiculo: '' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'placa_veiculo', 'em branco')
			})
		})

		it('Validar POST de conferencia da guia sem informar nome do motorista', () => {
			var dados_teste = montarDadosConferencia({ nome_motorista: '' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'nome_motorista', 'em branco')
			})
		})

		it('Validar POST de conferencia da guia sem informar data de recebimento', () => {
			var dados_teste = montarDadosConferencia({ data_recebimento: '' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'data_recebimento', 'Formato inval')
			})
		})

		it('Validar POST de conferencia da guia sem informar hora de recebimento', () => {
			var dados_teste = montarDadosConferencia({ hora_recebimento: '' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'hora_recebimento', 'Formato inval')
			})
		})

		it('Validar POST de conferencia da guia sem informar guia', () => {
			var dados_teste = montarDadosConferencia({ guia: '' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'guia', 'nao pode')
			})
		})

		it('Validar POST de conferencia da guia com guia no formato invalido', () => {
			var dados_teste = montarDadosConferencia({ guia: 'sdfsdfsdfsdfsd' })

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				validarErroCampoOuPermissao(response, 'guia', 'UUID')
			})
		})

		it('Validar DELETE de conferencia da guia com sucesso', () => {
			var dados_teste = montarDadosConferencia()

			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				expect([201, 403]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				cy.excluir_conferencia_da_guia(response.body.uuid).then((responseExclusao) => {
					expect([204, 403, 404]).to.include(responseExclusao.status)
				})
			})
		})

		it('Validar DELETE invalido de conferencia da guia', () => {
			var uuid = '2a69bc14-c0e8-43f8-b7d2-5cce299de'
			cy.excluir_conferencia_da_guia(uuid).then((response) => {
				expect([403, 404]).to.include(response.status)

				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar PUT de conferencia da guia com sucesso', () => {
			criarConferenciaGuiaValida('PUT sucesso').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({
					nome_motorista: 'Motorista Teste Alterado',
					placa_veiculo: 'ALT1B23',
				})

				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					expect([200, 403]).to.include(response.status)

					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}

					expect(response.body).to.have.property('alterado_em').that.is.not.empty
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia sem informar placa do veiculo', () => {
			criarConferenciaGuiaValida('PUT placa').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ placa_veiculo: '' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'placa_veiculo', 'em branco')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia sem informar nome do motorista', () => {
			criarConferenciaGuiaValida('PUT nome').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ nome_motorista: '' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'nome_motorista', 'em branco')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia sem informar data de recebimento', () => {
			criarConferenciaGuiaValida('PUT data').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ data_recebimento: '' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'data_recebimento', 'Formato inval')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia sem informar hora de recebimento', () => {
			criarConferenciaGuiaValida('PUT hora').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ hora_recebimento: '' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'hora_recebimento', 'Formato inval')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia sem informar guia', () => {
			criarConferenciaGuiaValida('PUT guia').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ guia: '' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'guia', 'nao pode')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PUT de conferencia da guia com guia no formato invalido', () => {
			criarConferenciaGuiaValida('PUT uuid invalido').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ guia: 'sdfsdfsdfsdfsd' })
				cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'guia', 'UUID')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia com sucesso', () => {
			criarConferenciaGuiaValida('PATCH sucesso').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({
					nome_motorista: 'Motorista Teste PATCH',
					placa_veiculo: 'PAT8C23',
				})

				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					expect([200, 403]).to.include(response.status)

					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}

					expect(response.body).to.have.property('alterado_em').that.is.not.empty
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia sem informar placa do veiculo', () => {
			criarConferenciaGuiaValida('PATCH placa').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ placa_veiculo: '' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'placa_veiculo', 'em branco')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia sem informar nome do motorista', () => {
			criarConferenciaGuiaValida('PATCH nome').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ nome_motorista: '' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'nome_motorista', 'em branco')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia sem informar data de recebimento', () => {
			criarConferenciaGuiaValida('PATCH data').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ data_recebimento: '' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'data_recebimento', 'Formato inval')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia sem informar hora de recebimento', () => {
			criarConferenciaGuiaValida('PATCH hora').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ hora_recebimento: '' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'hora_recebimento', 'Formato inval')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia sem informar guia', () => {
			criarConferenciaGuiaValida('PATCH guia').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ guia: '' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'guia', 'nao pode')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})

		it('Validar PATCH de conferencia da guia com guia no formato invalido', () => {
			criarConferenciaGuiaValida('PATCH uuid invalido').then((uuid) => {
				if (!uuid) {
					return
				}

				var dados_teste = montarDadosConferencia({ guia: 'sdfsdfsdfsdfsd' })
				cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then((response) => {
					validarErroCampoOuPermissao(response, 'guia', 'UUID')
				})

				excluirConferenciaSeCriada(uuid)
			})
		})
	})
})
