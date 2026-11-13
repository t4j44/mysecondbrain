import fs from 'node:fs';
import path from 'node:path';
import type { FullResult, Reporter, TestCase, TestResult } from '@playwright/test/reporter';

const xml = (value: string) => value.replace(/[<>&"']/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;' }[c]!));

// Hosted runs must not publish raw assertions, HTTP bodies, cookies, console
// output, attachments or page snapshots. This reporter writes outcomes only.
export default class SafeReporter implements Reporter {
  private cases = new Map<string, { name: string; status: string; failed: boolean; duration: number }>();
  private infrastructureFailure = false;
  onStdOut() {}
  onStdErr() {}
  onError() { this.infrastructureFailure = true; }
  onTestEnd(test: TestCase, result: TestResult) {
    const previous = this.cases.get(test.id);
    this.cases.set(test.id, { name: test.titlePath().join(' > '), status: result.status,
      failed: Boolean(previous?.failed || !['passed', 'skipped'].includes(result.status)),
      duration: (previous?.duration || 0) + result.duration });
  }
  onEnd(result: FullResult) {
    const cases = [...this.cases.values()];
    const body = cases.map(item => `<testcase name="${xml(item.name)}" time="${item.duration / 1000}">${
      item.failed ? '<failure message="Hosted check failed; private diagnostic review required."/>'
        : item.status === 'skipped' ? '<skipped/>' : ''}</testcase>`);
    if (this.infrastructureFailure || result.status !== 'passed') {
      body.push('<testcase name="Hosted runner completion"><error message="Runner did not complete successfully."/></testcase>');
    }
    const destination = path.resolve('test-results/e2e-results.xml');
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.writeFileSync(destination, `<?xml version="1.0"?><testsuite tests="${body.length}">${body.join('')}</testsuite>`);
    console.log(JSON.stringify({ hosted_e2e: result.status, tests: cases.length,
      failed: cases.filter(item => item.failed).length, skipped: cases.filter(item => item.status === 'skipped').length }));
  }
}
