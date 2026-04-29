const { spawnSync } = require('node:child_process')

const args = process.argv.slice(2)
const res = spawnSync('npx', ['eslint', ...args], {
  stdio: 'inherit',
  shell: true,
  env: {
    ...process.env,
    ESLINT_USE_FLAT_CONFIG: 'false',
  },
})

if (typeof res.status === 'number') {
  process.exit(res.status)
}
process.exit(1)
