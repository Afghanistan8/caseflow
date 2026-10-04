# Caseflow · Studionet evidence ledger

Fill this in only after transactions and readbacks have been observed on **Studionet (chain ID 61999)**. Keep wallet secrets out of this file.

| Checkpoint | Observed value |
| --- | --- |
| Contract address | `0x1562a4EC5C8331C27f5c0C9A3d744f5b087B267B` |
| Contract deployment transaction | `0x3a56d30f62be5c770c9a841311ca7890ba3566e601efa1083d638ea9cb73283c` · FINALIZED · execution SUCCESS |
| Explorer link | [Studionet transaction](https://explorer-studio.genlayer.com/tx/0x3a56d30f62be5c770c9a841311ca7890ba3566e601efa1083d638ea9cb73283c) |
| Contract code / source verification | Normalized SHA-256 `ac3fec08c0ce96c852dd83a0cf4810be8531259a1132c2ed9a3f6d551d46cc1f` for both on-chain code and `contracts/caseflow.py` |
| `get_protocol` readback | `{"admin":false,"chain_id":61999,"custody":false,"name":"Caseflow","source_id":"DOJ_CRT_LAWS_WE_ENFORCE","source_url":"https://www.justice.gov/crt/laws-we-enforce","version":"0.1.0"}` |
| `get_counts` readback after deployment | `{"cases":0,"epochs":0,"records":0}` |
| Deployer wallet (public address) | `0x4184bc5e5444f250767e8d33a49817a9b4fb0df3` |
| Creator wallet (public address) |  |
| Independent registering wallets (public addresses) |  |
| Case number |  |
| Create transaction |  |
| Record registration transactions |  |
| Seal transaction |  |
| Assessment transaction |  |
| Final case revision |  |
| Epoch number and transition |  |
| Source digest |  |
| Scope digest |  |
| Per-record status readbacks |  |
| Prior epoch readback after later assessment |  |
| Observation date and time (UTC) | 2026-10-04 01:56 UTC |

## Review notes

- Confirm each transaction reached finalization before copying the final readback.
- Confirm the creator and registering wallets are distinct where expected.
- If the page cannot be validated, record `SOURCE_UNAVAILABLE` and the actual error or receipt; do not substitute an expected verdict.
- A page membership result does not establish legal applicability, a violation, or guilt.
