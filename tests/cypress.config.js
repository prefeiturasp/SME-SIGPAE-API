const { defineConfig } = require('cypress')
const allureWriter = require('@shelex/cypress-allure-plugin/writer')
const { cloudPlugin } = require('cypress-cloud/plugin')
require('dotenv').config()

module.exports = defineConfig({
	e2e: {
		setupNodeEvents(on, config) {
			allureWriter(on, config)
			require('./cypress/plugin/index.js')(on, config)
			on('before:browser:launch', (browser = {}, launchOptions) => {
				if (browser.name === 'chrome') {
					launchOptions.args.push('--no-sandbox')
					launchOptions.args.push('--disable-dev-shm-usage')
				}
				return launchOptions
			})
			return cloudPlugin(on, config)
		},
		baseUrl: 'https://qa-sigpae.sme.prefeitura.sp.gov.br/',

		usuario_coordenador_logistica: process.env.COORDENADOR_LOGISTICA,
		usuario_coordenador_codae_dilog_logistica:
			process.env.COORDENADOR_CODAE_DILOG_LOGISTICA,
		usuario_coordenador_supervisao_nutricao:
			process.env.COORDENADOR_SUPERVISAO_NUTRICAO,
		usuario_dilog_cronograma: process.env.DILOG_CRONOGRAMA,
		usuario_abastecimento: process.env.ABASTECIMENTO,
		usuario_diretor_ue: process.env.DIRETOR_UE,
		usuario_codae: process.env.CODAE,
		usuario_gpcodae: process.env.GPCODAE,
		usuario_dre: process.env.DRE,
		senha: process.env.SENHA,
		video: false,
		timeout: 60000,
		videoCompression: 0,
		retries: 1,
		screenshotOnRunFailure: true,
		chromeWebSecurity: false,
		experimentalRunAllSpecs: true,
		failOnStatusCode: false,
		specPattern: 'cypress/e2e/**/**/*.{feature,cy.{js,jsx,ts,tsx}}',
	},
})
