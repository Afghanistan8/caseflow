# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *

import hashlib
import html
import json
import re


SOURCE_URL = "https://www.justice.gov/crt/laws-we-enforce"
SOURCE_ID = "DOJ_CRT_LAWS_WE_ENFORCE"
MAX_PAGE_LENGTH = 120000
MAX_RECORDS_PER_CASE = 50


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate_scope(raw: object) -> dict:
    if not isinstance(raw, dict) or set(raw) != {"correct_laws"}:
        raise gl.vm.UserError("scope schema")
    laws = raw["correct_laws"]
    if not isinstance(laws, list) or not laws or len(laws) > 30:
        raise gl.vm.UserError("laws")
    if any(not isinstance(x, str) or not 1 <= len(x) <= 80 for x in laws):
        raise gl.vm.UserError("law identifier")
    if len(set(laws)) != len(laws):
        raise gl.vm.UserError("duplicate scope field")
    return {"correct_laws": sorted(laws)}


def scope_from_page(page: str) -> dict:
    title = re.search(r"<h1\b[^>]*>(.*?)</h1>", page, re.I | re.S)
    if not title or html.unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() != "Laws We Enforce":
        raise gl.vm.UserError("source title")
    body = page[title.end():].split("<footer", 1)[0]
    headings = []
    for match in re.finditer(r"<h2\b[^>]*>(.*?)</h2>", body, re.I | re.S):
        name = " ".join(html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).split())
        if name:
            headings.append(name)
    return validate_scope({"correct_laws": headings})


def intersect(record: dict, scope: dict) -> dict:
    fields = {"law": record["law_identifier"] in scope["correct_laws"]}
    affected = all(fields.values())
    return {
        "status": "AFFECTED" if affected else "NOT_AFFECTED",
        "reason": "The identifier is listed on the DOJ page." if affected else
                  "The identifier is not listed on the DOJ page.",
        "fields": fields,
    }


