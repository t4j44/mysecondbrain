"""Fail release gates if a test suite is empty or contains skipped tests."""
import sys
import xml.etree.ElementTree as ET

root = ET.parse(sys.argv[1]).getroot()
cases = list(root.iter('testcase'))
assert cases, 'Release gate produced no test cases.'
assert not any(case.find('skipped') is not None for case in cases), 'Release gate contains skipped tests.'
assert not any(case.find('failure') is not None or case.find('error') is not None for case in cases), 'Release gate contains failed tests.'
print(f'Gate evidence: {len(cases)} tests, no skips or failures.')
