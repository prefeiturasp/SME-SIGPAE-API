import { Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const uuidInvalido = '53886ad8-cb8b-4175-853e-de087aaaaaaa'

function validarPermissao(response) {
	expect(response.status).to.eq(403)
	expect(response.body).to.have.property('detail')
}

function validarLista(response, resultado = 'dados') {
	expect([200, 403]).to.include(response.status)
	if (response.status === 403) {
		validarPermissao(response)
		return
	}
	expect(response.body).to.have.property('results').that.is.an('array')
	if (resultado === 'dados') expect(response.body.results).not.empty
	if (resultado === 'vazio') expect(response.body.results).empty
}

function obterCronograma() {
	return cy.validar_cronogramas('').then((response) => {
		expect([200, 403]).to.include(response.status)
		if (response.status === 403) return null
		expect(response.body.results).to.be.an('array').and.not.empty
		return response.body.results[0]
	})
}

function dadosCronograma(observacoes, data = '2025-10-26') {
	return {
		nome: `Teste Automacao ${Date.now()}`,
		armazem: 'd020c118-f124-4fec-a136-4e3da9ba63d9',
		empresa: 'd0630b2b-8e45-472c-b9c6-90451b60b081',
		contrato: '387121e0-f887-4ecf-9521-00c519e9830d',
		unidade_medida: 'e274494c-78aa-42cf-8718-0e362c0f8ba5',
		qtd_total_programada: 10,
		etapas: [{ numero_empenho: '123456', etapa: 1, parte: 'Parte 1', data_programada: data, quantidade: 10, total_embalagens: 1, qtd_total_empenho: 10, uuid: 'e972f048-a31b-4929-a337-d6b8057e60d9' }],
		programacoes_de_recebimento: [{ data_programada: '26/06/2025 - Etapa 1  - Parte 1', tipo_carga: 'PALETIZADA', uuid: '0f25baf8-4ed4-4572-a9cb-5871e076ec6b' }],
		ficha_tecnica: '7a308949-4e9d-4e2a-abea-be9322fa955a',
		tipo_embalagem_secundaria: '05690384-2d95-4e21-8646-8a0f8f8e0673',
		custo_unitario_produto: 10,
		uuid: 'fa932382-cd4e-4a7e-baa4-7351abe9cdf4',
		observacoes,
	}
}

Given('que estou autenticado para consultar cronogramas', () => {
	cy.autenticar_login(Cypress.env('usuario_dilog_cronograma'), Cypress.env('senha'))
})

When('consulto cronogramas com status {string}', function (status) {
	const parametros = status === 'sem filtro' ? '' : `status=${status}`
	cy.validar_cronogramas(parametros).then((response) => { this.response = response })
})

Then('a consulta de cronogramas retorna dados ou permissao negada', function () {
	validarLista(this.response)
})

When('consulto cronogramas pelo campo {string} com valor {string}', function (campo, valor) {
	cy.validar_cronogramas(`${campo}=${encodeURIComponent(valor)}`)
		.then((response) => { this.response = response })
})

Then('a consulta de cronogramas retorna {string} ou permissao negada', function (resultado) {
	validarLista(this.response, resultado)
})

When('consulto cronograma por parametro UUID existente', function () {
	obterCronograma().then((item) => {
		if (!item) {
			this.response = { status: 403, body: { detail: 'Sem permissao' } }
			return
		}
		cy.validar_cronogramas(`uuid=${item.uuid}`).then((response) => { this.response = response })
	})
})

When('consulto o detalhe {string} de cronograma com UUID {string}', function (detalhe, tipo) {
	const executar = (uuid) => {
		const comandos = {
			cronograma: () => cy.validar_cronogramas_por_uuid(uuid),
			'ficha recebimento': () => cy.validar_dados_cronograma_ficha_recebimento(uuid),
			log: () => cy.validar_detalhar_com_log(uuid),
		}
		comandos[detalhe]().then((response) => { this.response = response })
	}
	if (tipo === 'invalido') {
		executar(uuidInvalido)
		return
	}
	obterCronograma().then((item) => {
		if (item) executar(item.uuid)
		else this.response = { status: 403, body: { detail: 'Sem permissao' } }
	})
})

Then('o detalhe de cronograma retorna {string}', function (resultado) {
	if (resultado === 'nao encontrado') {
		expect([403, 404]).to.include(this.response.status)
	} else {
		expect([200, 403]).to.include(this.response.status)
	}
	if (this.response.status === 403) validarPermissao(this.response)
	if (this.response.status === 200) expect(this.response.body).to.exist
})

When('consulto a dashboard de cronogramas com filtro {string}', function (filtro) {
	if (filtro === 'sem parametros') {
		cy.validar_dashboard().then((response) => { this.response = response })
		return
	}
	const fixos = {
		'filtros vazios': '?numero_cronograma=&nome_produto=',
		'produto inexistente': '?numero_cronograma=&nome_produto=sadasdasda',
		'numero inexistente': '?numero_cronograma=1234567890&nome_produto=',
	}
	if (fixos[filtro]) {
		cy.validar_dashboard_com_filtro(fixos[filtro]).then((response) => { this.response = response })
		return
	}
	cy.validar_dashboard_com_filtro('').then((lista) => {
		if (lista.status === 403 || !lista.body.results.length) {
			this.response = lista
			return
		}
		const item = lista.body.results[0]
		const numero = encodeURIComponent(item.numero_cronograma || item.numero)
		const produto = encodeURIComponent(item.nome_produto)
		const filtros = {
			'filtros preenchidos': `?numero_cronograma=${numero}&nome_produto=${produto}`,
			'produto existente': `?numero_cronograma=&nome_produto=${produto}`,
			'numero existente': `?numero_cronograma=${numero}&nome_produto=`,
		}
		cy.validar_dashboard_com_filtro(filtros[filtro]).then((response) => { this.response = response })
	})
})

Then('a dashboard de cronogramas retorna {string} ou permissao negada', function (resultado) {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) {
		validarPermissao(this.response)
		return
	}
	expect(this.response.body).to.have.property('results').that.is.an('array')
	if (resultado === 'dados') {
		expect(this.response.body.results).not.empty
		return
	}
	this.response.body.results.forEach((grupo) => {
		expect(grupo).to.have.property('dados').that.is.an('array').and.empty
	})
})

