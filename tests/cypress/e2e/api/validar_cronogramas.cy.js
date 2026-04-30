/// <reference types='cypress' />

describe('Validar rotas de dashboard de produtos da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_dilog_cronograma')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	function validarPermissaoNegada(response) {
		expect(response.status).to.eq(403)
		expect(response.body).to.have.property('detail')
	}

	context('Casos de teste para a rota api/cronogramas/', () => {
		it('Validar GET de cronogramas com sucesso', () => {
			var parametros = ''
			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Status RASCUNHO com sucesso', () => {
			var parametros = 'status=RASCUNHO'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Rascunho')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida')
				expect(primeiroResultado).to.have.property('armazem')
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')

				expect(primeiroResultado.etapas[0]).to.have.property('parte')

				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes')
			})
		})

		it('Validar GET de cronogramas com parâmetro Status ASSINADO_E_ENVIADO_AO_FORNECEDOR com sucesso', () => {
			var parametros = 'status=ASSINADO_E_ENVIADO_AO_FORNECEDOR'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Assinado e Enviado ao Fornecedor')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida').that
					.exist
				expect(primeiroResultado.unidade_medida).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property('nome')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'abreviacao',
				).that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'criado_em',
				).that.exist
				expect(primeiroResultado).to.have.property('armazem')
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica').that
					.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'numero',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'produto',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'uuid_empresa',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('marca')
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'volume_embalagem_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_volume_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				).that.exist
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Status ALTERACAO_CODAE com sucesso', () => {
			var parametros = 'status=ALTERACAO_CODAE'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Alteração CODAE')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida')
				expect(primeiroResultado).to.have.property('armazem').that.exist
				expect(primeiroResultado.armazem).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.armazem).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.armazem).to.have.property(
					'razao_social',
				).that.exist
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('data_programada').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('tipo_carga').that.exist
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes')
			})
		})

		it('Validar GET de cronogramas com parâmetro Status ASSINADO_CODAE com sucesso', () => {
			var parametros = 'status=ASSINADO_CODAE'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Assinado CODAE')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida')
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes')
			})
		})

		it('Validar GET de cronogramas com parâmetro Status ASSINADO_FORNECEDOR com sucesso', () => {
			var parametros = 'status=ASSINADO_FORNECEDOR'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Assinado Fornecedor')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida').that
					.exist
				expect(primeiroResultado.unidade_medida).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property('nome')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'abreviacao',
				).that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'criado_em',
				).that.exist
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property('numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('etapa',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('total_embalagens',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('qtd_total_empenho',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica').that
					.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'numero',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'produto',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'uuid_empresa',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('marca')
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'volume_embalagem_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_volume_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_primaria',
				)
				
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_secundaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				).that.exist
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
				expect(primeiroResultado).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'qtd_total_empenho',
				).that.exist
				expect(primeiroResultado).to.have.property(
					'ponto_a_ponto',
				).that.exist
				
			})
		})

		it('Validar GET de cronogramas com parâmetro Status SOLICITADO_ALTERACAO com sucesso', () => {
			var parametros = 'status=SOLICITADO_ALTERACAO'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Solicitado Alteração')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida')
				expect(primeiroResultado).to.have.property('armazem').that.exist
				expect(primeiroResultado.armazem).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.armazem).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.armazem).to.have.property(
					'razao_social',
				).that.exist
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('data_programada').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('tipo_carga').that.exist
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Status ASSINADO_DILOG_ABASTECIMENTO com sucesso', () => {
			var parametros = 'status=ASSINADO_DILOG_ABASTECIMENTO'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado)
					.to.have.property('status')
					.to.eq('Assinado Abastecimento')
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('data_programada').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('tipo_carga').that.exist
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				
				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				)
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Nome Empresa com sucesso', () => {
			var parametros = 'nome_empresa=JP%20Alimentos'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa)
					.to.have.property('nome_fantasia')
					.to.eq('JP Alimentos')
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(primeiroResultado).to.have.property('ficha_tecnica')
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Nome Empresa inválido', () => {
			var parametros = 'nome_empresa=testes testes'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count').to.eq(0)
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(response.body.results).to.be.empty
			})
		})

		it('Validar GET de cronogramas com parâmetro Nome Produto com sucesso', () => {
			var parametros = 'nome_produto=ARROZ%20TIPO%20I'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa)
					.to.have.property('nome_fantasia')
					
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida').that
					.exist
				expect(primeiroResultado.unidade_medida).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'abreviacao',
				).that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'criado_em',
				).that.exist
				expect(primeiroResultado).to.have.property('armazem').that.exist
				expect(primeiroResultado.armazem).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.armazem).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.armazem).to.have.property(
					'razao_social',
				).that.exist
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('data_programada').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('tipo_carga').that.exist
				expect(primeiroResultado).to.have.property('ficha_tecnica').that
					.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'numero',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'produto',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'uuid_empresa',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('marca')
					.that.exist
				expect(primeiroResultado.ficha_tecnica.marca).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.marca).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'volume_embalagem_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_volume_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_primaria',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_primaria',
				).that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('abreviacao').that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_secundaria',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_secundaria',
				).that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('abreviacao').that.exist

				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				).that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('abreviacao').that.exist
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				).that.exist
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Nome Produto inválido', () => {
			var parametros = 'nome_produto=testes-testes'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count').to.eq(0)
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(response.body.results).to.be.empty
			})
		})

		it('Validar GET de cronogramas com parâmetro Número com sucesso', () => {
			var parametros = 'numero=172%2F2024A'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado)
					.to.have.property('numero')
					.to.eq('172/2024A')
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('criado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('alterado_em').that
					.exist.and.is.not.empty
				expect(primeiroResultado).to.have.property('empresa').that.exist
				expect(primeiroResultado.empresa).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.empresa)
					.to.have.property('nome_fantasia')
					.to.eq('JP Alimentos')
				expect(primeiroResultado.empresa).to.have.property(
					'razao_social',
				).that.exist

				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('unidade_medida').that
					.exist
				expect(primeiroResultado.unidade_medida).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property('nome')
					.that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'abreviacao',
				).that.exist
				expect(primeiroResultado.unidade_medida).to.have.property(
					'criado_em',
				).that.exist
				expect(primeiroResultado).to.have.property('armazem').that.exist
				expect(primeiroResultado.armazem).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.armazem).to.have.property(
					'nome_fantasia',
				).that.exist
				expect(primeiroResultado.armazem).to.have.property(
					'razao_social',
				).that.exist
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
					.that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				).that.exist
				expect(primeiroResultado)
					.to.have.property('programacoes_de_recebimento')
					.to.be.an('array')
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('data_programada').that.exist
				expect(
					primeiroResultado.programacoes_de_recebimento[0],
				).to.have.property('tipo_carga').that.exist
				expect(primeiroResultado).to.have.property('ficha_tecnica').that
					.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('uuid')
					.that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'numero',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'produto',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.produto).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'uuid_empresa',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property('marca')
					.that.exist
				expect(primeiroResultado.ficha_tecnica.marca).to.have.property(
					'uuid',
				).that.exist
				expect(primeiroResultado.ficha_tecnica.marca).to.have.property(
					'nome',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'volume_embalagem_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_volume_primaria',
				)
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_primaria',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_primaria',
				).that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_primaria,
				).to.have.property('abreviacao').that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'peso_liquido_embalagem_secundaria',
				).that.exist
				expect(primeiroResultado.ficha_tecnica).to.have.property(
					'unidade_medida_secundaria',
				).that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.ficha_tecnica.unidade_medida_secundaria,
				).to.have.property('abreviacao').that.exist

				expect(primeiroResultado).to.have.property(
					'tipo_embalagem_secundaria',
				).that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('uuid').that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('nome').that.exist
				expect(
					primeiroResultado.tipo_embalagem_secundaria,
				).to.have.property('abreviacao').that.exist
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				).that.exist
				expect(primeiroResultado).to.have.property('observacoes').that
					.exist
			})
		})

		it('Validar GET de cronogramas com parâmetro Número inválido', () => {
			var parametros = 'numero=testeteste'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count').to.eq(0)
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(response.body.results).to.be.empty
			})
		})

		it('Validar GET de cronogramas com parâmetro UUID com sucesso', () => {
			cy.validar_cronogramas('').then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultadoLista = response.body.results[0]
				if (!primeiroResultadoLista) {
					return
				}
				var uuid = primeiroResultadoLista.uuid
				var parametros = 'uuid=' + uuid
				var empresa = primeiroResultadoLista.empresa.nome_fantasia

				cy.validar_cronogramas(parametros).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}
					expect(response.body).to.have.property('count')
					expect(response.body).to.have.property('next')
					expect(response.body).to.have.property('previous')
					expect(response.body).to.have.property('results')
					expect(response.body.results).to.be.an('array')
					const primeiroResultado = response.body.results[0]
					if (!primeiroResultado) {
						return
					}
					expect(primeiroResultado).to.have.property('uuid').to.eq(uuid)
					expect(primeiroResultado).to.have.property('numero').that.exist
					expect(primeiroResultado).to.have.property('status').that.exist
						.and.is.not.empty
					expect(primeiroResultado).to.have.property('criado_em').that
						.exist.and.is.not.empty
					expect(primeiroResultado).to.have.property('alterado_em').that
						.exist.and.is.not.empty
					expect(primeiroResultado).to.have.property('empresa').that
						.exist
					expect(primeiroResultado.empresa).to.have.property('uuid').that
						.exist
					expect(primeiroResultado.empresa)
						.to.have.property('nome_fantasia')
						.to.eq(empresa)
					expect(primeiroResultado.empresa).to.have.property(
						'razao_social',
					).that.exist

					expect(primeiroResultado).to.have.property(
						'qtd_total_programada',
					)
					expect(primeiroResultado).to.have.property('etapas').that.exist
					expect(primeiroResultado.etapas).to.be.an('array')
					expect(primeiroResultado.etapas[0]).to.have.property('uuid')
						.that.exist
					expect(primeiroResultado.etapas[0]).to.have.property(
						'numero_empenho',
					).that.exist
					expect(primeiroResultado.etapas[0]).to.have.property(
						'qtd_total_empenho',
					)
					expect(primeiroResultado.etapas[0]).to.have.property('etapa')
					expect(primeiroResultado.etapas[0]).to.have.property('parte')
					expect(primeiroResultado.etapas[0]).to.have.property(
						'data_programada',
					)
					expect(primeiroResultado.etapas[0]).to.have.property(
						'quantidade',
					)
					expect(primeiroResultado.etapas[0]).to.have.property(
						'total_embalagens',
					)
					expect(primeiroResultado)
						.to.have.property('programacoes_de_recebimento')
						.to.be.an('array')
					expect(primeiroResultado).to.have.property('ficha_tecnica')
					expect(primeiroResultado).to.have.property(
						'custo_unitario_produto',
					)
					expect(primeiroResultado).to.have.property('observacoes').that
						.exist
				})
			})
		})

		it('Validar GET de cronogramas com parâmetro UUID inválido', () => {
			var parametros = 'uuid=53886ad8-cb8b-4175-853e-deaaaaaaaaaa'

			cy.validar_cronogramas(parametros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count').to.eq(0)
				expect(response.body).to.have.property('next').null
				expect(response.body).to.have.property('previous').null
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(response.body.results).to.be.empty
			})
		})

		it('Validar GET de cronogramas com UUID com sucesso', () => {
			cy.validar_cronogramas('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				if (!primeiroResultadoLista) {
					return
				}
				var uuid = primeiroResultadoLista.uuid
				var empresa = primeiroResultadoLista.empresa.nome_fantasia

				cy.validar_cronogramas_por_uuid(uuid).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}
					expect(response.body).to.have.property('uuid').to.eq(uuid)
					expect(response.body).to.have.property('numero').that.exist
					expect(response.body).to.have.property('status').that.exist.and.is.not
						.empty
					expect(response.body).to.have.property('criado_em').that.exist.and.is
						.not.empty
					expect(response.body).to.have.property('alterado_em').that.exist.and
						.is.not.empty
					expect(response.body).to.have.property('empresa').that.exist
					expect(response.body.empresa).to.have.property('uuid').that.exist
					expect(response.body.empresa)
						.to.have.property('nome_fantasia')
						.to.eq(empresa)
					expect(response.body.empresa).to.have.property('razao_social').that
						.exist

					expect(response.body).to.have.property('qtd_total_programada')
					expect(response.body).to.have.property('etapas').that.exist
					expect(response.body.etapas).to.be.an('array')
					expect(response.body.etapas[0]).to.have.property('uuid').that.exist
					expect(response.body.etapas[0]).to.have.property('numero_empenho')
						.that.exist
					expect(response.body.etapas[0]).to.have.property('qtd_total_empenho')
					expect(response.body.etapas[0]).to.have.property('etapa')
					expect(response.body.etapas[0]).to.have.property('parte')
					expect(response.body.etapas[0]).to.have.property('data_programada')
					expect(response.body.etapas[0]).to.have.property('quantidade')
					expect(response.body.etapas[0]).to.have.property('total_embalagens')
					expect(response.body)
						.to.have.property('programacoes_de_recebimento')
						.to.be.an('array')
					expect(response.body).to.have.property('ficha_tecnica')
					expect(response.body).to.have.property('custo_unitario_produto')
					expect(response.body).to.have.property('observacoes').that.exist
				})
			})
		})

		it('Validar GET de cronogramas com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'

			cy.validar_cronogramas_por_uuid(uuid).then((response) => {
				expect([403, 404]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar GET de dados cronogramas ficha de recebimento com sucesso', () => {
			cy.validar_cronogramas('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				if (!primeiroResultadoLista) {
					return
				}
				var uuid = primeiroResultadoLista.uuid

				cy.validar_dados_cronograma_ficha_recebimento(uuid).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}
					expect(response.body.results).to.have.property('uuid').to.eq(uuid)
					expect(response.body.results).to.have.property('fornecedor').that
						.exist
					expect(response.body.results).property('contrato').that.exist.and.is
						.not.empty
					expect(response.body.results).property('pregao_chamada_publica').that
						.exist
					expect(response.body.results).property('ata').that.exist
					expect(response.body.results).to.have.property('produto')
					expect(response.body.results).to.have.property('marca')
					expect(response.body.results).to.have.property('qtd_total_programada')
					expect(response.body.results).to.have.property(
						'peso_liquido_embalagem_primaria',
					)
					expect(response.body.results).to.have.property(
						'peso_liquido_embalagem_secundaria',
					)
					expect(response.body.results).to.have.property('embalagem_primaria')
					expect(response.body.results).to.have.property('embalagem_secundaria')
					expect(response.body.results).to.have.property('categoria')
					expect(response.body.results).to.have.property('etapas').that.exist
					expect(response.body.results.etapas).to.be.an('array')
					expect(response.body.results.etapas[0]).to.have.property('uuid').that
						.exist
					expect(response.body.results.etapas[0]).to.have.property(
						'numero_empenho',
					).that.exist
					expect(response.body.results.etapas[0]).to.have.property(
						'qtd_total_empenho',
					)
					expect(response.body.results.etapas[0]).to.have.property('etapa')
					expect(response.body.results.etapas[0]).to.have.property('parte')
					expect(response.body.results.etapas[0]).to.have.property(
						'data_programada',
					)
					expect(response.body.results.etapas[0]).to.have.property('quantidade')
					expect(response.body.results.etapas[0]).to.have.property(
						'total_embalagens',
					)
					expect(response.body.results)
						.to.have.property('documentos_de_recebimento')
						.to.be.an('array')
					expect(response.body.results).to.have.property(
						'sistema_vedacao_embalagem_secundaria',
					)
				})
			})
		})

		it('Validar GET de dados cronogramas ficha de recebimento com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'

			cy.validar_dados_cronograma_ficha_recebimento(uuid).then((response) => {
				expect([403, 404]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar GET de detalhar com log com sucesso', () => {
			cy.validar_cronogramas('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				if (!primeiroResultadoLista) {
					return
				}
				var uuid = primeiroResultadoLista.uuid
				var empresa = primeiroResultadoLista.empresa.nome_fantasia

				cy.validar_detalhar_com_log(uuid).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}
					expect(response.body).to.have.property('uuid').to.eq(uuid)
					expect(response.body).to.have.property('numero').that.exist
					expect(response.body).to.have.property('status').that.exist.and.is.not
						.empty
					expect(response.body).to.have.property('criado_em').that.exist.and.is
						.not.empty
					expect(response.body).to.have.property('alterado_em').that.exist.and
						.is.not.empty
					expect(response.body).to.have.property('empresa').that.exist
					expect(response.body.empresa).to.have.property('uuid').that.exist
					expect(response.body.empresa)
						.to.have.property('nome_fantasia')
						.to.eq(empresa)
					expect(response.body.empresa).to.have.property('razao_social').that
						.exist
					expect(response.body).to.have.property('qtd_total_programada')
					expect(response.body).to.have.property('etapas').that.exist
					expect(response.body.etapas).to.be.an('array')
					expect(response.body.etapas[0]).to.have.property('uuid').that.exist
					expect(response.body.etapas[0]).to.have.property('numero_empenho')
						.that.exist
					expect(response.body.etapas[0]).to.have.property('qtd_total_empenho')
					expect(response.body.etapas[0]).to.have.property('etapa')
					expect(response.body.etapas[0]).to.have.property('parte')
					expect(response.body.etapas[0]).to.have.property('data_programada')
					expect(response.body.etapas[0]).to.have.property('quantidade')
					expect(response.body.etapas[0]).to.have.property('total_embalagens')
					expect(response.body)
						.to.have.property('programacoes_de_recebimento')
						.to.be.an('array')
					expect(response.body).to.have.property('ficha_tecnica')
					expect(response.body).to.have.property('custo_unitario_produto')
					expect(response.body).to.have.property('observacoes').that.exist
				})
			})
		})

		it('Validar GET de detalhar com log com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'

			cy.validar_detalhar_com_log(uuid).then((response) => {
				expect([403, 404]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})

		it('Validar GET da dashboard de cronogramas com sucesso', () => {
			cy.validar_dashboard().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado)
					.to.have.property('status')
					.to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
				expect(primeiroResultado)
					.to.have.property('dados')
					.to.be.an('array')
				expect(primeiroResultado.dados[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.dados[0]).to.have.property('numero')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('status')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('empresa')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('produto')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property(
					'log_mais_recente',
				).that.exist
				const segundoResultado = response.body.results[1]
				const terceiroResultado = response.body.results[2]
				const quartoResultado = response.body.results[3]
				if (segundoResultado) {
					expect(segundoResultado).to.have.property('status').to.be.eq('ASSINADO_FORNECEDOR')
					expect(segundoResultado).to.have.property('dados').to.be.an('array')
				}
				if (terceiroResultado) {
					expect(terceiroResultado).to.have.property('status').to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
					expect(terceiroResultado).to.have.property('dados').to.be.an('array')
				}
				if (quartoResultado) {
					expect(quartoResultado).to.have.property('status').to.be.eq('ASSINADO_CODAE')
					expect(quartoResultado).to.have.property('dados').to.be.an('array')
				}
			})
		})

		it('Validar GET da dashboard com filtros vazios com sucesso', () => {
			var filtros = '?numero_cronograma=&nome_produto='

			cy.validar_dashboard_com_filtro(filtros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado)
					.to.have.property('status')
					.to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
				expect(primeiroResultado)
					.to.have.property('dados')
					.to.be.an('array')
				expect(primeiroResultado.dados[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.dados[0]).to.have.property('numero')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('status')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('empresa')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property('produto')
					.that.exist
				expect(primeiroResultado.dados[0]).to.have.property(
					'log_mais_recente',
				).that.exist
				const segundoResultado = response.body.results[1]
				const terceiroResultado = response.body.results[2]
				const quartoResultado = response.body.results[3]
				if (segundoResultado) {
					expect(segundoResultado).to.have.property('status').to.be.eq('ASSINADO_FORNECEDOR')
					expect(segundoResultado).to.have.property('dados').to.be.an('array')
				}
				if (terceiroResultado) {
					expect(terceiroResultado).to.have.property('status').to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
					expect(terceiroResultado).to.have.property('dados').to.be.an('array')
				}
				if (quartoResultado) {
					expect(quartoResultado).to.have.property('status').to.be.eq('ASSINADO_CODAE')
					expect(quartoResultado).to.have.property('dados').to.be.an('array')
				}
			})
		})

		it('Validar GET da dashboard com filtros preenchidos com sucesso', () => {
			cy.validar_dashboard_com_filtro('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				const primeiroDadoLista = primeiroResultadoLista?.dados?.[0]
				if (!primeiroDadoLista) {
					return
				}
				var numeroCronograma = primeiroDadoLista.numero
				var nomeProduto = primeiroDadoLista.produto

				var filtros =
					'?numero_cronograma=' +
					numeroCronograma +
					'&nome_produto=' +
					nomeProduto

				cy.validar_dashboard_com_filtro(filtros).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}

					const dados0 = response.body.results[0]?.dados || []
					const dados1 = response.body.results[1]?.dados || []
					const dados2 = response.body.results[2]?.dados || []
					const dados3 = response.body.results[3]?.dados || []

					if (dados0.length > 0) {
						expect(dados0[0]).to.have.property('numero').to.eq(numeroCronograma)
						expect(dados0[0]).to.have.property('produto').to.eq(nomeProduto)
					} else if (dados1.length > 0) {
						expect(dados1[0]).to.have.property('numero').to.eq(numeroCronograma)
						expect(dados1[0]).to.have.property('produto').to.eq(nomeProduto)
					} else if (dados2.length > 0) {
						expect(dados2[0]).to.have.property('numero').to.eq(numeroCronograma)
						expect(dados2[0]).to.have.property('produto').to.eq(nomeProduto)
					} else if (dados3.length > 0) {
						expect(dados3[0]).to.have.property('numero').to.eq(numeroCronograma)
						expect(dados3[0]).to.have.property('produto').to.eq(nomeProduto)
					}

					if (response.body.results[0]) {
						expect(response.body.results[0]).to.have.property('status').to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
					}
					if (response.body.results[1]) {
						expect(response.body.results[1]).to.have.property('status').to.be.eq('ASSINADO_FORNECEDOR')
					}
					if (response.body.results[2]) {
						expect(response.body.results[2]).to.have.property('status').to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
					}
					if (response.body.results[3]) {
						expect(response.body.results[3]).to.have.property('status').to.be.eq('ASSINADO_CODAE')
					}
				})
			})
		})

		it('Validar GET da dashboard com filtro nome do produto com sucesso', () => {
			cy.validar_dashboard_com_filtro('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				const primeiroDadoLista = primeiroResultadoLista?.dados?.[0]
				if (!primeiroDadoLista) {
					return
				}
				var nomeProduto = primeiroDadoLista.produto

				var filtros = '?numero_cronograma=&nome_produto=' + nomeProduto

				cy.validar_dashboard_com_filtro(filtros).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}
					const primeiroResultado = response.body.results[0]
					if (!primeiroResultado) {
						return
					}
					expect(primeiroResultado)
						.to.have.property('status')
						.to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
					expect(primeiroResultado)
						.to.have.property('dados')
						.to.be.an('array')
					expect(primeiroResultado.dados[0]).to.have.property('uuid')
						.that.exist
					expect(primeiroResultado.dados[0]).to.have.property('numero')
						.that.exist
					expect(primeiroResultado.dados[0]).to.have.property('status')
						.that.exist
					expect(primeiroResultado.dados[0]).to.have.property('empresa')
						.that.exist
					expect(primeiroResultado.dados[0]).to.have.property('produto')
						.that.exist
					expect(primeiroResultado.dados[0]).to.have.property(
						'log_mais_recente',
					).that.exist
					expect(response.body.results[1])
						.to.have.property('status')
						.to.be.eq('ASSINADO_FORNECEDOR')
					expect(response.body.results[1])
						.to.have.property('dados')
						.to.be.an('array')
					expect(response.body.results[2])
						.to.have.property('status')
						.to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
					expect(response.body.results[2])
						.to.have.property('dados')
						.to.be.an('array')
					expect(response.body.results[3])
						.to.have.property('status')
						.to.be.eq('ASSINADO_CODAE')
					expect(response.body.results[3])
						.to.have.property('dados')
						.to.be.an('array')
				})
			})
		})

		it('Validar GET da dashboard com filtro nome do produto não existente', () => {
			var filtros = '?numero_cronograma=&nome_produto=sadasdasda'

			cy.validar_dashboard_com_filtro(filtros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				const dados0 = primeiroResultado?.dados || []
				const dados1 = response.body.results[1]?.dados || []
				const dados2 = response.body.results[2]?.dados || []
				const dados3 = response.body.results[3]?.dados || []

				expect(primeiroResultado)
					.to.have.property('status')
					.to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
				expect(expect(dados0.length).to.eq(0))

				expect(response.body.results[1])
					.to.have.property('status')
					.to.be.eq('ASSINADO_FORNECEDOR')
				expect(expect(dados1.length).to.eq(0))

				expect(response.body.results[2])
					.to.have.property('status')
					.to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
				expect(expect(dados2.length).to.eq(0))

				expect(response.body.results[3])
					.to.have.property('status')
					.to.be.eq('ASSINADO_CODAE')
				expect(expect(dados3.length).to.eq(0))
			})
		})

		it('Validar GET da dashboard com filtro numero do cronograma com sucesso', () => {
			cy.validar_dashboard_com_filtro('').then((responseList) => {
				expect([200, 403]).to.include(responseList.status)
				if (responseList.status === 403) {
					validarPermissaoNegada(responseList)
					return
				}
				expect(responseList.body).to.have.property('results')
				expect(responseList.body.results).to.be.an('array')
				const primeiroResultadoLista = responseList.body.results[0]
				const primeiroDadoLista = primeiroResultadoLista?.dados?.[0]
				if (!primeiroDadoLista) {
					return
				}
				var numeroCronograma = primeiroDadoLista.numero

				var filtros =
					'?numero_cronograma=' + numeroCronograma + '&nome_produto='

				cy.validar_dashboard_com_filtro(filtros).then((response) => {
					expect([200, 403]).to.include(response.status)
					if (response.status === 403) {
						validarPermissaoNegada(response)
						return
					}

					const dados0 = response.body.results[0]?.dados || []
					const dados1 = response.body.results[1]?.dados || []
					const dados2 = response.body.results[2]?.dados || []
					const dados3 = response.body.results[3]?.dados || []

					if (dados0.length > 0) {
						expect(dados0[0]).to.have.property('numero').to.eq(numeroCronograma)
					} else if (dados1.length > 0) {
						expect(dados1[0]).to.have.property('numero').to.eq(numeroCronograma)
					} else if (dados2.length > 0) {
						expect(dados2[0]).to.have.property('numero').to.eq(numeroCronograma)
					} else if (dados3.length > 0) {
						expect(dados3[0]).to.have.property('numero').to.eq(numeroCronograma)
					}

					if (response.body.results[0]) {
						expect(response.body.results[0]).to.have.property('status').to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
					}
					if (response.body.results[1]) {
						expect(response.body.results[1]).to.have.property('status').to.be.eq('ASSINADO_FORNECEDOR')
					}
					if (response.body.results[2]) {
						expect(response.body.results[2]).to.have.property('status').to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
					}
					if (response.body.results[3]) {
						expect(response.body.results[3]).to.have.property('status').to.be.eq('ASSINADO_CODAE')
					}
				})
			})
		})

		it('Validar GET da dashboard com filtro numero do cronograma não existente', () => {
			var filtros = '?numero_cronograma=1234567890&nome_produto='
			cy.validar_dashboard_com_filtro(filtros).then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}

				const dados0 = primeiroResultado?.dados || []
				const dados1 = response.body.results[1]?.dados || []
				const dados2 = response.body.results[2]?.dados || []
				const dados3 = response.body.results[3]?.dados || []

				expect(primeiroResultado)
					.to.have.property('status')
					.to.be.eq('ASSINADO_E_ENVIADO_AO_FORNECEDOR')
				expect(expect(dados0.length).to.eq(0))

				expect(response.body.results[1])
					.to.have.property('status')
					.to.be.eq('ASSINADO_FORNECEDOR')
				expect(expect(dados1.length).to.eq(0))

				expect(response.body.results[2])
					.to.have.property('status')
					.to.be.eq('ASSINADO_DILOG_ABASTECIMENTO')
				expect(expect(dados2.length).to.eq(0))

				expect(response.body.results[3])
					.to.have.property('status')
					.to.be.eq('ASSINADO_CODAE')
				expect(expect(dados3.length).to.eq(0))
			})
		})

		it('Validar GET de lista cronogramas ficha recebimento com sucesso', () => {
			cy.validar_lista_cronogramas_ficha_recebimento().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist
				expect(primeiroResultado).to.have.property('numero').that.exist
				expect(primeiroResultado).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado).to.have.property('nome_produto').that
					.exist
			})
		})

		it('Validar GET de lista cronogramas cadastro com sucesso', () => {
			cy.validar_lista_cronogramas_cadastro().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist
				expect(primeiroResultado).to.have.property('numero').that.exist
				expect(primeiroResultado).to.have.property(
					'pregao_chamada_publica',
				).that.exist
				expect(primeiroResultado).to.have.property('nome_produto')
			})
		})

		it('Validar GET de listagem de relatório com sucesso', () => {
			cy.validar_listagem_relatorio().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.have.property('count')
				expect(response.body).to.have.property('next')
				expect(response.body).to.have.property('previous')
				expect(response.body).to.have.property('results')
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				expect(primeiroResultado).to.have.property('uuid').that.exist.and
					.is.not.empty
				expect(primeiroResultado).to.have.property('numero').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('produto')
				expect(primeiroResultado).to.have.property('empresa').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property(
					'qtd_total_programada',
				)
				expect(primeiroResultado).to.have.property('status').that.exist
					.and.is.not.empty
				expect(primeiroResultado).to.have.property('marca')
				expect(primeiroResultado).to.have.property(
					'custo_unitario_produto',
				)
				expect(primeiroResultado).to.have.property('etapas').that.exist
				expect(primeiroResultado.etapas).to.be.an('array')
				expect(primeiroResultado.etapas[0]).to.have.property('uuid').that
					.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'numero_empenho',
				).that.exist
				expect(primeiroResultado.etapas[0]).to.have.property(
					'qtd_total_empenho',
				)
				expect(primeiroResultado.etapas[0]).to.have.property('etapa')
				expect(primeiroResultado.etapas[0]).to.have.property('parte')
				expect(primeiroResultado.etapas[0]).to.have.property(
					'data_programada',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'quantidade',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'total_embalagens',
				)
				expect(primeiroResultado.etapas[0]).to.have.property(
					'desvinculada_recebimento',
				)
				expect(response.body).to.have.property('totalizadores').that.exist
				expect(response.body.totalizadores).to.have.property(
					'Assinado e Enviado ao Fornecedor',
				).that.exist
				expect(response.body.totalizadores).to.have.property(
					'Solicitado Alteração',
				).that.exist
				expect(response.body.totalizadores).to.have.property('Assinado CODAE')
					.that.exist
				expect(response.body.totalizadores).to.have.property('Alteração CODAE')
					.that.exist
				expect(response.body.totalizadores).to.have.property(
					'Assinado Abastecimento',
				).that.exist
				expect(response.body.totalizadores).to.have.property(
					'Assinado Fornecedor',
				).that.exist
				expect(response.body.totalizadores).to.have.property('Rascunho').that
					.exist
			})
		})

		it('Validar GET de opções etapas com sucesso', () => {
			cy.validar_opcoes_etapas().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body).to.be.an('array')
				expect(response.body[0]).to.have.property('uuid').that.exist
				expect(response.body[0]).to.have.property('value').that.exist
			})
		})

		it('Validar GET de rascunhos com sucesso', () => {
			cy.validar_rascunhos().then((response) => {
				expect([200, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body.results).to.be.an('array')
				const primeiroResultado = response.body.results[0]
				if (!primeiroResultado) {
					return
				}
				if (response.body.results.length > 0) {
					expect(primeiroResultado).to.have.property('uuid').that.exist
					expect(primeiroResultado).to.have.property('numero').that.exist
					expect(primeiroResultado).to.have.property('alterado_em').that
						.exist
				}
			})
		})

		it('Validar POST de cronograma com sucesso', () => {
			var dados_teste = {
				nome: 'Teste Automação Novo Produto Cadastrado',
				armazem: 'd020c118-f124-4fec-a136-4e3da9ba63d9',
				empresa: 'd0630b2b-8e45-472c-b9c6-90451b60b081',
				contrato: '387121e0-f887-4ecf-9521-00c519e9830d',
				unidade_medida: 'e274494c-78aa-42cf-8718-0e362c0f8ba5',
				qtd_total_programada: 10.0,
				etapas: [
					{
						numero_empenho: '123456',
						etapa: 1,
						parte: 'Parte 1',
						data_programada: '2025-10-26',
						quantidade: 10.0,
						total_embalagens: 1.0,
						qtd_total_empenho: 10.0,
						uuid: 'e972f048-a31b-4929-a337-d6b8057e60d9',
					},
				],
				programacoes_de_recebimento: [
					{
						data_programada: '26/06/2025 - Etapa 1  - Parte 1',
						tipo_carga: 'PALETIZADA',
						uuid: '0f25baf8-4ed4-4572-a9cb-5871e076ec6b',
					},
				],
				ficha_tecnica: '7a308949-4e9d-4e2a-abea-be9322fa955a',
				tipo_embalagem_secundaria: '05690384-2d95-4e21-8646-8a0f8f8e0673',
				custo_unitario_produto: 10.0,
				uuid: 'fa932382-cd4e-4a7e-baa4-7351abe9cdf4',
				observacoes: 'Teste Automação',
			}
			cy.cadastrar_cronogramas(dados_teste).then((response) => {
				expect([201, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body['observacoes']).to.eq('Teste Automação')
				var uuid = response.body['uuid']

				cy.deletar_cronograma(uuid).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de cronograma com sucesso', () => {
			var dados_teste = {
				nome: 'Teste Automação Novo Produto Cadastrado',
				armazem: 'd020c118-f124-4fec-a136-4e3da9ba63d9',
				empresa: 'd0630b2b-8e45-472c-b9c6-90451b60b081',
				contrato: '387121e0-f887-4ecf-9521-00c519e9830d',
				unidade_medida: 'e274494c-78aa-42cf-8718-0e362c0f8ba5',
				qtd_total_programada: 10.0,
				etapas: [
					{
						numero_empenho: '123456',
						etapa: 1,
						parte: 'Parte 1',
						data_programada: '2025-06-26',
						quantidade: 10.0,
						total_embalagens: 1.0,
						qtd_total_empenho: 10.0,
						uuid: 'e972f048-a31b-4929-a337-d6b8057e60d9',
					},
				],
				programacoes_de_recebimento: [
					{
						data_programada: '26/06/2025 - Etapa 1  - Parte 1',
						tipo_carga: 'PALETIZADA',
						uuid: '0f25baf8-4ed4-4572-a9cb-5871e076ec6b',
					},
				],
				ficha_tecnica: '7a308949-4e9d-4e2a-abea-be9322fa955a',
				tipo_embalagem_secundaria: '05690384-2d95-4e21-8646-8a0f8f8e0673',
				custo_unitario_produto: 10.0,
				uuid: 'fa932382-cd4e-4a7e-baa4-7351abe9cdf4',
				observacoes: 'Teste Automação - Deletar',
			}
			cy.cadastrar_cronogramas(dados_teste).then((response) => {
				expect([201, 403]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
					return
				}
				expect(response.body['observacoes']).to.eq('Teste Automação - Deletar')
				var uuid = response.body['uuid']

				cy.deletar_cronograma(uuid).then((responseDelete) => {
					expect(responseDelete.status).to.eq(204)
				})
			})
		})

		it('Validar DELETE de cronograma com UUID inválido', () => {
			var uuid = '53886ad8-cb8b-4175-853e-de087aaaaaaa'
			cy.deletar_cronograma(uuid).then((response) => {
				expect([403, 404]).to.include(response.status)
				if (response.status === 403) {
					validarPermissaoNegada(response)
				}
			})
		})
	})
})
