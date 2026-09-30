import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function normalizar(texto) {
	return String(texto)
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '')
}

Given('que estou autenticado como diretor para consultar alunos', () => {
	cy.autenticar_login(
		Cypress.env('usuario_diretor_ue'),
		Cypress.env('senha'),
	)
})

When('consulto todos os alunos', function () {
	cy.validar_alunos('').then((response) => {
		this.response = response
	})
})

When('consulto o aluno de codigo EOL {int}', function (codigoEol) {
	cy.validar_alunos(`${codigoEol}/`).then((response) => {
		this.response = response
	})
})

When(
	'verifico se o aluno {int} pertence a escola {string}',
	function (codigoEol, escola) {
		cy.validar_alunos_e_escola_codigo_eol(codigoEol, escola).then(
			(response) => {
				this.response = response
			},
		)
	},
)

When(
	'consulto detalhes de dieta com escola {int} e nome {string}',
	function (escola, nome) {
		cy.validar_alunos_nao_matriculado_detalhes_dieta(
			`?codigo_eol_escola=${escola}&nome_aluno=${nome}`,
		).then((response) => {
			this.response = response
		})
	},
)

When('consulto detalhes de dieta sem parametros', function () {
	cy.validar_alunos_nao_matriculado_detalhes_dieta('').then((response) => {
		this.response = response
	})
})

When('consulto detalhes de dieta apenas com escola {int}', function (escola) {
	cy.validar_alunos_nao_matriculado_detalhes_dieta(
		`?codigo_eol_escola=${escola}`,
	).then((response) => {
		this.response = response
	})
})

When('consulto quantidade de alunos por periodo sem codigo da escola', function () {
	cy.validar_alunos_qtde_por_periodo_cei_emei('').then((response) => {
		this.response = response
	})
})

When(
	'consulto quantidade de alunos por periodo da escola {string}',
	function (escola) {
		cy.validar_alunos_qtde_por_periodo_cei_emei(
			`?codigo_eol_escola=${escola}`,
		).then((response) => {
			this.response = response
		})
	},
)

When(
	'consulto quantidade CEMEI por CEI e EMEI da escola {string}',
	function (escola) {
		cy.validar_alunos_qtde_cemei_cei_emei(
			`?codigo_eol_escola=${escola}`,
		).then((response) => {
			this.response = response
		})
	},
)

When(
	'consulto quantidade CEMEI por CEI e EMEI sem codigo da escola',
	function () {
		cy.validar_alunos_qtde_cemei_cei_emei('').then((response) => {
			this.response = response
		})
	},
)

Then('deve retornar uma lista paginada de alunos', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.have.property('count').that.exist
	expect(this.response.body).to.have.property('next')
	expect(this.response.body).to.have.property('previous')
	expect(this.response.body).to.have.property('results').that.is.an('array').and.not
		.to.be.empty
	const aluno = this.response.body.results[0]
	expect(aluno).to.have.property('uuid').that.exist
	expect(aluno).to.have.property('nome').that.exist
	expect(aluno).to.have.property('data_nascimento').that.exist
	expect(aluno).to.have.property('codigo_eol').that.exist
	expect(aluno).to.have.property('escola')
})

Then('deve retornar os dados do aluno com status 200', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.exist
	expect(this.response.body).to.have.property('uuid').that.exist
	expect(this.response.body).to.have.property('nome').that.exist
	expect(this.response.body).to.have.property('data_nascimento').that.exist
	expect(this.response.body).to.have.property('codigo_eol').that.exist
})

Then('a consulta do aluno deve retornar status 404', function () {
	expect(this.response.status).to.eq(404)
	expect(this.response.body).to.exist
})

Then('o resultado de pertencimento deve ser {string}', function (resultado) {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.exist
	expect(this.response.body)
		.to.have.property('pertence_a_escola')
		.that.equals(resultado === 'true')
})

Then('a consulta de detalhes de dieta deve retornar status 200', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.exist
})

Then('deve informar que codigo_eol_escola e obrigatorio', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.exist
	expect(normalizar(this.response.body)).to.contain(
		'`codigo_eol_escola` como query_param e obrigatorio',
	)
})

Then('deve informar que nome_aluno e obrigatorio', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.exist
	expect(normalizar(this.response.body)).to.contain(
		'`nome_aluno` como query_param e obrigatorio',
	)
})

Then('deve informar que a escola nao e CEMEI', function () {
	expect(this.response.status).to.eq(400)
	expect(this.response.body).to.exist
	expect(normalizar(this.response.body)).to.contain('escola nao e CEMEI')
})

Then('deve retornar quantidades CEI e EMEI por periodo', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.exist
	this.response.body.forEach((item) => {
		expect(item).to.have.property('CEI').that.exist
		expect(item).to.have.property('EMEI').that.exist
		expect(item).to.have.property('nome').that.exist
	})
})

Then('deve retornar quantidades CEMEI para CEI e EMEI', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body).to.exist
	this.response.body.forEach((item) => {
		expect(item).to.have.property('CEI').that.exist
		expect(item).to.have.property('EMEI').that.exist
	})
})

When('filtro alunos por um codigo EOL existente', function () {
	cy.validar_alunos('', { limit: 1 }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.be.an('array').and.not.be.empty
		this.codigoEol = response.body.results[0].codigo_eol
		cy.validar_alunos('', { codigo_eol: this.codigoEol }).then((resposta) => {
			this.response = resposta
		})
	})
})

Then('a listagem deve conter somente o aluno solicitado', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.results).to.be.an('array').and.not.be.empty
	this.response.body.results.forEach((aluno) => {
		expect(String(aluno.codigo_eol)).to.eq(String(this.codigoEol))
	})
})

When('filtro alunos pelo codigo EOL inexistente', function () {
	cy.validar_alunos('', { codigo_eol: '0' }).then((response) => {
		this.response = response
	})
})

Then('a listagem de alunos deve estar vazia', function () {
	expect(this.response.status).to.eq(200)
	expect(this.response.body.count).to.eq(0)
	expect(this.response.body.results).to.deep.eq([])
})

When('consulto duas paginas consecutivas de alunos', function () {
	cy.validar_alunos('', { limit: 1, offset: 0 }).then((response) => {
		this.primeiraPagina = response
	})
	cy.validar_alunos('', { limit: 1, offset: 1 }).then((response) => {
		this.response = response
	})
})

Then('as paginas devem respeitar o limite sem repetir o primeiro aluno', function () {
	for (const response of [this.primeiraPagina, this.response]) {
		expect(response.status).to.eq(200)
		expect(response.body.results).to.have.length(1)
	}
	expect(this.response.body.results[0].uuid).not.to.eq(this.primeiraPagina.body.results[0].uuid)
})

When('executo {string} para foto de aluno inexistente', function (acao) {
	cy.validar_foto_aluno(acao, '0').then((response) => {
		this.response = response
	})
})

When('executo {string} para foto de aluno sem autenticacao', function (acao) {
	cy.clearCookies()
	cy.validar_foto_aluno(acao, '0', false).then((response) => {
		this.response = response
	})
})

Then('a operacao de foto do aluno deve retornar {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