When('consulto a lista auxiliar de cronogramas {string}', function (lista) {
	const consultas = {
		'ficha recebimento': () => cy.validar_lista_cronogramas_ficha_recebimento(),
		cadastro: () => cy.validar_lista_cronogramas_cadastro(),
		relatorio: () => cy.validar_listagem_relatorio(),
		'opcoes etapas': () => cy.validar_opcoes_etapas(),
		rascunhos: () => cy.validar_rascunhos(),
	}
	consultas[lista]().then((response) => { this.response = response })
})

Then('a lista auxiliar de cronogramas retorna dados ou permissao negada', function () {
	expect([200, 403]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
	else expect(this.response.body).to.exist
})

When('cadastro um cronograma para teste', function () {
	cy.cadastrar_cronogramas(dadosCronograma('Teste Automacao')).then((response) => {
		this.response = response
		if (response.status === 201) {
			cy.deletar_cronograma(response.body.uuid).its('status').should('eq', 204)
		}
	})
})

Then('o cronograma e criado e removido ou retorna permissao negada', function () {
	expect([201, 403]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
	else expect(this.response.body.observacoes).to.eq('Teste Automacao')
})

When('cadastro e excluo um cronograma para teste', function () {
	cy.cadastrar_cronogramas(dadosCronograma('Teste Automacao - Deletar', '2025-06-26'))
		.then((cadastro) => {
			if (cadastro.status === 403) {
				this.response = cadastro
				return
			}
			expect(cadastro.status).to.eq(201)
			cy.deletar_cronograma(cadastro.body.uuid).then((response) => { this.response = response })
		})
})

Then('o cronograma e excluido ou retorna permissao negada', function () {
	expect([204, 403]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
})

When('excluo um cronograma com UUID invalido', function () {
	cy.deletar_cronograma(uuidInvalido).then((response) => { this.response = response })
})

Then('a exclusao de cronograma retorna nao encontrado ou permissao negada', function () {
	expect([403, 404]).to.include(this.response.status)
	if (this.response.status === 403) validarPermissao(this.response)
})
