const { readFileSync } = require('node:fs');

function* allSpecs(suites) {
  for (const suite of suites) {
    yield* suite.specs;
    yield* allSpecs(suite.suites ?? []);
  }
}

function verifyResults(required, report) {
  if (!Array.isArray(required) || required.length === 0 ||
      required.some(title => typeof title !== 'string' || !title.trim()) ||
      new Set(required).size !== required.length) {
    throw new Error('Required browser tests must have unique nonempty titles');
  }
  if (!Array.isArray(report?.suites) || !Array.isArray(report.errors) || report.errors.length) {
    throw new Error('Playwright report is missing suites or contains run errors');
  }

  const missing = new Set(required);
  const seen = new Set();
  for (const { title, tests } of allSpecs(report.suites)) {
    if (seen.has(title)) throw new Error(`Duplicate browser test: ${title}`);
    if (!missing.delete(title)) throw new Error(`Undeclared browser test: ${title}`);
    seen.add(title);

    const outcome = tests?.[0];
    if (tests?.length !== 1 || outcome?.expectedStatus !== 'passed' ||
        outcome.status !== 'expected' || outcome.results?.length !== 1 ||
        outcome.results[0].status !== 'passed') {
      throw new Error(`Required browser test did not pass: ${title} (${outcome?.status ?? 'no outcome'})`);
    }
  }
  if (missing.size) throw new Error(`Missing required test: ${[...missing].join(', ')}`);
  return seen.size;
}

if (require.main === module) {
  try {
    const [requiredPath, reportPath] = process.argv.slice(2);
    const required = JSON.parse(readFileSync(requiredPath, 'utf8'));
    const report = JSON.parse(readFileSync(reportPath, 'utf8'));
    const passed = verifyResults(required, report);
    console.log(`Playwright receipt: all ${passed} declared tests executed and passed`);
  } catch (error) {
    console.error(`Playwright receipt refused: ${error.message}`);
    process.exitCode = 1;
  }
}

module.exports = { verifyResults };
