import test from 'node:test';
import assert from 'node:assert/strict';
import { fixtures, parseStored, shortDigest } from './fixtures.js';

test('reviewer examples include two listed identifiers and one negative control', () => {
  assert.equal(fixtures.length, 3);
  assert.equal(fixtures[1].law_identifier, 'Fair Housing Act');
  assert.notEqual(fixtures[0].law_identifier, fixtures[2].law_identifier);
});

test('stored JSON and digest display handle unavailable reads', () => {
  assert.deepEqual(parseStored('{"status":"OPEN"}'), { status: 'OPEN' });
  assert.equal(parseStored(''), null);
  assert.equal(parseStored('{oops'), null);
  assert.equal(shortDigest(''), '—');
});
