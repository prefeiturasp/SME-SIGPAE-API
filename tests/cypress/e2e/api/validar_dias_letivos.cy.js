/// <reference types='cypress' />

describe('Validar rota de Dias Letivos da aplicacao SIGPAE', () => {
	const senha = Cypress.env('senha')
	const parametros = {
		ano: 2025,
		mes: 11,
	}

	context('Rota api/dias-letivos/', () => {
		it('Validar GET de Dias Letivos com sucesso', () => {
			cy.consultar_dias_letivos({
				...parametros,
				usuario: Cypress.env('usuario_codae'),
				senha,
			}).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(200)
				expect(response.body).to.be.an('array')

				response.body.forEach((diaLetivo) => {
					expect(diaLetivo).to.have.all.keys(
						'uuid',
						'data',
						'lotes',
						'tipos_unidade_escolar',
						'periodos_escolares',
						'unidades_escolares',
						'editais_numeros',
					)
					expect(diaLetivo.uuid).to.be.a('string').and.not.be.empty
					expect(diaLetivo.data).to.match(/^\d{4}-\d{2}-\d{2}$/)
					expect(diaLetivo.lotes).to.be.an('array')
					expect(diaLetivo.tipos_unidade_escolar).to.be.an('array')
					expect(diaLetivo.periodos_escolares).to.be.an('array')
					expect(diaLetivo.unidades_escolares).to.be.a('string')
					expect(diaLetivo.editais_numeros).to.be.a('string')
				})
			})
		})

		it('Validar GET de Dias Letivos sem permissao', () => {
			cy.consultar_dias_letivos({
				...parametros,
				usuario: Cypress.env('usuario_diretor_ue'),
				senha,
			}).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(403)
				expect(response.body).to.deep.eq({
					detail: 'Você não tem permissão para executar essa ação.',
				})
			})
		})
	})
})
