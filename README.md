# Caseflow

**One public page. Many wallets. A permanent trail of source checks.**

Caseflow is a Studionet intelligent contract and React interface for checking whether a registered **law identifier is named on one fixed U.S. Department of Justice page**: [Civil Rights Division — Laws We Enforce](https://www.justice.gov/crt/laws-we-enforce). An intelligent contract agent reads the page, validators compare the bounded list of law names, and deterministic contract code checks each registered identifier against that list.

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

The contract pins `https://www.justice.gov/crt/laws-we-enforce`. Callers cannot substitute a URL or upload a document. The web render and extraction prompt execute only inside the comparative equivalence callback. The model returns a list of law identifiers and verbatim page evidence. The callback checks the evidence against the rendered text; deterministic code validates the returned schema and computes record outcomes. An unavailable result does not replace the last valid scope digest.

This design classifies **exact strings**. It does not resolve aliases, decide which statute governs an event, or claim the DOJ page is a complete list of all laws. A source page update may change the scope digest and create a `SCOPE_CHANGED` epoch after a later assessment.

## Reviewer walk-through

Use two or more Studio wallets. The three examples in the interface are tied to the pinned page as follows:

| Entry | Expected page membership | Why |
| --- | --- | --- |
| `Title VII of the Civil Rights Act of 1964` | Listed | Exact page heading |
| `Fair Housing Act` | Not listed on this specific page | Negative control; this says nothing about other DOJ pages |
| `Pregnant Workers Fairness Act` | Listed | Exact page heading |

Create a case with one wallet. Register at least two records from separate wallets. The creator seals the case. Any wallet can assess at the displayed case revision. Read the records and the newest epoch. A web, extraction, or consensus failure can yield `SOURCE_UNAVAILABLE`, so the listed outcomes are expectations contingent on successful source validation.

## Contract invariants

- **Studionet only:** chain ID `61999`; the constructor has no arguments.
- **No special wallet:** the deployer receives no admin, pause, upgrade, or reviewer method. All writes are nonpayable and the contract has no withdrawal path.
- **Ownership:** any wallet can create and register; only a record owner can revise it while open; only the case creator can seal it.
- **Concurrency:** record updates require the expected record revision; assessments require the expected case revision.
- **History:** every successful assessment call appends an epoch. Earlier epochs are never overwritten. A failed source epoch leaves the last valid scope digest intact.
- **Decision boundary:** model output cannot set a record verdict. Only the contract's `intersect` function maps a validated law list to record status.

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
2. Deploy [`contracts/caseflow.py`](contracts/caseflow.py) with its no-argument constructor using your own Studio wallet. Verify the resulting contract code and address in Studio.
3. Copy `frontend/.env.example` to `frontend/.env` and place the **verified** address in `VITE_CASEFLOW_ADDRESS`.
4. Run `cd frontend && npm install && npm run dev`. Connect a Studionet wallet in the interface.
5. Record the real deployment and case transaction hashes in [`docs/LIVE_EVIDENCE.md`](docs/LIVE_EVIDENCE.md).

No deployment address is included here because none has been verified. Studionet fees are paid by the caller's wallet; the contract does not receive user value.

## Repository map

| Path | Purpose |
| --- | --- |
| `contracts/caseflow.py` | On-chain case lifecycle, source validation, and deterministic membership |
| `frontend/` | Wallet-driven case desk and epoch reader |
| `tests/test_caseflow.py` | Direct contract behavior checks |
| `docs/LIVE_EVIDENCE.md` | Fill-in ledger for a real Studionet review |

Caseflow deliberately keeps its source and classification rule narrow. A record's presence on the DOJ page is a verifiable reference check, not a legal judgment.
