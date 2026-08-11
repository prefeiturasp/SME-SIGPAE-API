/// <reference types='cypress' />

function normalizarEnum(valor) {
	return String(valor)
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toUpperCase()
}

function formatarDataParaApi(data) {
	const correspondencia = String(data).match(/^(\d{2})\/(\d{2})\/(\d{4})$/)

	if (!correspondencia) {
		return data
	}

	const [, dia, mes, ano] = correspondencia
	return `${ano}-${mes}-${dia}`
}

function montarDadosPatch(conferencia) {
	return {
		nome_motorista: conferencia.nome_motorista,
	}
}

function montarDadosPost(conferencia) {
	const alimento = conferencia.conferencia_dos_alimentos.find(
		(itemAlimento) => itemAlimento.tem_ocorrencia,
	)
	const agora = new Date()

	return {
		conferencia_dos_alimentos: [
			{
				conferencia: conferencia.uuid,
				tipo_embalagem: normalizarEnum(alimento.tipo_embalagem),
				nome_alimento: alimento.nome_alimento,
				qtd_recebido: alimento.qtd_recebido,
				status_alimento: normalizarEnum(alimento.status_alimento),
				ocorrencia: alimento.ocorrencia,
				observacao: 'Cadastro criado pelo teste automatizado',
				tem_ocorrencia: alimento.tem_ocorrencia,
			},
		],
		guia: conferencia.guia.uuid,
		nome_motorista: `Motorista teste ${agora.getTime()}`,
		placa_veiculo: 'TES1A23',
		data_recebimento: agora.toISOString().slice(0, 10),
		hora_recebimento: agora.toTimeString().slice(0, 8),
		eh_reposicao: false,
	}
}

