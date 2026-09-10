const assert = require('node:assert/strict')
const { test } = require('node:test')
const menu = require('../pinokio.js').menu

function info(files = [], running = [], local = {}) {
  return { exists: p => files.includes(p), running: p => running.includes(p), local: () => local }
}

test('partial installations offer recovery instead of Start', async () => {
  assert.equal((await menu({}, info(['env'])))[0].href, 'install.js')
  assert.equal((await menu({}, info(['env/.installed'])))[0].href, 'start.js')
})

test('maintenance stays visible after the environment has been removed', async () => {
  for (const task of ['reset', 'update', 'link', 'install']) {
    const result = await menu({}, info([], [`${task}.js`]))
    assert.equal(result[0].href, `${task}.js`)
    assert.equal(result[0].default, true)
  }
})

test('running server transitions from terminal to captured URL', async () => {
  const files = ['env/.installed']
  assert.equal((await menu({}, info(files, ['start.js'])))[0].href, 'start.js')
  assert.equal((await menu({}, info(files, ['start.js'], { url: 'http://127.0.0.1:9000' })))[0].href,
    'http://127.0.0.1:9000')
})

test('start captures the server URL in group one', async () => {
  const script = await require('../start.js')({ port: async () => 9000 })
  const pattern = script.run[0].params.on[0].event
  const match = new RegExp(pattern.slice(1, -1)).exec('Running on local URL: http://127.0.0.1:9000')
  assert.equal(match[1], 'http://127.0.0.1:9000')
  assert.equal(script.run[1].params.url, '{{input.event[1]}}')
  assert.equal(script.daemon, true)
})

function activeSteps(platform, gpu, args) {
  const result = []
  for (const step of require('../torch.js').run) {
    const condition = step.when.slice(2, -2)
    if (Function('platform', 'gpu', 'args', `return (${condition})`)(platform, gpu, args)) {
      result.push(step)
      if (step.next === null) break
    }
  }
  return result
}

test('each hardware branch installs one coherent torch stack with dependencies', () => {
  for (const [platform, gpu] of [['win32', 'nvidia'], ['win32', 'amd'], ['win32', 'cpu'],
    ['linux', 'nvidia'], ['linux', 'amd'], ['linux', 'cpu'], ['darwin', 'apple']]) {
    const steps = activeSteps(platform, gpu, {})
    assert.equal(steps.length, 1, `${platform}/${gpu}`)
    assert.ok(!steps[0].params.message.includes('--no-deps'))
    assert.ok(!steps[0].params.message.includes('torch-directml'))
  }
})

test('requested NVIDIA extras remain reachable', () => {
  const win = activeSteps('win32', 'nvidia', { triton: true, sageattention: true })
  assert.equal(win.length, 3)
  assert.ok(win[1].params.message.includes('triton-windows'))
  assert.ok(win[2].params.message.includes('sageattention'))
  assert.equal(activeSteps('linux', 'nvidia', { sageattention: true }).length, 2)
})

test('installation marks success only after verification, update reuses install', () => {
  const steps = require('../install.js').run
  assert.equal(steps[0].params.path, 'env/.installed')
  assert.equal(steps.at(-1).method, 'fs.write')
  assert.ok(steps.at(-2).params.message.includes('uv pip check'))
  assert.equal(require('../update.js').run.at(-1).params.uri, 'install.js')
})
