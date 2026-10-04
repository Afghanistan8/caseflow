import test from 'node:test';
import assert from 'node:assert/strict';
import { failureReason, isFinalSuccess, returnedId } from './transactions.js';

const finalized = {
  status_name: 'FINALIZED',
  result_name: 'MAJORITY_AGREE',
  consensus_data: {
    leader_receipt: [{
      mode: 'leader',
      execution_result: 'SUCCESS',
      result: { status: 'return', payload: { readable: '7' } }
    }]
  }
};

test('recognizes the installed SDK receipt shape and exact returned case ID', () => {
  assert.equal(isFinalSuccess(finalized), true);
  assert.equal(returnedId(finalized), 7);
});

test('does not mistake finalization for successful contract execution', () => {
  const failed = {
    status_name: 'FINALIZED',
    consensus_data: { leader_receipt: [{
      mode: 'leader', execution_result: 'ERROR',
      genvm_result: { error_description: 'record revision conflict' }
    }] }
  };
  assert.equal(isFinalSuccess(failed), false);
  assert.equal(returnedId(failed), null);
  assert.equal(failureReason(failed), 'record revision conflict');
});

test('rejects a finalized validator disagreement even when the leader succeeded', () => {
  const disagreed = { ...finalized, result_name: 'MAJORITY_DISAGREE' };
  assert.equal(isFinalSuccess(disagreed), false);
  assert.equal(failureReason(disagreed), 'MAJORITY_DISAGREE');
});

test('does not infer an ID from malformed or missing return data', () => {
  assert.equal(returnedId({ ...finalized, consensus_data: { leader_receipt: [{ mode: 'leader', execution_result: 'SUCCESS' }] } }), null);
  assert.equal(returnedId({ ...finalized, consensus_data: { leader_receipt: [{ mode: 'leader', result: { payload: { readable: '7x' } } }] } }), null);
});
