function leaderReceipt(transaction) {
  const receipts = transaction?.consensus_data?.leader_receipt;
  if (!Array.isArray(receipts)) return null;
  return receipts.find(receipt => receipt.mode === 'leader') ?? receipts[0] ?? null;
}

export function isFinalSuccess(transaction) {
  return (transaction?.status_name ?? transaction?.statusName) === 'FINALIZED' &&
    (transaction?.result_name ?? transaction?.resultName) === 'MAJORITY_AGREE' &&
    leaderReceipt(transaction)?.execution_result === 'SUCCESS';
}

export function returnedId(transaction) {
  const raw = leaderReceipt(transaction)?.result?.payload?.readable;
  const id = typeof raw === 'string' && /^\d+$/.test(raw) ? Number(raw) : NaN;
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export function failureReason(transaction) {
  const leader = leaderReceipt(transaction);
  return leader?.genvm_result?.error_description ||
    (transaction?.result_name ?? transaction?.resultName) || leader?.execution_result ||
    transaction?.status_name || transaction?.statusName || 'Unknown transaction result';
}