class Caseflow(gl.Contract):
    case_count: u256
    record_count: u256
    epoch_count: u256
    cases: TreeMap[str, str]
    records: TreeMap[str, str]
    epochs: TreeMap[str, str]

    def __init__(self):
        if int(gl.message.chain_id) != 61999:
            raise gl.vm.UserError("Studionet chain required")
        self.case_count = u256(0)
        self.record_count = u256(0)
        self.epoch_count = u256(0)
        self.cases = TreeMap()
        self.records = TreeMap()
        self.epochs = TreeMap()

    def _case(self, case_id: int) -> dict:
        raw = self.cases.get(str(case_id), "")
        if not raw:
            raise gl.vm.UserError("case not found")
        return json.loads(raw)

    def _record(self, case_id: int, record_id: int) -> dict:
        raw = self.records.get(f"{case_id}:{record_id}", "")
        if not raw:
            raise gl.vm.UserError("record not found")
        return json.loads(raw)

    @gl.public.write
    def create_case(self) -> int:
        self.case_count += 1
        case_id = int(self.case_count)
        item = {
            "id": case_id, "creator": str(gl.message.sender_address),
            "status": "OPEN", "revision": 0, "record_count": 0,
            "epoch_count": 0, "last_valid_scope_digest": "",
            "created_at": gl.message_raw["datetime"],
        }
        self.cases[str(case_id)] = canonical(item)
        return case_id

    @gl.public.write
    def register_record(self, case_id: int, law_identifier: str) -> int:
        case = self._case(case_id)
        if case["status"] != "OPEN":
            raise gl.vm.UserError("case is sealed")
        if case["record_count"] >= MAX_RECORDS_PER_CASE:
            raise gl.vm.UserError("case is full")
        self._check_record_fields(law_identifier)
        case["record_count"] += 1
        case["revision"] += 1
        self.record_count += 1
        record_id = case["record_count"]
        record = {
            "id": record_id, "case_id": case_id, "owner": str(gl.message.sender_address),
            "law_identifier": law_identifier,
            "revision": 0, "status": "PENDING", "reason": "Awaiting assessment.",
        }
        self.records[f"{case_id}:{record_id}"] = canonical(record)
        self.cases[str(case_id)] = canonical(case)
        return record_id

    def _check_record_fields(self, law: str) -> None:
        if not isinstance(law, str) or not 1 <= len(law) <= 80:
            raise gl.vm.UserError("law identifier")

    @gl.public.write
    def update_record(self, case_id: int, record_id: int, expected_revision: int,
                      law_identifier: str) -> None:
        case = self._case(case_id)
        record = self._record(case_id, record_id)
        if case["status"] != "OPEN":
            raise gl.vm.UserError("case is sealed")
        if record["owner"] != str(gl.message.sender_address):
            raise gl.vm.UserError("not record owner")
        if record["revision"] != expected_revision:
            raise gl.vm.UserError("record revision conflict")
        self._check_record_fields(law_identifier)
        record.update({
            "law_identifier": law_identifier,
            "revision": record["revision"] + 1,
        })
        case["revision"] += 1
        self.records[f"{case_id}:{record_id}"] = canonical(record)
        self.cases[str(case_id)] = canonical(case)

    @gl.public.write
    def seal_case(self, case_id: int) -> None:
        case = self._case(case_id)
        if case["status"] != "OPEN":
            raise gl.vm.UserError("case is sealed")
        if case["creator"] != str(gl.message.sender_address):
            raise gl.vm.UserError("not case creator")
        if case["record_count"] < 2:
            raise gl.vm.UserError("at least two records required")
        case["status"] = "SEALED"
        case["revision"] += 1
        self.cases[str(case_id)] = canonical(case)

    @gl.public.write
    def assess_epoch(self, case_id: int, expected_revision: int) -> int:
        case = self._case(case_id)
        if case["status"] != "SEALED":
            raise gl.vm.UserError("case is not sealed")
        if case["revision"] != expected_revision:
            raise gl.vm.UserError("case revision conflict")

        def fetch_scope() -> str:
            page_digest = ""
            try:
                page = gl.nondet.web.render(SOURCE_URL, mode="html")
                if not isinstance(page, str) or not 100 <= len(page) <= MAX_PAGE_LENGTH:
                    return canonical({"available": False, "source_digest": "", "scope": None})
                scope = scope_from_page(page)
                page_digest = digest(canonical({"source_id": SOURCE_ID, "headings": scope["correct_laws"]}))
                return canonical({"available": True, "source_digest": page_digest, "scope": scope})
            except Exception:
                return canonical({"available": False, "source_digest": page_digest, "scope": None})

        try:
            agreed = gl.eq_principle.prompt_comparative(
                fetch_scope,
                "Agree only when availability, source digest, and the exact sorted law "
                "identifiers are the same. Reject ambiguous or missing facts.",
            )
            envelope = json.loads(agreed)
            if not isinstance(envelope, dict) or set(envelope) != {"available", "source_digest", "scope"}:
                raise gl.vm.UserError("consensus schema")
            if type(envelope["available"]) is not bool:
                raise gl.vm.UserError("availability")
            if envelope["available"]:
                if not re.fullmatch(r"[0-9a-f]{64}", envelope["source_digest"]):
                    raise gl.vm.UserError("source digest")
                scope = validate_scope(envelope["scope"])
            else:
                scope = None
        except Exception:
            envelope = {"available": False, "source_digest": "", "scope": None}
            scope = None

        scope_digest = digest(canonical(scope)) if scope is not None else ""
        if scope is None:
            transition = "SOURCE_UNAVAILABLE"
        elif not case["last_valid_scope_digest"]:
            transition = "INITIAL"
        elif case["last_valid_scope_digest"] == scope_digest:
            transition = "UNCHANGED"
        else:
            transition = "SCOPE_CHANGED"
        diagnostics = []
        for record_id in range(1, case["record_count"] + 1):
            record = self._record(case_id, record_id)
            result = intersect(record, scope) if scope is not None else {
                "status": "SOURCE_UNAVAILABLE", "reason": "The fixed source did not yield a verified complete scope.",
                "fields": {"law": False},
            }
            record["status"] = result["status"]
            record["reason"] = result["reason"]
            self.records[f"{case_id}:{record_id}"] = canonical(record)
            diagnostics.append({"record_id": record_id, **result})
        if scope is not None:
            case["last_valid_scope_digest"] = scope_digest
        case["epoch_count"] += 1
        case["revision"] += 1
        self.epoch_count += 1
        epoch_id = case["epoch_count"]
        epoch = {
            "id": epoch_id, "case_id": case_id,
            "source_digest": envelope["source_digest"], "scope_digest": scope_digest,
            "transition": transition,
            "diagnostics": diagnostics, "case_revision": case["revision"],
            "timestamp": gl.message_raw["datetime"],
        }
        self.epochs[f"{case_id}:{epoch_id}"] = canonical(epoch)
        self.cases[str(case_id)] = canonical(case)
        return epoch_id

    @gl.public.view
    def get_case(self, case_id: int) -> str:
        return self.cases.get(str(case_id), "")

    @gl.public.view
    def get_record(self, case_id: int, record_id: int) -> str:
        return self.records.get(f"{case_id}:{record_id}", "")

    @gl.public.view
    def get_epoch(self, case_id: int, epoch_id: int) -> str:
        return self.epochs.get(f"{case_id}:{epoch_id}", "")

    @gl.public.view
    def get_counts(self) -> str:
        return canonical({"cases": int(self.case_count), "records": int(self.record_count),
                          "epochs": int(self.epoch_count)})

    @gl.public.view
    def get_protocol(self) -> str:
        return canonical({"name": "Caseflow", "version": "0.3.0", "chain_id": 61999,
                          "source_id": SOURCE_ID, "source_url": SOURCE_URL,
                          "admin": False, "custody": False})
