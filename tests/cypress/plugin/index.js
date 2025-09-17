const cucumber = require('cypress-cucumber-preprocessor').default
require('dotenv').config()
const postgreSQL = require('cypress-postgresql')
const pg = require('pg')
const dbConfig = {
	user: process.env.DB_USER,
	password: process.env.DB_PASSWORD,
	host: process.env.DB_HOST,
	database: process.env.DB_DATABASE
}

module.exports = (on, config) => {
	on('file:preprocessor', cucumber())
	const pool = new pg.Pool(dbConfig)
	var tasks = postgreSQL.loadDBPlugin(pool)
	on('task', tasks)
	return config
}
