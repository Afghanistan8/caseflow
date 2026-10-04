"""Direct contract tests. Pytest discovers these unittest cases without a live Studio."""
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path


class FakePublic:
    @staticmethod
    def write(fn):
        return fn

    @staticmethod
    def view(fn):
        return fn


class FakeEquivalence:
    def __init__(self):
        self.result = None

    def prompt_comparative(self, callback, principle):
        if isinstance(self.result, Exception):
            raise self.result
        return callback() if self.result is None else self.result


def load_contract():
    runtime = types.ModuleType("genlayer")
    runtime.gl = types.SimpleNamespace(
        Contract=object,
        public=FakePublic,
        vm=types.SimpleNamespace(UserError=ValueError),
        message=types.SimpleNamespace(sender_address="0xA", chain_id=61999),
        message_raw={"datetime": "2026-10-04T00:00:00Z"},
        eq_principle=FakeEquivalence(),
        nondet=types.SimpleNamespace(
            web=types.SimpleNamespace(render=lambda *args, **kwargs: "DOJ page body" * 20),
            exec_prompt=lambda *args: "null",
        ),
    )
    runtime.TreeMap = dict
    runtime.u256 = int
    runtime.__all__ = ["gl", "TreeMap", "u256"]
    sys.modules["genlayer"] = runtime
    path = Path(__file__).resolve().parents[1] / "contracts" / "caseflow.py"
    spec = importlib.util.spec_from_file_location("caseflow", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaseflowTests(unittest.TestCase):
    def setUp(self):
        self.module = load_contract()
        self.gl = self.module.gl
        self.contract = self.module.Caseflow()

    def sender(self, value):
        self.gl.message.sender_address = value

    def sample_scope(self, laws=None):
        return {"correct_laws": laws or [
            "Title VII of the Civil Rights Act of 1964",
            "Pregnant Workers Fairness Act",
        ]}

    def agree(self, scope):
        self.gl.eq_principle.result = json.dumps({
            "available": True,
            "source_digest": "a" * 64,
            "scope": scope,
        })

    def make_sealed_case(self):
        case_id = self.contract.create_case()
        self.sender("0xB")
        self.contract.register_record(case_id, "Title VII of the Civil Rights Act of 1964")
        self.sender("0xC")
        self.contract.register_record(case_id, "Fair Housing Act")
        self.sender("0xA")
        self.contract.seal_case(case_id)
        return case_id

    def test_create_and_multi_wallet_registration(self):
        case_id = self.contract.create_case()
        self.sender("0xB")
        self.contract.register_record(case_id, "Pregnant Workers Fairness Act")
        self.sender("0xC")
        self.contract.register_record(case_id, "Fair Housing Act")
        case = json.loads(self.contract.get_case(case_id))
        self.assertEqual(case["record_count"], 2)
        self.assertEqual(json.loads(self.contract.get_record(case_id, 1))["owner"], "0xB")
        self.assertEqual(json.loads(self.contract.get_counts())["records"], 2)

    def test_only_creator_can_seal_and_two_records_required(self):
        case_id = self.contract.create_case()
        with self.assertRaisesRegex(ValueError, "two records"):
            self.contract.seal_case(case_id)
        self.sender("0xB")
        self.contract.register_record(case_id, "Title VII of the Civil Rights Act of 1964")
        self.sender("0xC")
        self.contract.register_record(case_id, "Fair Housing Act")
        with self.assertRaisesRegex(ValueError, "creator"):
            self.contract.seal_case(case_id)
        self.sender("0xA")
        self.contract.seal_case(case_id)
        with self.assertRaisesRegex(ValueError, "sealed"):
            self.contract.register_record(case_id, "Pregnant Workers Fairness Act")

    def test_owner_revision_conflict_and_seal_lock(self):
        case_id = self.contract.create_case()
        self.sender("0xB")
        self.contract.register_record(case_id, "Fair Housing Act")
        self.sender("0xC")
        with self.assertRaisesRegex(ValueError, "owner"):
            self.contract.update_record(case_id, 1, 0, "Pregnant Workers Fairness Act")
        self.sender("0xB")
        self.contract.update_record(case_id, 1, 0, "Pregnant Workers Fairness Act")
        with self.assertRaisesRegex(ValueError, "revision"):
            self.contract.update_record(case_id, 1, 0, "Fair Housing Act")
        self.sender("0xC")
        self.contract.register_record(case_id, "Fair Housing Act")
        self.sender("0xA")
        self.contract.seal_case(case_id)
        self.sender("0xB")
        with self.assertRaisesRegex(ValueError, "sealed"):
            self.contract.update_record(case_id, 1, 1, "Fair Housing Act")

    def test_deterministic_membership_and_revision_guard(self):
        case_id = self.make_sealed_case()
        case = json.loads(self.contract.get_case(case_id))
        self.agree(self.sample_scope())
        with self.assertRaisesRegex(ValueError, "revision"):
            self.contract.assess_epoch(case_id, case["revision"] - 1)
        self.sender("0xD")
        self.contract.assess_epoch(case_id, case["revision"])
        epoch = json.loads(self.contract.get_epoch(case_id, 1))
        self.assertEqual(epoch["transition"], "INITIAL")
        self.assertEqual(epoch["diagnostics"][0]["status"], "AFFECTED")
        self.assertEqual(epoch["diagnostics"][1]["status"], "NOT_AFFECTED")
        self.assertEqual(epoch["diagnostics"][1]["fields"], {"law": False})

    def test_unavailable_epoch_preserves_last_valid_digest(self):
        case_id = self.make_sealed_case()
        self.agree(self.sample_scope())
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        baseline = json.loads(self.contract.get_case(case_id))["last_valid_scope_digest"]
        self.gl.eq_principle.result = RuntimeError("consensus failed")
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 2))["transition"], "SOURCE_UNAVAILABLE")
        self.assertEqual(json.loads(self.contract.get_case(case_id))["last_valid_scope_digest"], baseline)
        self.assertEqual(json.loads(self.contract.get_record(case_id, 1))["status"], "SOURCE_UNAVAILABLE")

    def test_append_only_transitions(self):
        case_id = self.make_sealed_case()
        first = self.sample_scope()
        self.agree(first)
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        saved_first = self.contract.get_epoch(case_id, 1)
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 2))["transition"], "UNCHANGED")
        self.agree(self.sample_scope(["Pregnant Workers Fairness Act"]))
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 3))["transition"], "SCOPE_CHANGED")
        self.assertEqual(self.contract.get_epoch(case_id, 1), saved_first)
        self.assertEqual(json.loads(self.contract.get_counts())["epochs"], 3)

    def test_invalid_scope_is_unavailable_and_cannot_assign_guilt(self):
        case_id = self.make_sealed_case()
        self.agree({"correct_laws": ["Title VII"], "default_level": "HIGH"})
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 1))["transition"], "SOURCE_UNAVAILABLE")
        self.assertNotIn("default_level", json.loads(self.contract.get_record(case_id, 1)))

    def test_html_headings_define_scope_and_exclude_navigation(self):
        case_id = self.make_sealed_case()
        page = (
            "<h2>Utilities</h2><h1>Laws We Enforce</h1>"
            "<h2>Title VII of the Civil Rights Act of 1964</h2>"
            "<h2>Pregnant Workers Fairness Act</h2>"
            "<h2>The Uniformed Services Employment and Reemployment Rights Act "
            "of 1994&nbsp;(USERRA)</h2><h2>&nbsp;</h2><footer><h2>Contact</h2></footer>"
        )
        self.gl.nondet.web.render = lambda *args, **kwargs: page
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 1))["transition"], "INITIAL")
        self.assertEqual(json.loads(self.contract.get_record(case_id, 1))["status"], "AFFECTED")
        self.assertEqual(json.loads(self.contract.get_record(case_id, 2))["status"], "NOT_AFFECTED")
        self.assertEqual(len(self.module.scope_from_page(page)["correct_laws"]), 3)

        self.gl.nondet.web.render = lambda *args, **kwargs: page.replace(
            "<h1>Laws We Enforce</h1>", "<h1>Different page</h1>"
        )
        self.contract.assess_epoch(case_id, json.loads(self.contract.get_case(case_id))["revision"])
        self.assertEqual(json.loads(self.contract.get_epoch(case_id, 2))["transition"], "SOURCE_UNAVAILABLE")

    def test_wrong_chain_is_rejected(self):
        self.gl.message.chain_id = 1
        with self.assertRaisesRegex(ValueError, "Studionet"):
            self.module.Caseflow()


if __name__ == "__main__":
    unittest.main()
