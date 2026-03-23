/// <reference types='cypress' />

describe('Validar rotas de homologações de produtos da aplicação SIGPAE', () => {
	var usuario = Cypress.config('usuario_homologacao_produto')
	var senha = Cypress.config('senha')

	before(() => {
		cy.autenticar_login(usuario, senha)
	})

	context('Casos de teste para a rota api/homologacoes-produtos/', () => {
		it('Validar GET de homologações de produtos com sucesso', () => {
			var query = '?limit=10&offset=1'

			cy.validar_homologacao_produtos(query).then((response) => {
				expect(response.status).to.eq(200)

				expect(response.body)
					.to.have.property('count')
					.that.is.a('number')

				expect(response.body)
					.to.have.property('results')
					.that.is.an('array')
					.and.not.to.be.empty

				const item = response.body.results[0]

				expect(item).to.have.property('uuid').that.is.a('string')
				expect(item).to.have.property('produto').that.is.an('object')
			})
		})

		it('Validar estrutura básica do produto', () => {
			var query = '?limit=10&offset=1'

			cy.validar_homologacao_produtos(query).then((response) => {
				const produto = response.body.results[0].produto

				expect(produto).to.have.property('marca')
				expect(produto).to.have.property('fabricante')
				expect(produto).to.have.property('imagens')
				expect(produto).to.have.property('id_externo')
				expect(produto).to.have.property('informacoes_nutricionais')
				expect(produto).to.have.property('homologacao')
			})
		})

		it('Validar marca e fabricante', () => {
			var query = '?limit=10&offset=1'

			cy.validar_homologacao_produtos(query).then((response) => {
				const marca = response.body.results[0].produto.marca
				const fabricante = response.body.results[0].produto.fabricante

				expect(marca).to.have.property('nome')
				expect(marca).to.have.property('uuid')

				expect(fabricante).to.have.property('nome')
				expect(fabricante).to.have.property('uuid')
			})
		})

		it('Validar estrutura da homologacao', () => {
			var query = '?limit=10&offset=1'

			cy.validar_homologacao_produtos(query).then((response) => {
				const homologacao = response.body.results[0].produto.homologacao

				expect(homologacao).to.have.property('uuid')
				expect(homologacao).to.have.property('status')
				expect(homologacao).to.have.property('id_externo')
				expect(homologacao).to.have.property('criado_em')
				expect(homologacao).to.have.property('status_titulo')
			})
		})

		it('Validar arrays de imagens e informacoes nutricionais', () => {
			var query = '?limit=10&offset=1'

			cy.validar_homologacao_produtos(query).then((response) => {
				const imagens = response.body.results[0].produto.imagens
				const info =
					response.body.results[0].produto.informacoes_nutricionais

				expect(imagens).to.be.an('array')
				expect(info).to.be.an('array')
			})
		})
	})
})