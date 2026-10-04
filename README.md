# Caseflow

**One public page. Many wallets. A permanent trail of source checks.**

Caseflow is a Studionet intelligent contract and React interface for checking whether a registered **law identifier is named on one fixed U.S. Department of Justice page**: [Civil Rights Division — Laws We Enforce](https://www.justice.gov/crt/laws-we-enforce). Validators compare a bounded list of headings from the live page, and contract code checks each registered identifier against that list.

**Live Studionet contract:** `0xcE9f13ED45AC3561659Beed43B7FD9dAfcf2A13E` · [deployment transaction](https://explorer-studio.genlayer.com/tx/0x0e12338ab8ea1229b32437285f3f04e67725ee8253ee3bca66aff7c79bd026f8). The finalized deployment source matches [`contracts/caseflow.py`](contracts/caseflow.py) after line-ending normalization. [`docs/LIVE_EVIDENCE.md`](docs/LIVE_EVIDENCE.md) contains the live case readbacks.

The outcome is a page membership classification. It is **not legal advice, a determination that a law applies to a person or event, a finding of a violation, or a determination of guilt**. DOJ's page does not publish lot codes, best-by dates, or severity levels, so Caseflow does not ask validators to invent them.

## Follow a case

```text
any wallet creates a case (OPEN)
    ↓
independent wallets register law identifiers; owners can revise their own records
    ↓
the creator seals after at least two records (SEALED)
    ↓
any wallet requests an assessment
    ↓
validators render the pinned DOJ page and compare the bounded law list
    ↓
contract code marks each record AFFECTED, NOT_AFFECTED, or SOURCE_UNAVAILABLE
    ↓
an immutable epoch is appended with digests, diagnostics, revision, and time
```

`AFFECTED` means the identifier appears in the verified list on that one page. `NOT_AFFECTED` means it does not appear in that list. Neither label evaluates a person's circumstances. `SOURCE_UNAVAILABLE` means a complete, agreed source list could not be established; it is not a negative result.

## The source boundary

The contract pins `https://www.justice.gov/crt/laws-we-enforce`. Callers cannot substitute a URL or upload a document. Inside the comparative equivalence callback, validators render the live HTML and extract the nonempty second-level headings that follow the page title. The source digest covers the canonical source ID and heading tuple, so incidental HTML differences do not split validator agreement. Contract code validates the bounded, unique list and computes record outcomes. A missing or changed page structure yields `SOURCE_UNAVAILABLE` and does not replace the last valid scope digest.

This design classifies **exact strings**. It does not resolve aliases, decide which statute governs an event, or claim the DOJ page is a complete list of all laws. A source page update may change the scope digest and create a `SCOPE_CHANGED` epoch after a later assessment.

## Reviewer walk-through

Use two or more Studio wallets. The three examples in the interface are tied to the pinned page as follows:

| Entry | Expected page membership | Why |
| --- | --- | --- |
| `Title VII of the Civil Rights Act of 1964` | Listed | Exact page heading |
| `Fair Housing Act` | Not listed on this specific page | Negative control; this says nothing about other DOJ pages |
| `Pregnant Workers Fairness Act` | Listed | Exact page heading |

Create a case with one wallet. Register at least two records from separate wallets. The creator seals the case. Any wallet can assess at the displayed case revision. Read the records and the newest epoch. A web or extraction failure can yield `SOURCE_UNAVAILABLE`. If validators reject the transaction with `MAJORITY_DISAGREE`, no epoch is appended and the case revision stays unchanged; the interface reports the failed transaction.

## Contract invariants

- **Studionet only:** chain ID `61999`; the constructor has no arguments.
- **No special wallet:** the deployer receives no admin, pause, upgrade, or reviewer method. All writes are nonpayable and the contract has no withdrawal path.
- **Ownership:** any wallet can create and register; only a record owner can revise it while open; only the case creator can seal it.
- **Concurrency:** record updates require the expected record revision; assessments require the expected case revision.
- **History:** every successful assessment call appends an epoch. Earlier epochs are never overwritten. A failed source epoch leaves the last valid scope digest intact.
- **Decision boundary:** only the contract's `intersect` function maps an agreed law-heading list to record status.

## Run and verify locally

Python 3.12+ and Node 20.19+ are recommended. From the repository root:

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
genvm-lint check contracts/caseflow.py
cd frontend
npm install
npm test
npm run build
```

The Python tests use a direct GenLayer stub so they run without a Studio node. They cover multi-wallet registration, creator-only sealing, owner revisions, revision conflicts, deterministic membership, unavailable source handling, and append-only transitions. A direct stub does not prove live validator equivalence; record a real Studionet run in [`docs/LIVE_EVIDENCE.md`](docs/LIVE_EVIDENCE.md).

## Deploy and connect

1. Open [GenLayer Studio](https://studio.genlayer.com/) and select **Studionet**, chain ID `61999`.
2. Run `cd frontend && npm install && npm run dev`. The verified deployment address is the default; `VITE_CASEFLOW_ADDRESS` can override it for another verified deployment.
3. Connect a Studionet wallet in the interface. Case creation, registration, sealing, and assessment each require a wallet transaction.
4. Record future case transaction hashes and readbacks in [`docs/LIVE_EVIDENCE.md`](docs/LIVE_EVIDENCE.md).

To verify this deployment from the repository root, run `cd frontend && npm run verify:deployment -- 0xcE9f13ED45AC3561659Beed43B7FD9dAfcf2A13E 0x0e12338ab8ea1229b32437285f3f04e67725ee8253ee3bca66aff7c79bd026f8`. Studionet fees are paid by the caller's wallet; the contract does not receive user value.

## Repository map

| Path | Purpose |
| --- | --- |
| `contracts/caseflow.py` | On-chain case lifecycle, source validation, and deterministic membership |
| `frontend/` | Wallet-driven case desk and epoch reader |
| `tests/test_caseflow.py` | Direct contract behavior checks |
| `docs/LIVE_EVIDENCE.md` | Finalized Studionet transactions and readbacks |

Caseflow deliberately keeps its source and classification rule narrow. A record's presence on the DOJ page is a verifiable reference check, not a legal judgment.
