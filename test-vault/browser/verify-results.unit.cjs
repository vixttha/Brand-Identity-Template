const assert = require('node:assert/strict');
const { spawnSync } = require('node:child_process');
const { mkdtempSync, rmSync, writeFileSync } = require('node:fs');
const { tmpdir } = require('node:os');
const { join } = require('node:path');
const { test } = require('node:test');
const { verifyResults } = require('./verify-results.cjs');

const required = ['Decode RGBA', 'Composite on dark'];

function spec(title, testOverrides = {}) {
  return {
    title,
    tests: [{
      expectedStatus: 'passed',
      status: 'expected',
      results: [{ status: 'passed' }],
      ...testOverrides,
    }],
  };
}

function report(...specs) {
  return { errors: [], suites: [{ specs }] };
}

test('accepts each required test passing once, including nested suites', () => {
  const run = report(spec(required[1]));
  run.suites[0].suites = [{ specs: [spec(required[0])] }];
  assert.equal(verifyResults(required, run), 2);
});

test('rejects an otherwise green report when one required test is skipped', () => {
  const skipped = spec(required[0], { expectedStatus: 'skipped', status: 'skipped',
    results: [{ status: 'skipped' }] });
  assert.throws(() => verifyResults(required, report(skipped, spec(required[1]))),
    /did not pass: Decode RGBA/);
});

test('rejects an all-skipped or empty test run', () => {
  const skipped = required.map(title => spec(title, {
    expectedStatus: 'skipped', status: 'skipped', results: [],
  }));
  assert.throws(() => verifyResults(required, report(...skipped)), /did not pass/);
  assert.throws(() => verifyResults(required, report()), /Missing required test/);
});

test('rejects an omitted case even when every reported case passed', () => {
  assert.throws(() => verifyResults(required, report(spec(required[0]))),
    /Missing required test: Composite on dark/);
});

test('rejects duplicate, unexpected, and multi-project outcomes', () => {
  assert.throws(() => verifyResults(required, report(spec(required[0]), spec(required[0]))),
    /Duplicate browser test/);
  assert.throws(() => verifyResults(required, report(spec('Unlisted test'))),
    /Undeclared browser test/);
  const duplicate = spec(required[0]);
  duplicate.tests.push(duplicate.tests[0]);
  assert.throws(() => verifyResults(required, report(duplicate, spec(required[1]))),
    /did not pass: Decode RGBA/);
});

test('rejects expected failures, flaky retries, and interrupted outcomes', () => {
  for (const overrides of [
    { expectedStatus: 'failed', results: [{ status: 'failed' }] },
    { status: 'flaky', results: [{ status: 'failed' }, { status: 'passed' }] },
    { status: 'unexpected', results: [{ status: 'interrupted' }] },
    { results: [] },
  ]) {
    assert.throws(() => verifyResults(required,
      report(spec(required[0], overrides), spec(required[1]))), /did not pass/);
  }
});

test('rejects reporter errors and invalid required test declarations', () => {
  const run = report(...required.map(title => spec(title)));
  assert.throws(() => verifyResults(required, { ...run, errors: [{ message: 'global teardown' }] }),
    /missing suites or contains run errors/);
  for (const declaration of [[], ['', 'Valid'], [required[0], required[0]]]) {
    assert.throws(() => verifyResults(declaration, run), /unique nonempty titles/);
  }
});

test('refuses a real Playwright report when the runner exits zero with a skip', t => {
  const directory = mkdtempSync(join(tmpdir(), 'playwright-receipt-'));
  t.after(() => rmSync(directory, { recursive: true, force: true }));
  const requiredPath = join(directory, 'required.json');
  const reportPath = join(directory, 'report.json');
  const configPath = join(directory, 'playwright.config.cjs');
  writeFileSync(requiredPath, JSON.stringify(required));
  writeFileSync(configPath, 'module.exports = { testDir: ".", workers: 1 };');
  writeFileSync(join(directory, 'example.spec.cjs'), [
    `const { test } = require(${JSON.stringify(require.resolve('@playwright/test'))});`,
    `test(${JSON.stringify(required[0])}, () => {});`,
    `test.skip(${JSON.stringify(required[1])}, () => {});`,
  ].join('\n'));

  const run = spawnSync(process.execPath, [
    require.resolve('@playwright/test/cli'), 'test', '--config', configPath, '--reporter=json',
  ], {
    cwd: directory,
    encoding: 'utf8',
    env: { ...process.env, PLAYWRIGHT_JSON_OUTPUT_FILE: reportPath },
    timeout: 20_000,
  });
  assert.equal(run.status, 0, run.stderr || run.error?.message);

  const verdict = spawnSync(process.execPath, [
    join(__dirname, 'verify-results.cjs'), requiredPath, reportPath,
  ], { encoding: 'utf8', timeout: 20_000 });
  assert.equal(verdict.status, 1, verdict.stdout || verdict.error?.message);
  assert.match(verdict.stderr, /Required browser test did not pass: Composite on dark/);
});