describe('Validar conferência da guia com ocorrência da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_abastecimento')
	const senha = Cypress.env('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Rota GET api/conferencia-da-guia-com-ocorrencia/', () => {
		it('Valida a listagem paginada com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia().then((response) => {
				expect(response.status).to.eq(200)
				expect(response.body).to.include.all.keys(
					'count',
					'next',
					'previous',
					'results',
				)
				expect(response.body.count).to.be.a('number').and.to.be.greaterThan(0)
				expect(response.body.results).to.be.an('array').and.not.to.be.empty

				response.body.results.forEach((conferencia) => {
					expect(conferencia).to.have.property('criado_por').that.is.an('object')
					expect(conferencia.criado_por).to.include.all.keys(
						'uuid',
						'cpf',
						'nome',
						'email',
					)
					expect(conferencia)
						.to.have.property('conferencia_dos_alimentos')
						.that.is.an('array')
				})
			})
		})
	})

	context('Rota GET api/conferencia-da-guia-com-ocorrencia/{uuid}/', () => {
		it('Valida a consulta por UUID com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia('limit=1&offset=0').then(
				(responseLista) => {
					expect(responseLista.status).to.eq(200)
					expect(responseLista.body.results).to.be.an('array').and.not.to.be.empty

					const uuid = responseLista.body.results[0].uuid
					expect(uuid).to.be.a('string').and.not.to.be.empty

					cy.consultar_conferencia_da_guia_com_ocorrencia_por_uuid(uuid).then(
						(response) => {
							expect(response.status).to.eq(200)
							expect(response.body).to.include({ uuid })
							expect(response.body).to.include.all.keys(
								'criado_por',
								'conferencia_dos_alimentos',
								'guia',
								'data_recebimento',
								'hora_recebimento',
								'nome_motorista',
								'placa_veiculo',
								'eh_reposicao',
							)
							expect(response.body.conferencia_dos_alimentos).to.be.an('array')
						},
					)
				},
			)
		})

		it('Exibe erro ao consultar UUID inexistente', () => {
			const uuidInexistente = '00000000-0000-0000-0000-000000000000'

			cy.consultar_conferencia_da_guia_com_ocorrencia_por_uuid(
				uuidInexistente,
			).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota PUT api/conferencia-da-guia-com-ocorrencia/{uuid}/', () => {
		it('Atualiza conferência da guia com ocorrência por UUID com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia('limit=100&offset=0').then(
				(responseLista) => {
					expect(responseLista.status).to.eq(200)
					expect(responseLista.body.results).to.be.an('array').and.not.to.be.empty

					const conferencia = responseLista.body.results.find(
						(item) => item.guia.situacao === 'ATIVA',
					)
					expect(conferencia).to.exist

					const dados_teste = {
						conferencia_dos_alimentos:
							conferencia.conferencia_dos_alimentos.map((alimento) => ({
								conferencia: conferencia.uuid,
								tipo_embalagem: normalizarEnum(alimento.tipo_embalagem),
								nome_alimento: alimento.nome_alimento,
								qtd_recebido: alimento.qtd_recebido,
								status_alimento: normalizarEnum(alimento.status_alimento),
								ocorrencia: alimento.ocorrencia,
								observacao: alimento.observacao,
								tem_ocorrencia: alimento.tem_ocorrencia,
							})),
						guia: conferencia.guia.uuid,
						nome_motorista: conferencia.nome_motorista,
						placa_veiculo: conferencia.placa_veiculo,
						data_recebimento: formatarDataParaApi(
							conferencia.data_recebimento,
						),
						hora_recebimento: conferencia.hora_recebimento,
						eh_reposicao: conferencia.eh_reposicao,
					}

					cy.atualizar_conferencia_da_guia_com_ocorrencia(
						conferencia.uuid,
						dados_teste,
					).then((response) => {
						expect(response.status, JSON.stringify(response.body)).to.eq(200)
						expect(response.body).to.include({ uuid: conferencia.uuid })
					})
				},
			)
		})

		it('Exibe erro ao atualizar conferência vinculada a guia arquivada', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia('limit=100&offset=0').then(
				(responseLista) => {
					expect(responseLista.status).to.eq(200)

					const conferencia = responseLista.body.results.find(
						(item) => item.guia.situacao === 'ARQUIVADA',
					)
					expect(conferencia).to.exist

					const dados_teste = {
						conferencia_dos_alimentos:
							conferencia.conferencia_dos_alimentos.map((alimento) => ({
								conferencia: conferencia.uuid,
								tipo_embalagem: normalizarEnum(alimento.tipo_embalagem),
								nome_alimento: alimento.nome_alimento,
								qtd_recebido: alimento.qtd_recebido,
								status_alimento: normalizarEnum(alimento.status_alimento),
								ocorrencia: alimento.ocorrencia,
								observacao: alimento.observacao,
								tem_ocorrencia: alimento.tem_ocorrencia,
							})),
						guia: conferencia.guia.uuid,
						nome_motorista: conferencia.nome_motorista,
						placa_veiculo: conferencia.placa_veiculo,
						data_recebimento: formatarDataParaApi(
							conferencia.data_recebimento,
						),
						hora_recebimento: conferencia.hora_recebimento,
						eh_reposicao: conferencia.eh_reposicao,
					}

					cy.atualizar_conferencia_da_guia_com_ocorrencia(
						conferencia.uuid,
						dados_teste,
					).then((response) => {
						expect(response.status).to.eq(400)
						expect(JSON.stringify(response.body)).to.contain('guia arquivada')
					})
				},
			)
		})
	})

	context('Rota PATCH api/conferencia-da-guia-com-ocorrencia/{uuid}/', () => {
		it('Atualiza parcialmente conferência por UUID com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia('limit=100&offset=0').then(
				(responseLista) => {
					expect(responseLista.status).to.eq(200)

					const conferencia = responseLista.body.results.find(
						(item) => item.guia.situacao === 'ATIVA',
					)
					expect(conferencia).to.exist

					cy.atualizar_conferencia_da_guia_com_ocorrencia_patch(
						conferencia.uuid,
						montarDadosPatch(conferencia),
					).then((response) => {
						expect(response.status, JSON.stringify(response.body)).to.eq(200)
						expect(response.body).to.include({ uuid: conferencia.uuid })
					})
				},
			)
		})

		it('Exibe erro ao atualizar parcialmente UUID inexistente', () => {
			const uuidInexistente = '00000000-0000-0000-0000-000000000000'

			cy.atualizar_conferencia_da_guia_com_ocorrencia_patch(
				uuidInexistente,
				{ nome_motorista: 'Motorista inexistente' },
			).then((response) => {
				expect(response.status).to.eq(404)
			})
		})
	})

	context('Rota DELETE api/conferencia-da-guia-com-ocorrencia/{uuid}/', () => {
		it('Exibe erro ao excluir UUID inexistente', () => {
			const uuidInexistente = '00000000-0000-0000-0000-000000000000'

			cy.excluir_conferencia_da_guia_com_ocorrencia(uuidInexistente).then(
				(response) => {
					expect(response.status).to.eq(404)
				},
			)
		})
	})

	context('Rota POST api/conferencia-da-guia-com-ocorrencia/', () => {
		it('Cadastra conferência da guia com ocorrência com sucesso', () => {
			cy.consultar_conferencia_da_guia_com_ocorrencia('limit=10&offset=0').then(
				(responseLista) => {
					expect(responseLista.status).to.eq(200)
					expect(responseLista.body.results).to.be.an('array').and.not.to.be.empty

					const conferencia = responseLista.body.results.find((item) =>
						item.conferencia_dos_alimentos.some(
							(itemAlimento) => itemAlimento.tem_ocorrencia,
						),
					)
					expect(conferencia).to.exist
					const dados_teste = montarDadosPost(conferencia)

					cy.cadastrar_conferencia_da_guia_com_ocorrencia(dados_teste).then(
						(response) => {
							expect(response.status, JSON.stringify(response.body)).to.eq(201)
							expect(response.body).to.include({
								nome_motorista: dados_teste.nome_motorista,
								placa_veiculo: dados_teste.placa_veiculo,
								eh_reposicao: dados_teste.eh_reposicao,
							})
							expect(response.body.uuid).to.be.a('string').and.not.to.be.empty
						},
					)
				},
			)
		})

		it('Exibe erro ao cadastrar com dados inválidos', () => {
			cy.cadastrar_conferencia_da_guia_com_ocorrencia({
				conferencia_dos_alimentos: [],
				guia: 'uuid-invalido',
				nome_motorista: '',
				placa_veiculo: '',
				data_recebimento: '',
				hora_recebimento: '',
				eh_reposicao: false,
			}).then((response) => {
				expect(response.status).to.eq(400)
				expect(response.body).to.be.an('object').and.not.to.be.empty
			})
		})
	})
})
