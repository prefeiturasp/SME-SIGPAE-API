import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

function guardarResposta(contexto, requisicao) {
	requisicao.then((response) => {
		contexto.response = response
	})
}

function validarEmbalagens(response) {
	expect(response.body).to.have.property('results').that.is.an('array')

	response.body.results.forEach((embalagem) => {
		expect(embalagem).to.include.all.keys('uuid', 'nome')
		expect(embalagem.uuid).to.be.a('string').and.not.be.empty
		expect(embalagem.nome).to.be.a('string').and.not.be.empty
	})
}

Given(
	'que estou autenticado como CODAE para consultar embalagens de produto',
	() => {
		cy.autenticar_login(Cypress.config('usuario_codae'), Cypress.config('senha'))
	},
)

When('consulto todas as embalagens de produto', function () {
	guardarResposta(this, cy.consultar_embalagens_produto())
})

When(
	'consulto embalagens de produto com limite {int} e deslocamento {int}',
	function (limit, offset) {
		this.limit = limit
		this.offset = offset
		guardarResposta(
			this,
			cy.consultar_embalagens_produto({ limit, offset }),
		)
	},
)

Then(
	'a consulta de embalagens de produto retorna status 200 e uma lista valida',
	function () {
		expect(this.response.status).to.eq(200)
		validarEmbalagens(this.response)
	},
)

Then(
	'a consulta paginada de embalagens de produto retorna status 200 e uma lista valida',
	function () {
		expect(this.response.status).to.eq(200)
		expect(this.limit).to.be.a('number')
		expect(this.offset).to.be.a('number')
		validarEmbalagens(this.response)
	},
)
