/// <reference types='cypress' />
const dayjs = require('dayjs')
var data_atual = dayjs()

describe('Validar rotas de conferência da guia da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_abastecimento')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/conferencia-da-guia/', () => {
		it('Validar GET de conferencia da guia com sucesso', () => {
			cy.consultar_conferencia_da_guia().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.have.property('count').that.exist
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results').that.is.an('array')
					.and.not.to.be.empty
				expect(response.body.results[0].criado_por).to.have.property('uuid')
					.that.exist
				expect(response.body.results[0].criado_por).to.have.property('cpf').that
					.exist
				expect(response.body.results[0].criado_por).to.have.property('nome')
					.that.exist
				expect(response.body.results[0].criado_por).to.have.property('email')
					.that.exist
				expect(response.body.results[0].criado_por).to.have.property(
					'date_joined',
				).that.exist
				expect(response.body.results[0].criado_por).to.have.property(
					'registro_funcional',
				).that.exist
				expect(response.body.results[0].criado_por).to.have.property(
					'tipo_usuario',
				).that.exist
				expect(response.body.results[0].criado_por).to.have.property('cargo')
					.that.exist
				expect(response.body.results[0]).to.have.property('criado_em').that
					.exist
				expect(response.body.results[0]).to.have.property('alterado_em').that
					.exist
				expect(response.body.results[0]).to.have.property('uuid').that.exist
				expect(response.body.results[0]).to.have.property('data_recebimento')
					.that.exist
				expect(response.body.results[0]).to.have.property('hora_recebimento')
					.that.exist
				expect(response.body.results[0]).to.have.property('nome_motorista').that
					.exist
				expect(response.body.results[0]).to.have.property('placa_veiculo').that
					.exist
				expect(response.body.results[0]).to.have.property('eh_reposicao').that
					.exist
				expect(response.body.results[0]).to.have.property('guia').that.exist
			})
		})

		it('Validar GET por UUID de conferencia da guia com sucesso', () => {
			var uuid = '2a69bc14-c0e8-43f8-b7d2-5cce299de4f4/'
			cy.consultar_por_id_conferencia_da_guia(uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body.criado_por).to.have.property('uuid').that.exist
				expect(response.body.criado_por).to.have.property('cpf').that.exist
				expect(response.body.criado_por).to.have.property('nome').that.exist
				expect(response.body.criado_por).to.have.property('email').that.exist
				expect(response.body.criado_por).to.have.property('date_joined').that
					.exist
				expect(response.body.criado_por).to.have.property('registro_funcional')
					.that.exist
				expect(response.body.criado_por).to.have.property('tipo_usuario').that
					.exist
				expect(response.body.criado_por).to.have.property('cargo').that.exist
				expect(response.body).to.have.property('criado_em').that.exist
				expect(response.body).to.have.property('alterado_em').that.exist
				expect(response.body).to.have.property('uuid').that.exist
				expect(response.body).to.have.property('data_recebimento').that.exist
				expect(response.body).to.have.property('hora_recebimento').that.exist
				expect(response.body).to.have.property('nome_motorista').that.exist
				expect(response.body).to.have.property('placa_veiculo').that.exist
				expect(response.body).to.have.property('eh_reposicao').that.exist
				expect(response.body).to.have.property('guia').that.exist
			})
		})

		it('Validar GET por UUID inváido de conferencia da guia', () => {
			var uuid = '2a69bc14-c0e8-43f8-b7d2-5cce299de/'
			cy.validar_solicitacoes_dieta(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar POST de conferencia da guia com sucesso', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação',
				placa_veiculo: 'ABC1D23',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '10:00',
				eh_reposicao: false,
			}
			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				expect(response.body.criado_por['cpf']).to.eq('12345678997')
				expect(response.body.criado_por['tipo_usuario']).to.eq('escola')
				var uuid = response.body['uuid']
				cy.excluir_conferencia_da_guia(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
					expect(response_exclusao.body).to.be.empty
				})
			})
		})

		it('Validar POST de conferencia da guia sem informar placa do veículo', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: '',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.placa_veiculo[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar POST de conferencia da guia sem informar nome do motirista', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: '',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome_motorista[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar POST de conferencia da guia sem informar data de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: '',
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.data_recebimento[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
			})
		})

		it('Validar POST de conferencia da guia sem informar hora de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.hora_recebimento[0]).to.eq(
					'Formato inválido para tempo. Use um dos formatos a seguir: hh:mm:ss, hh:mm[:ss[.uuuuuu]].',
				)
			})
		})

		it('Validar POST de conferencia da guia sem informar guia', () => {
			var dados_teste = {
				guia: '',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar POST de conferencia da guia com guia no formato inválido', () => {
			var dados_teste = {
				guia: 'sdfsdfsdfsdfsd',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.cadastrar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq(
					'O valor “sdfsdfsdfsdfsd” não é um UUID válido',
				)
			})
		})

		it('Validar DELETE de conferencia da guia com sucesso', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação',
				placa_veiculo: 'AAA1B23',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			cy.cadastrar_conferencia_da_guia(dados_teste).then((response) => {
				expect(response.status).to.eq(201)
				var uuid = response.body['uuid']
				cy.excluir_conferencia_da_guia(uuid).then((response_exclusao) => {
					expect(response_exclusao.status).to.eq(204)
					expect(response_exclusao.body).to.be.empty
				})
			})
		})

		it('Validar DELETE inváido de conferencia da guia', () => {
			var uuid = '2a69bc14-c0e8-43f8-b7d2-5cce299de/'
			cy.excluir_conferencia_da_guia(uuid).then((response) => {
				expect(response.status).to.eq(404)
			})
		})

		it('Validar PUT de conferencia da guia com sucesso', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação Alterado',
				placa_veiculo: 'ALT1B23',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = '86141002-926d-48bb-a3ed-9e63a2ba6917'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body['alterado_em']).to.contain(
					data_atual.format('DD/MM/YYYY'),
				)
			})
		})

		it('Validar PUT de conferencia da guia sem informar placa do veículo', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: '',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.placa_veiculo[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar PUT de conferencia da guia sem informar nome do motirista', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: '',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.nome_motorista[0]).to.eq(
					'Este campo não pode estar em branco.',
				)
			})
		})

		it('Validar PUT de conferencia da guia sem informar data de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: '',
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.data_recebimento[0]).to.eq(
					'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
				)
			})
		})

		it('Validar PUT de conferencia da guia sem informar hora de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.hora_recebimento[0]).to.eq(
					'Formato inválido para tempo. Use um dos formatos a seguir: hh:mm:ss, hh:mm[:ss[.uuuuuu]].',
				)
			})
		})

		it('Validar PUT de conferencia da guia sem informar guia', () => {
			var dados_teste = {
				guia: '',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq('Este campo não pode ser nulo.')
			})
		})

		it('Validar PUT de conferencia da guia com guia no formato inválido', () => {
			var dados_teste = {
				guia: 'sdfsdfsdfsdfsd',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia(dados_teste, uuid).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body.guia[0]).to.eq(
					'O valor “sdfsdfsdfsdfsd” não é um UUID válido',
				)
			})
		})

		it('Validar PATCH de conferencia da guia com sucesso', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'PAT8C23',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(200)
					expect(response.body['alterado_em']).to.contain(
						data_atual.format('DD/MM/YYYY'),
					)
				},
			)
		})

		it('Validar PATCH de conferencia da guia sem informar placa do veículo', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: '',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.placa_veiculo[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
				},
			)
		})

		it('Validar PATCH de conferencia da guia sem informar nome do motirista', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: '',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.nome_motorista[0]).to.eq(
						'Este campo não pode estar em branco.',
					)
				},
			)
		})

		it('Validar PATCH de conferencia da guia sem informar data de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: '',
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.data_recebimento[0]).to.eq(
						'Formato inválido para data. Use um dos formatos a seguir: DD/MM/YYYY, YYYY-MM-DD.',
					)
				},
			)
		})

		it('Validar PATCH de conferencia da guia sem informar hora de recebimento', () => {
			var dados_teste = {
				guia: '7ceb5d9f-4c90-42d8-b295-316c4aab3276',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.hora_recebimento[0]).to.eq(
						'Formato inválido para tempo. Use um dos formatos a seguir: hh:mm:ss, hh:mm[:ss[.uuuuuu]].',
					)
				},
			)
		})

		it('Validar PATCH de conferencia da guia sem informar guia', () => {
			var dados_teste = {
				guia: '',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.guia[0]).to.eq('Este campo não pode ser nulo.')
				},
			)
		})

		it('Validar PATCH de conferencia da guia com guia no formato inválido', () => {
			var dados_teste = {
				guia: 'sdfsdfsdfsdfsd',
				nome_motorista: 'Motorista Teste Automação PATCH',
				placa_veiculo: 'AAA1234',
				data_recebimento: data_atual.add(-1, 'day').format('YYYY-MM-DD'),
				hora_recebimento: '11:00:00',
				eh_reposicao: true,
			}
			var uuid = 'bece6929-2442-4255-97b6-6360ae03df9a'
			cy.alterar_conferencia_da_guia_patch(dados_teste, uuid).then(
				(response) => {
					expect(response.status).to.eq(400)
					expect(response.body.guia[0]).to.eq(
						'O valor “sdfsdfsdfsdfsd” não é um UUID válido',
					)
				},
			)
		})
	})
})
