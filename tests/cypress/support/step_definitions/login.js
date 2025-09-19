import {  Given, When, Then } from 'cypress-cucumber-preprocessor/steps'

const Dado = Given
const Quando = When
const Entao = Then

Dado('eu acesso o sistema com a visualização {string}', function (device) {
	cy.login_sme(device)
})

Dado('informo os dados nos campos {string} e {string}', function (usuario, senha) {
	cy.dados_de_login(usuario, senha)
})

Quando('clico no botão acessar', function () {
	cy.clicar_botao()
})

Entao('sistema realiza validacao necessesaria {string} para o cenario {string}', function (mensagem) {
	cy.validar_mensagem(mensagem)
})