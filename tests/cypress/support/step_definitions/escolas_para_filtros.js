import { When, Then } from 'cypress-cucumber-preprocessor/steps'

const inexistente = '00000000-0000-0000-0000-000000000000'
const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function autenticar() {
	return cy.autenticar_login(Cypress.env('usuario_codae'), Cypress.env('senha'))
}
function consultar(contexto, opcoes = {}) {
	return cy.executar_escolas_para_filtros({ token: globalThis.token, ...opcoes }).then((response) => { contexto.response = response })
}
function referencia(contexto) {
	return cy.executar_escolas_para_filtros({ token: globalThis.token }).then((response) => {
		expect(response.status).to.eq(200)
		expect(response.body).to.be.an('array').and.not.be.empty
		contexto.escolas = response.body
		contexto.escola = response.body.find((item) => item.codigo_eol && item.lote && item.diretoria_regional && item.tipo_unidade)
		expect(contexto.escola, 'Escola com DRE, lote e tipo de unidade').to.exist
	})
}

When('consulto escolas para filtros com sucesso', function () {
	return autenticar().then(() => consultar(this))
})
When('consulto {string} de uma escola para filtros existente', function (rota) {
	autenticar().then(() => referencia(this)).then(() => consultar(this, { caminho: `${this.escola.uuid}/${rota}` }))
})
When('consulto escolas para filtros usando {string}', function (filtro) {
	autenticar().then(() => referencia(this)).then(() => {
		const escola = this.escola
		const tipos = [...new Set(this.escolas.filter((e) => e.tipo_unidade).map((e) => e.tipo_unidade.uuid))].slice(0, 2)
		const configuracoes = {
			dre: [{ diretoria_regional__uuid: escola.diretoria_regional.uuid }, (e) => e.diretoria_regional?.uuid === escola.diretoria_regional.uuid],
			lote: [{ lote__uuid: escola.lote.uuid }, (e) => e.lote?.uuid === escola.lote.uuid],
			tipo: [{ tipo_unidade__uuid__in: escola.tipo_unidade.uuid }, (e) => e.tipo_unidade?.uuid === escola.tipo_unidade.uuid],
			multiplos: [{ tipo_unidade__uuid__in: tipos.join(',') }, (e) => tipos.includes(e.tipo_unidade?.uuid)],
			combinados: [{ diretoria_regional__uuid: escola.diretoria_regional.uuid, lote__uuid: escola.lote.uuid, tipo_unidade__uuid__in: escola.tipo_unidade.uuid }, (e) => e.diretoria_regional?.uuid === escola.diretoria_regional.uuid && e.lote?.uuid === escola.lote.uuid && e.tipo_unidade?.uuid === escola.tipo_unidade.uuid],
			'tipos em lista': [{ 'tipo_unidade__uuid[]': tipos }, (e) => tipos.includes(e.tipo_unidade?.uuid)],
			'lotes em lista': [{ 'lote__uuid[]': [escola.lote.uuid] }, (e) => e.lote?.uuid === escola.lote.uuid],
			'excluir tipo': [{ 'excluir_tipo_unidade__uuid[]': [escola.tipo_unidade.uuid] }, (e) => e.tipo_unidade?.uuid !== escola.tipo_unidade.uuid],
		}
		expect(configuracoes).to.have.property(filtro)
		const [qs, predicado] = configuracoes[filtro]
		this.esperadas = this.escolas.filter(predicado).map((e) => e.uuid).sort()
		return consultar(this, { qs })
	})
})
When('consulto escolas para filtros pelo tipo de gestao', function () {
	autenticar().then(() => referencia(this)).then(() => {
		cy.request({ url: `${Cypress.config('baseUrl')}api/escolas-simplissima/`, qs: { codigo_eol: this.escola.codigo_eol }, headers: { Authorization: `JWT ${globalThis.token}` }, timeout: 60000 }).then((response) => {
			expect(response.status).to.eq(200)
			expect(response.body.results).to.be.an('array')
			const escola = response.body.results.find((e) => e.uuid === this.escola.uuid)
			expect(escola).to.exist
			this.tipoGestao = escola.tipo_gestao
			expect(this.tipoGestao).to.be.a('string').and.not.be.empty
			return consultar(this, { qs: { tipo_gestao__nome: this.tipoGestao } })
		})
	})
})
Then('escolas para filtros respeita o tipo de gestao', function () {
	expect(this.response.body.map((e) => e.uuid)).to.include(this.escola.uuid)
	// Confirmar o tipo em uma amostra independente, pois a rota nao expoe esse campo.
	const amostra = this.response.body.filter((e) => e.codigo_eol).slice(0, 3)
	expect(amostra).not.to.be.empty
	amostra.forEach((escola) => {
		cy.request({ url: `${Cypress.config('baseUrl')}api/escolas-simplissima/`, qs: { codigo_eol: escola.codigo_eol }, headers: { Authorization: `JWT ${globalThis.token}` }, timeout: 60000 }).then((response) => {
			expect(response.status).to.eq(200)
			const detalhe = response.body.results.find((e) => e.uuid === escola.uuid)
			expect(detalhe).to.exist
			expect(detalhe.tipo_gestao).to.eq(this.tipoGestao)
		})
	})
})
When('consulto escolas para filtros com parametro {string} e valor {string}', function (campo, valor) {
	this.campoInvalido = campo
	return autenticar().then(() => consultar(this, { qs: { [campo]: valor === 'inexistente' ? inexistente : valor } }))
})
When('consulto {string} de escolas para filtros com UUID {string}', function (rota, uuid) {
	return autenticar().then(() => consultar(this, { caminho: `${uuid === 'inexistente' ? inexistente : uuid}/${rota}` }))
})
When('consulto escolas para filtros na rota {string} com acesso {string}', function (rota, acesso) {
	cy.clearCookies()
	return consultar(this, { caminho: rota === 'listagem' ? '' : `${inexistente}/${rota}`, token: acesso === 'token invalido' ? 'token-invalido' : undefined })
})
When('executo {string} em escolas para filtros na rota {string}', function (metodo, rota) {
	return autenticar().then(() => consultar(this, { metodo, caminho: rota === 'listagem' ? '' : `${inexistente}/${rota}` }))
})
Then('a operacao de escolas para filtros retorna {int}', function (status) {
	expect(this.response.status).to.eq(status)
	if (status === 401) expect(this.response.body.detail).to.be.a('string').and.not.be.empty
})
Then('escolas para filtros retorna uma lista valida', function () {
	expect(this.response.body).to.be.an('array')
	const campos = ['uuid', 'nome', 'codigo_eol', 'diretoria_regional', 'tipo_unidade', 'lote'].sort()
	const invalidas = this.response.body.filter((e) => {
		return !e || JSON.stringify(Object.keys(e).sort()) !== JSON.stringify(campos)
			|| !uuidRegex.test(e.uuid) || typeof e.nome !== 'string' || typeof e.codigo_eol !== 'string'
			|| ['diretoria_regional', 'tipo_unidade', 'lote'].some((campo) => e[campo] !== null && !uuidRegex.test(e[campo]?.uuid))
	})
	expect(invalidas, 'Escolas fora do contrato de resposta').to.deep.eq([])
})
Then('escolas para filtros corresponde ao filtro aplicado', function () {
	expect(this.response.body.map((e) => e.uuid).sort()).to.deep.eq(this.esperadas)
})
Then('escolas para filtros retorna uma lista vazia', function () {
	expect(this.response.body).to.deep.eq([])
})
Then('escolas para filtros retorna periodos ou tipos de alimentacao validos', function () {
	expect(this.response.body).to.be.an('array')
	this.response.body.forEach((item) => {
		expect(item).to.include.all.keys('uuid', 'nome')
		expect(item.uuid).to.match(uuidRegex)
		expect(item.nome).to.be.a('string').and.not.be.empty
	})
})
Then('escolas para filtros informa parametro invalido', function () {
	expect(this.response.body[this.campoInvalido]).to.be.an('array').and.not.be.empty
})
