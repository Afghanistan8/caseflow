import React, { useCallback, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createClient } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';
import { TransactionHashVariant, TransactionStatus } from 'genlayer-js/types';
import { fixtures, parseStored, shortDigest, SOURCE_URL } from './fixtures.js';
import { failureReason, isFinalSuccess, returnedId } from './transactions.js';
import './style.css';

const contractAddress = import.meta.env.VITE_CASEFLOW_ADDRESS || '0xcE9f13ED45AC3561659Beed43B7FD9dAfcf2A13E';
const addressOk = /^0x[a-fA-F0-9]{40}$/.test(contractAddress || '');
const readClient = createClient({ chain: studionet });

function App() {
  const [wallet, setWallet] = useState('');
  const [walletChainId, setWalletChainId] = useState(null);
  const [caseId, setCaseId] = useState('1');
  const [law, setLaw] = useState(fixtures[0].law_identifier);
  const [editId, setEditId] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [caseData, setCaseData] = useState(null);
  const [records, setRecords] = useState([]);
  const [epochs, setEpochs] = useState([]);
  const [counts, setCounts] = useState(null);

  const read = useCallback(async (functionName, args = []) => {
    return parseStored(await readClient.readContract({
      address: contractAddress,
      functionName,
      args,
      transactionHashVariant: TransactionHashVariant.LATEST_FINAL
    }));
  }, []);

  const refresh = useCallback(async (requestedId = caseId) => {
    if (!addressOk) return;
    const id = Number(requestedId);
    const newCounts = await read('get_counts');
    setCounts(newCounts);
    if (!Number.isSafeInteger(id) || id < 1) {
      setCaseData(null); setRecords([]); setEpochs([]); return;
    }
    const currentCase = await read('get_case', [id]);
    setCaseData(currentCase);
    if (!currentCase) { setRecords([]); setEpochs([]); return; }
    const [newRecords, newEpochs] = await Promise.all([
      Promise.all(Array.from({ length: currentCase.record_count }, (_, i) => read('get_record', [id, i + 1]))),
      Promise.all(Array.from({ length: currentCase.epoch_count }, (_, i) => read('get_epoch', [id, i + 1])))
    ]);
    setRecords(newRecords.filter(Boolean));
    setEpochs(newEpochs.filter(Boolean).reverse());
  }, [caseId, read]);

  useEffect(() => { refresh().catch(error => setMessage(String(error))); }, [refresh]);
  useEffect(() => {
    if (!window.ethereum?.on) return;
    const changed = accounts => setWallet(accounts?.[0] || '');
    const chainChanged = chain => setWalletChainId(Number(chain));
    window.ethereum.on('accountsChanged', changed);
    window.ethereum.on('chainChanged', chainChanged);
    return () => {
      window.ethereum.removeListener?.('accountsChanged', changed);
      window.ethereum.removeListener?.('chainChanged', chainChanged);
    };
  }, []);

  async function connect() {
    try {
      if (!window.ethereum) throw new Error('Install or open an EIP-1193 wallet.');
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      if (!accounts?.[0]) throw new Error('No wallet account selected.');
      const client = createClient({ chain: studionet, account: accounts[0], provider: window.ethereum });
      await client.connect('studionet');
      const connectedChain = await window.ethereum.request({ method: 'eth_chainId' });
      setWalletChainId(Number(connectedChain));
      if (Number(connectedChain) !== 61999) throw new Error('Switch your wallet to Studionet (chain 61999).');
      setWallet(accounts[0]);
      setMessage('Wallet connected to Studionet.');
    } catch (error) { setMessage(String(error)); }
  }

  async function write(functionName, args) {
    if (!addressOk) { setMessage('Set VITE_CASEFLOW_ADDRESS to a verified Studionet deployment.'); return; }
    if (!wallet || walletChainId !== 61999) { setMessage('Connect a wallet on Studionet (chain 61999) first.'); return; }
    setBusy(true);
    try {
      const client = createClient({ chain: studionet, account: wallet, provider: window.ethereum });
      await client.connect('studionet');
      const currentChain = await window.ethereum.request({ method: 'eth_chainId' });
      if (Number(currentChain) !== 61999) throw new Error('Wallet is not on Studionet (chain 61999).');
      const call = { address: contractAddress, functionName, args };
      const hash = await client.writeContract({ ...call, value: 0n });
      setMessage(`${functionName} submitted: ${hash}. Waiting for finalization…`);
      const receipt = await client.waitForTransactionReceipt({
        hash, status: TransactionStatus.FINALIZED, interval: 5000, retries: 120
      });
      if (!isFinalSuccess(receipt)) {
        throw new Error(`${functionName} failed: ${failureReason(receipt)}. Transaction: ${hash}`);
      }
      setMessage(`${functionName} finalized: ${hash}`);
      if (functionName === 'create_case') {
        const createdId = returnedId(receipt);
        if (createdId) {
          setCaseId(String(createdId));
          await refresh(createdId);
        } else {
          setMessage(`Case created, but its ID was not present in the receipt. Transaction: ${hash}`);
          await refresh();
        }
      } else {
        await refresh();
      }
    } catch (error) { setMessage(String(error)); }
    finally { setBusy(false); }
  }

  const id = Number(caseId);
  const walletReady = Boolean(wallet && walletChainId === 61999);
  const selectedRecord = records.find(record => record.id === Number(editId));
  const canRevise = Boolean(walletReady && caseData?.status === 'OPEN' && selectedRecord &&
    selectedRecord.owner.toLowerCase() === wallet.toLowerCase());
  return <div className="page">
    <header className="topbar">
      <div className="brand"><span className="mark">C<span>.</span></span><span>CASEFLOW</span></div>
      <div className="network"><span className="dot" /> STUDIONET · 61999</div>
      <button className="wallet" onClick={connect}>{walletReady ? `${wallet.slice(0, 6)}…${wallet.slice(-4)}` : 'Connect wallet'}</button>
    </header>
    <main>
      <section className="hero">
        <p className="eyebrow">PUBLIC SOURCE / SHARED CASES / REVIEWABLE EPOCHS</p>
        <h1>Trace a law name<br/><em>to its source.</em></h1>
        <p className="lead">Register a law identifier in a shared case. After sealing, validators read one fixed DOJ page, and contract code checks whether that identifier appears in its verified scope.</p>
        <div className="notice"><strong>Scope check only.</strong> A result is not legal advice, a court decision, or a determination of guilt or legal applicability.</div>
      </section>

      <section className="workflow" aria-label="Case workflow">
        {['01 / OPEN A CASE', '02 / REGISTER TOGETHER', '03 / SEAL THE BATCH', '04 / ASSESS & READ'].map(x => <div key={x}>{x}</div>)}
      </section>

      {!addressOk && <div className="banner">No verified contract address is configured. Deploy to Studionet, then set <code>VITE_CASEFLOW_ADDRESS</code>.</div>}
      {wallet && !walletReady && <div className="banner">Your wallet is on a different network. Connect it to Studionet (chain 61999) to write.</div>}
      {message && <div className="banner" role="status">{message}</div>}

      <div className="grid">
        <section className="panel controls">
          <div className="sectionhead"><span>01</span><h2>Work the case</h2></div>
          <div className="fieldrow"><label>Case number<input type="number" min="1" value={caseId} onChange={e => setCaseId(e.target.value)} /></label><button onClick={() => refresh().catch(error => setMessage(String(error)))} disabled={busy || !addressOk}>Read</button></div>
          <button className="primary" disabled={busy || !addressOk || !walletReady} onClick={() => write('create_case', [])}>Create new case</button>
          <div className="divider" />
          <label>Law identifier<input value={law} onChange={e => setLaw(e.target.value)} maxLength="80" /></label>
          <div className="buttons"><button disabled={busy || !walletReady || !caseData || caseData.status !== 'OPEN'} onClick={() => write('register_record', [id, law])}>Register record</button><button disabled={busy || !canRevise} onClick={() => write('update_record', [id, selectedRecord.id, selectedRecord.revision, law])}>Revise own record</button></div>
          <label>Record number to revise<input type="number" min="1" value={editId} onChange={e => setEditId(e.target.value)} placeholder="Select your record" /></label>
          <div className="divider" />
          <div className="buttons"><button disabled={busy || !walletReady || !caseData || caseData.status !== 'OPEN' || caseData.record_count < 2 || caseData.creator.toLowerCase() !== wallet.toLowerCase()} onClick={() => write('seal_case', [id])}>Seal case</button><button disabled={busy || !walletReady || !caseData || caseData.status !== 'SEALED'} onClick={() => write('assess_epoch', [id, caseData.revision])}>Assess epoch</button></div>
          <p className="hint">Only the creator seals. Any connected wallet may register while open or assess after seal. At least two records are required.</p>
        </section>

        <section className="panel readout">
          <div className="sectionhead"><span>02</span><h2>Current state</h2></div>
          <div className="metrics"><div><small>CASES</small><b>{counts?.cases ?? '—'}</b></div><div><small>RECORDS</small><b>{counts?.records ?? '—'}</b></div><div><small>EPOCHS</small><b>{counts?.epochs ?? '—'}</b></div></div>
          {caseData ? <><div className="casehead"><div><small>CASE {caseData.id}</small><h3>{caseData.status}</h3></div><span>revision {caseData.revision}</span></div><p className="mono">Creator: {caseData.creator}</p><p className="mono">Last valid scope: {shortDigest(caseData.last_valid_scope_digest)}</p>
            <h3 className="subheading">Registered records</h3>
            {records.map(r => <article className="record" key={r.id}><div><b>#{r.id} {r.law_identifier}</b><span className={`tag ${r.status.toLowerCase()}`}>{r.status}</span></div><p>{r.reason}</p><small>Owner {r.owner} · revision {r.revision}</small></article>)}
          </> : <p className="empty">No case at this number yet. Create one or enter an existing case number.</p>}
        </section>
      </div>

      <div className="grid lower">
        <section className="panel">
          <div className="sectionhead"><span>03</span><h2>Reviewer identifiers</h2></div>
          <p className="hint">Use two or more wallets to register these in one case. These are page membership examples, not legal assessments.</p>
          {fixtures.map(f => <button className="fixture" key={f.label} onClick={() => setLaw(f.law_identifier)}><b>{f.label}</b><span>{f.law_identifier}</span><small>{f.note}</small></button>)}
        </section>
        <section className="panel">
          <div className="sectionhead"><span>04</span><h2>Assessment history</h2></div>
          {epochs.length ? epochs.map(e => <article className="epoch" key={e.id}><div><b>Epoch {e.id}</b><span className={`tag ${e.transition.toLowerCase()}`}>{e.transition}</span></div><p>Source digest <code>{shortDigest(e.source_digest)}</code><br/>Scope digest <code>{shortDigest(e.scope_digest)}</code></p><small>Case revision {e.case_revision} · {e.timestamp}</small><details><summary>Field diagnostics</summary><pre>{JSON.stringify(e.diagnostics, null, 2)}</pre></details></article>) : <p className="empty">Sealed cases show their append-only assessment trail here.</p>}
        </section>
      </div>
      <footer><span>CASEFLOW · SOURCE-BOUND CLASSIFICATION</span><a href={SOURCE_URL} target="_blank" rel="noreferrer">View the fixed DOJ page ↗</a></footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
