import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';
import { isFinalSuccess } from '../src/transactions.js';

const [address, txHash] = process.argv.slice(2);
if (!/^0x[0-9a-fA-F]{40}$/.test(address || '') || !/^0x[0-9a-fA-F]{64}$/.test(txHash || '')) {
  throw new Error('Usage: node scripts/verify-deployment.mjs <contract-address> <deployment-tx>');
}

const client = createClient({ chain: studionet });
const [deployedCode, transaction, receipt, protocolRaw, countsRaw] = await Promise.all([
  client.getContractCode(address),
  client.getTransaction({ hash: txHash }),
  client.waitForTransactionReceipt({ hash: txHash, status: TransactionStatus.FINALIZED }),
  client.readContract({ address, functionName: 'get_protocol', args: [] }),
  client.readContract({ address, functionName: 'get_counts', args: [] })
]);

const localCode = readFileSync(new URL('../../contracts/caseflow.py', import.meta.url), 'utf8');
const normalized = value => value.replace(/\r\n/g, '\n').trimEnd();
const hash = value => createHash('sha256').update(normalized(value)).digest('hex');
const localDigest = hash(localCode);
const deployedDigest = hash(deployedCode);
const protocol = JSON.parse(protocolRaw);
const counts = JSON.parse(countsRaw);

const result = {
  address,
  txHash,
  status: transaction.statusName,
  receiptStatus: receipt.status_name,
  receiptSuccess: isFinalSuccess(receipt),
  consensusResult: transaction.resultName,
  execution: transaction.txExecutionResultName ?? transaction.consensus_data?.leader_receipt?.[0]?.execution_result ?? null,
  sourceMatches: localDigest === deployedDigest,
  sourceSha256: deployedDigest,
  protocol,
  counts
};
console.log(JSON.stringify(result, null, 2));

if (transaction.statusName !== 'FINALIZED' || !result.receiptSuccess || !result.sourceMatches ||
    protocol.chain_id !== 61999 || protocol.name !== 'Caseflow') {
  process.exitCode = 1;
}
