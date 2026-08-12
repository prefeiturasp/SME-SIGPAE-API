/// <reference types='cypress' />

describe('Validar rota de dados de alunos EOL da aplicação SIGPAE', () => {
	const usuario = Cypress.env('usuario_coordenador_logistica')
	const senha = Cypress.env('senha')

	context('Rota api/dados-alunos-eol/{codigo_eol}/', () => {
		it('Validar GET de dados do aluno EOL com sucesso', () => {
			const codigoEol = '8310251'

			cy.consultar_dados_aluno_eol(codigoEol, usuario, senha).then(
				(response) => {
					expect(response.status, JSON.stringify(response.body)).to.eq(200)
					expect(response.body).to.have.property('detail')

					const aluno = response.body.detail
					expect(aluno).to.include.all.keys(
						'cd_aluno',
						'nm_aluno',
						'nm_social_aluno',
						'dt_nascimento_aluno',
						'cd_sexo_aluno',
						'nm_mae_aluno',
						'nm_pai_aluno',
						'cd_escola',
						'dc_turma_escola',
					)
					expect(aluno.cd_aluno).to.eq(codigoEol)
					expect(aluno.nm_aluno).to.be.a('string').and.not.be.empty
				},
			)
		})

		it('Validar GET com código EOL inexistente', () => {
			const codigoEolInexistente = '999999999'

			cy.consultar_dados_aluno_eol(
				codigoEolInexistente,
				usuario,
				senha,
			).then((response) => {
				expect(response.status, JSON.stringify(response.body)).to.eq(400)
				expect(response.body.detail).to.eq(
					'Aluno matching query does not exist.',
				)
			})
		})
	})
})
