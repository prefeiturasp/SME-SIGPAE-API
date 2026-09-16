import { When, Then } from 'cypress-cucumber-preprocessor/steps'

When('consulto os dados do aluno pelo codigo EOL {string}', function (codigo) {
	cy.consultar_dados_aluno_eol(
		codigo,
		Cypress.env('usuario_coordenador_logistica'),
		Cypress.env('senha'),
	).then((response) => {
		this.response = response
	})
})

Then('a consulta do aluno EOL retorna status {int}', function (status) {
	expect(this.response.status, JSON.stringify(this.response.body)).to.eq(status)
})

Then('a resposta do aluno EOL corresponde ao codigo {string}', function (codigo) {
	if (this.response.status === 400) {
		expect(this.response.body.detail).to.eq('Aluno matching query does not exist.')
		return
	}
	const aluno = this.response.body.detail
	expect(aluno).to.include.all.keys(
		'cd_aluno', 'nm_aluno', 'nm_social_aluno', 'dt_nascimento_aluno',
		'cd_sexo_aluno', 'nm_mae_aluno', 'nm_pai_aluno', 'cd_escola', 'dc_turma_escola',
	)
	expect(aluno.cd_aluno).to.eq(codigo)
	expect(aluno.nm_aluno).to.be.a('string').and.not.be.empty
})
