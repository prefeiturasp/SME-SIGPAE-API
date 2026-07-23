/// <reference types='cypress' />

function normalizarEnum(valor) {
	return String(valor)
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
		.toUpperCase()
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

					const alimento = conferencia.conferencia_dos_alimentos.find(
						(itemAlimento) => itemAlimento.tem_ocorrencia,
					)
					const agora = new Date()
					const dados_teste = {
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
	})
})
