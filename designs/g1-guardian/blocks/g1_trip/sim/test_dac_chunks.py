"""Driver regressions with synthetic leaf records; these do not run a simulator."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch


class ChunkAggregation(unittest.TestCase):
    def exercise(self, kind="normal", workers=1, code_range=None):
        driver = Path(__file__).with_name("run_dac_chunks.py")
        with tempfile.TemporaryDirectory() as temporary:
            sim = Path(temporary)
            (sim / "qualification").mkdir()
            copied = sim / driver.name
            copied.write_text(driver.read_text())

            def fake_leaf(command, **kwargs):
                args = dict(zip(command[2::2], command[3::2]))
                # Boolean leaf options interrupt key/value pairing; only the
                # arguments below precede those options.
                leaf = args["--run-id"]
                codes = list(map(int, args["--codes"].split(",")))
                temp = float(args["--temps"])
                rows = [[0, temp, code, .5 + .001 * code,
                         .51 + .001 * code, 1.04, 1.5, -.001]
                        for code in codes]
                if kind == "flat":
                    for row in rows:
                        row[3] = .5
                if kind == "return_drift" and "-t2-" in leaf:
                    for row in rows:
                        row[3] += 1e-6
                if kind == "wrong_code":
                    rows[0][2] = 255
                destination = sim / "qualification" / leaf
                destination.mkdir()
                provenance = {key: "synthetic" for key in
                              ["source_hashes", "model_hashes", "image_id",
                               "pdk_commit", "ngspice", "solver"]}
                (destination / "provenance.json").write_text(json.dumps(provenance))
                result = {"status": "passed", "rows": rows,
                          "fingerprints": [[["synthetic", "0"]] * 31],
                          "frozen_fingerprints": True, "wall_s": 0}
                (destination / "summary.json").write_text(json.dumps([result]))
                return type("Result", (), {"returncode": 0})()

            active = [0, 0]
            def fake_process(command, **kwargs):
                fake_leaf(command, **kwargs)
                active[0] += 1
                active[1] = max(active)
                class Process:
                    def wait(self):
                        active[0] -= 1
                        return 0
                return Process()
            argv = [str(copied), "--run-id", "fixture", "--image-id", "synthetic",
                    "--temps", "25,125,25", "--chunk-size", "16", "--workers", str(workers), "--tight"]
            if code_range:
                argv += ['--code-start', str(code_range[0]), '--code-stop', str(code_range[1])]
            with patch.object(sys, "argv", argv), patch("subprocess.run", fake_leaf), patch("subprocess.Popen", fake_process):
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(str(copied), run_name="__main__")
                except SystemExit as exception:
                    self.assertEqual(exception.code, 1)
            self.assertEqual(active[0], 0)
            self.assertLessEqual(active[1], workers)
            return json.loads((sim / "qualification/fixture/summary.json").read_text())

    def test_repeated_temperature_keeps_three_independent_sweeps(self):
        result = self.exercise()
        self.assertEqual(len(result["rows"]), 768)
        self.assertEqual([x["temperature_index"] for x in result["transfer"]],
                         [0, 0, 1, 1, 2, 2])
        self.assertEqual(result["return_temperature_status"], "passed")
        self.assertEqual(result["monotonicity_status"], "passed")

    def test_flat_transfer_is_an_electrical_failure_not_a_division_error(self):
        result = self.exercise("flat")
        self.assertEqual(result["status"], "passed numerical/all-code completion")
        self.assertEqual(result["monotonicity_status"], "failed")
        self.assertIsNone(result["transfer"][0]["min_DNL_LSB"])

    def test_changed_return_temperature_is_reported(self):
        result = self.exercise("return_drift")
        self.assertEqual(result["return_temperature_status"], "failed")

    def test_mislabeled_code_cannot_be_counted_as_complete(self):
        result = self.exercise("wrong_code")
        self.assertEqual(result["status"], "failed/incomplete")
        self.assertEqual(result["leaves"][0]["row_contract_status"], "failed")

    def test_three_worker_batches_keep_all_three_temperature_sweeps(self):
        result = self.exercise(workers=3)
        self.assertEqual(len(result['rows']), 768)
        self.assertEqual(result['return_temperature_status'], 'passed')

    def test_parallel_failure_finishes_started_group_without_claiming_transfer(self):
        result = self.exercise('wrong_code', workers=3)
        self.assertEqual(result['status'], 'failed/incomplete')
        self.assertEqual(result['transfer'], [])

    def test_nonzero_partial_range_groups_and_last_short_leaf(self):
        result = self.exercise(workers=4, code_range=(172, 255))
        self.assertEqual(result['status'], 'passed numerical/declared-code completion')
        self.assertEqual(result['code_range_half_open'], [172, 255])
        self.assertEqual(len(result['rows']), 3 * 83)
        self.assertEqual(result['return_temperature_status'], 'passed')
        self.assertAlmostEqual(result['transfer'][0]['endpoint_lsb_V'], .001)


if __name__ == "__main__":
    unittest.main()
