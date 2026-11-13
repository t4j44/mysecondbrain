// @vitest-environment node
import fs from 'node:fs';
import { afterEach, expect, it, vi } from 'vitest';
import type { TestCase, TestResult } from '@playwright/test/reporter';
import SafeReporter from '../../e2e/safe-reporter';

afterEach(() => { vi.restoreAllMocks(); });
function harness() {
  vi.spyOn(fs, 'mkdirSync').mockReturnValue(undefined);
  const write = vi.spyOn(fs, 'writeFileSync').mockImplementation(() => {});
  const log = vi.spyOn(console, 'log').mockImplementation(() => {});
  return { reporter: new SafeReporter(), write, log };
}
const testCase = { id: 'case-1', titlePath: () => ['chromium', 'A < B & C'] } as unknown as TestCase;
const result = (status: string) => ({ status, duration: 10, error: { message: 'synthetic-password-do-not-log' }, stdout: ['synthetic-private-record'], attachments: [{ body: 'synthetic-cookie' }] }) as unknown as TestResult;
it('retains failures without publishing diagnostic secrets or attachments', () => {
  const { reporter, write, log } = harness();
  reporter.onTestEnd(testCase, result('failed'));
  reporter.onEnd({ status: 'failed', startTime: new Date(), duration: 10 });
  const output = String(write.mock.calls[0][1]);
  expect(output).toContain('<failure');
  expect(output).toContain('A &lt; B &amp; C');
  expect(JSON.stringify([write.mock.calls, log.mock.calls])).not.toMatch(/synthetic-password|synthetic-private-record|synthetic-cookie/);
});
it('does not turn a failed attempt followed by a retry into clean acceptance', () => {
  const { reporter, write } = harness();
  reporter.onTestEnd(testCase, result('failed'));
  reporter.onTestEnd(testCase, result('passed'));
  reporter.onEnd({ status: 'passed', startTime: new Date(), duration: 20 });
  expect(String(write.mock.calls[0][1])).toContain('<failure');
});
it('preserves skipped tests for the release gate to reject', () => {
  const { reporter, write } = harness();
  reporter.onTestEnd(testCase, result('skipped'));
  reporter.onEnd({ status: 'passed', startTime: new Date(), duration: 10 });
  expect(String(write.mock.calls[0][1])).toContain('<skipped/>');
});
it('makes infrastructure failure explicit even if no test finishes', () => {
  const { reporter, write } = harness();
  reporter.onError();
  reporter.onEnd({ status: 'failed', startTime: new Date(), duration: 10 });
  expect(String(write.mock.calls[0][1])).toContain('<error');
});
