const { defineConfig } = require('cypress')
const allureWriter = require('@shelex/cypress-allure-plugin/writer')
const { cloudPlugin } = require('cypress-cloud/plugin')
require('dotenv').config()

const baseUrl =
  process.env.CYPRESS_BASE_URL ||
  process.env.BASE_URL ||
  process.env.SIGPAE_BASE_URL ||
  'https://qa-sigpae.sme.prefeitura.sp.gov.br/'

const INVALID_LOOPBACK_PROXY = 'http://127.0.0.1:9'

function normalizeProxyEnvironment(targetUrl) {
  const proxyKeys = [
    'HTTP_PROXY',
    'HTTPS_PROXY',
    'ALL_PROXY',
    'http_proxy',
    'https_proxy',
    'all_proxy',
    'GIT_HTTP_PROXY',
    'GIT_HTTPS_PROXY',
  ]

  proxyKeys.forEach((key) => {
    if (process.env[key] === INVALID_LOOPBACK_PROXY) {
      delete process.env[key]
    }
  })

  const hostname = new URL(targetUrl).hostname
  const currentNoProxy = process.env.NO_PROXY || process.env.no_proxy || ''
  const entries = currentNoProxy
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)

  if (!entries.includes(hostname)) {
    entries.push(hostname)
  }

  process.env.NO_PROXY = entries.join(',')
  process.env.no_proxy = process.env.NO_PROXY
}

normalizeProxyEnvironment(baseUrl)

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

    baseUrl,
    specPattern: [
      'tests/cypress/e2e/**/*.cy.js',
      'tests/cypress/e2e/**/*.feature',
    ],
    supportFile: 'tests/cypress/support/e2e.js',
    experimentalRunAllSpecs: true,
  },

  env: {
    usuario_coordenador_logistica: process.env.COORDENADOR_LOGISTICA,
    usuario_coordenador_codae_dilog_logistica:
      process.env.COORDENADOR_CODAE_DILOG_LOGISTICA,
    usuario_coordenador_supervisao_nutricao:
      process.env.COORDENADOR_SUPERVISAO_NUTRICAO,
    usuario_dilog_cronograma: process.env.DILOG_CRONOGRAMA,
    usuario_dilog_qualidade: process.env.DILOG_QUALIDADE,
    usuario_abastecimento: process.env.ABASTECIMENTO,
    usuario_diretor_ue: process.env.DIRETOR_UE,
    usuario_codae: process.env.CODAE,
    usuario_gpcodae: process.env.GPCODAE,
    usuario_dre: process.env.DRE,
    senha: process.env.SENHA,

    db_user: process.env.DB_USER,
    db_password: process.env.DB_PASSWORD,
    db_host: process.env.DB_HOST,
    db_database: process.env.DB_DATABASE,
  },
})
