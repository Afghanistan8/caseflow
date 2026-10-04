# Caseflow · verified Studionet run

Observed on 2026-10-04 UTC, chain ID `61999`. All listed transactions reached `FINALIZED` with `MAJORITY_AGREE` and successful leader execution. No wallet secrets are recorded here.

| Checkpoint | Observed value |
| --- | --- |
| Active contract | `0xcE9f13ED45AC3561659Beed43B7FD9dAfcf2A13E` |
| Deployment | [Transaction `0x0e1233…bd026f8`](https://explorer-studio.genlayer.com/tx/0x0e12338ab8ea1229b32437285f3f04e67725ee8253ee3bca66aff7c79bd026f8) |
| Code verification | Normalized SHA-256 `5327331e7721af533be5bd6a3f36bfae971b4182f29a96b1cf2ae7da78d19ccb` for both on-chain code and `contracts/caseflow.py` |
| Protocol | Caseflow `0.3.0`; DOJ Civil Rights Division source; no admin or custody; Studionet `61999` |
| Test wallet | `0x4184bc5e5444f250767e8d33a49817a9b4fb0df3` |
| Case creation | [Transaction `0x83bd0b…4b289a`](https://explorer-studio.genlayer.com/tx/0x83bd0bc854a739d473e594d67eb7a287ccbe6c78930099f9c94d98a7554b289a) → case `1` |
| Title VII registration | [Transaction `0xb43ea6…41d1c`](https://explorer-studio.genlayer.com/tx/0xb43ea64d3f3853f2f2d76712cd78260620e2f7f3937a6ad57b4c3ffaa7941d1c) → record `1` |
| Fair Housing Act registration | [Transaction `0x4a6a55…a4e7b`](https://explorer-studio.genlayer.com/tx/0x4a6a553a117278939321bbe1dd8f5a360900346ddb2010f389cc361fbaca4e7b) → record `2` |
| Seal | [Transaction `0x443ac3…a10b48`](https://explorer-studio.genlayer.com/tx/0x443ac3f67bbd18d120643f5fda851413ceec349a9d2f38f2e68f4f73caa10b48) → `SEALED`, revision `3` |
| Assessment | [Transaction `0xc04022…3a2b4`](https://explorer-studio.genlayer.com/tx/0xc04022c47785c51a33ffb78593cdc4481a39cc21ca56b1753b5424e23733a2b4) → epoch `1` |
| Final case readback | `SEALED`; revision `4`; 2 records; 1 epoch |
| Epoch transition | `INITIAL`; timestamp `2026-10-04T02:40:46.017018Z` |
| Source digest | `b96c8d6425d61527e072737bd9ba40e45809db3d4bf1eb63abb6d4fe486526d0` |
| Scope digest | `3bb0960074df85cba3012a872fddcf4eac8f2acf841e43714185e5a9970b5a15` |
| Record 1 readback | `AFFECTED`; `law: true` for `Title VII of the Civil Rights Act of 1964` |
| Record 2 readback | `NOT_AFFECTED`; `law: false` for `Fair Housing Act` on this one DOJ page |
| Final counters | `{"cases":1,"records":2,"epochs":1}` |

The test wallet owned both records. The direct contract tests cover distinct owners and owner-only revision, but a live multi-wallet flow has not been performed. `AFFECTED` is page membership only; it is not a legal finding.

## Corrections observed during the smoke test

- The first deployment, `0x1562a4EC5C8331C27f5c0C9A3d744f5b087B267B`, finalized an assessment as `SOURCE_UNAVAILABLE`; its model-based extraction did not return a verified scope. The exact failing validation stage is not exposed by that version. Its [assessment transaction](https://explorer-studio.genlayer.com/tx/0x9608e6dc93368176a82534ab3c52e221119b8d94605e9a82b354f4c34c14f789) remains public.
- The second deployment, `0xecB1cdC12DF7FF4Cd7f5A4011d8b7DBCE95de666`, extracted all three page headings in the leader result, but its [assessment transaction](https://explorer-studio.genlayer.com/tx/0x54f4d4a3869d42de87e3fa1ffdf3cc6f51f60745bc5f952a5d1b306d297f656e) finalized with `MAJORITY_DISAGREE`; no epoch was appended. That version compared a digest of the full rendered HTML. The active contract compares a canonical digest of the heading tuple, and its subsequent live assessment reached `MAJORITY_AGREE`.
