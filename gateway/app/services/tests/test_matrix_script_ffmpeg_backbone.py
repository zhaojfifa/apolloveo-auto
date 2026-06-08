"""Matrix Script ffmpeg backbone — Runtime PR-1 tests.

Gate Spec: docs/design/MATRIX_SCRIPT_FFMPEG_BACKBONE_RUNTIME_GATE_SPEC_20260607.md
(acceptance rows FB-1..FB-12). Pure tests assert deterministic command construction,
the QC verdict logic, operator-safe leakage rules, honest proxy semantics, and the
fallback path (via an injectable runner) — all without invoking ffmpeg. Integration
tests that actually run ffmpeg/ffprobe are skipped when they are not on PATH
(environment limitation, not a regression).
"""
from __future__ import annotations

import os
import tempfile
import unittest

from gateway.app.services.matrix_script import ffmpeg_backbone as fb


def _good_probe(width=1080, height=1920, codec="h264", rate="30/1", duration="3.0"):
    return {
        "streams": [{"codec_type": "video", "width": width, "height": height,
                     "codec_name": codec, "avg_frame_rate": rate, "duration": duration}],
        "format": {"duration": duration},
    }


class TestDeterministicCommands(unittest.TestCase):
    def test_kenburns_command_has_backbone_params(self):  # FB-1
        cmd = fb.build_kenburns_command("in.png", "out.mp4", duration_seconds=3.0, zoom=fb.ZOOM_IN)
        joined = " ".join(cmd)
        self.assertIn("1080x1920", joined)
        self.assertIn("fps=30", joined)
        self.assertIn(fb.BACKBONE_VENCODER, cmd)
        self.assertIn(fb.BACKBONE_PIX_FMT, cmd)
        self.assertIn(fb.BACKBONE_CRF, cmd)
        self.assertIn("zoompan", joined)
        self.assertIn("-an", cmd)  # backbone clips carry no audio

    def test_kenburns_deterministic_same_input_same_command(self):  # FB-1
        a = fb.build_kenburns_command("in.png", "out.mp4", duration_seconds=3.0, zoom=fb.ZOOM_IN)
        b = fb.build_kenburns_command("in.png", "out.mp4", duration_seconds=3.0, zoom=fb.ZOOM_IN)
        self.assertEqual(a, b)

    def test_zoom_in_vs_out_differ(self):
        zin = " ".join(fb.build_kenburns_command("i.png", "o.mp4", duration_seconds=3, zoom=fb.ZOOM_IN))
        zout = " ".join(fb.build_kenburns_command("i.png", "o.mp4", duration_seconds=3, zoom=fb.ZOOM_OUT))
        self.assertNotEqual(zin, zout)

    def test_bad_zoom_rejected(self):
        with self.assertRaises(fb.BackboneRenderError):
            fb.build_kenburns_command("i.png", "o.mp4", duration_seconds=3, zoom="sideways")

    def test_nonpositive_duration_rejected(self):
        with self.assertRaises(fb.BackboneRenderError):
            fb.build_kenburns_command("i.png", "o.mp4", duration_seconds=0, zoom=fb.ZOOM_IN)

    def test_compose_command_is_concat_copy(self):  # FB-4
        cmd = fb.build_compose_command("/tmp/concat.txt", "out.mp4")
        self.assertIn("concat", cmd)
        self.assertIn("copy", cmd)

    def test_static_still_command_has_no_zoompan(self):  # FB-7 fallback
        cmd = " ".join(fb.build_static_still_command("i.png", "o.mp4", duration_seconds=3))
        self.assertIn("1080x1920", cmd.replace(":", "x") or cmd)
        self.assertNotIn("zoompan", cmd)


class TestQcVerdict(unittest.TestCase):
    def test_qc_pass_on_good_probe(self):  # FB-6
        rep = fb.qc_report(_good_probe(), expected_duration_seconds=3.0)
        self.assertTrue(rep["passed"])
        self.assertTrue(all(rep["checks"].values()))

    def test_qc_fail_wrong_resolution(self):  # FB-6
        rep = fb.qc_report(_good_probe(width=720, height=1280))
        self.assertFalse(rep["passed"])
        self.assertFalse(rep["checks"]["resolution"])

    def test_qc_fail_wrong_codec(self):
        rep = fb.qc_report(_good_probe(codec="vp9"))
        self.assertFalse(rep["passed"])
        self.assertFalse(rep["checks"]["codec"])

    def test_qc_fail_wrong_fps(self):
        rep = fb.qc_report(_good_probe(rate="25/1"))
        self.assertFalse(rep["passed"])
        self.assertFalse(rep["checks"]["fps"])

    def test_qc_fail_duration_mismatch(self):
        rep = fb.qc_report(_good_probe(duration="3.0"), expected_duration_seconds=10.0)
        self.assertFalse(rep["passed"])
        self.assertFalse(rep["checks"]["duration_fit"])

    def test_qc_no_video_stream(self):
        rep = fb.qc_report({"streams": [], "format": {}})
        self.assertFalse(rep["passed"])

    def test_qc_pass_never_implies_publish_ready(self):  # FB-9
        rep = fb.qc_report(_good_probe(), expected_duration_seconds=3.0)
        self.assertFalse(rep["official_publish_ready"])

    def test_probe_media_parses_injected_json(self):
        import json as _json
        captured = {}

        def fake_capture(cmd):
            captured["cmd"] = cmd
            return _json.dumps(_good_probe()).encode("utf-8")

        data = fb.probe_media("x.mp4", runner_capture=fake_capture)
        self.assertEqual(data["streams"][0]["codec_name"], "h264")
        self.assertIn("ffprobe", captured["cmd"][0])


class TestHonestSemanticsAndLeakage(unittest.TestCase):
    def test_proxy_is_not_generative(self):  # FB-3 / §4 non-goal
        self.assertFalse(fb.IS_GENERATIVE)
        art = fb.ClipArtifact(kind="proxy_clip", local_path="/tmp/x.mp4", duration_seconds=3.0)
        self.assertFalse(art.is_generative)
        summary = art.operator_summary()
        self.assertFalse(summary["is_generative"])
        self.assertIn("非生成式", summary["operator_label"])

    def test_operator_summary_excludes_local_path(self):  # FB-8 leakage
        art = fb.ClipArtifact(kind="proxy_clip", local_path="/secret/internal/path.mp4",
                              duration_seconds=3.0)
        summary = art.operator_summary()
        blob = repr(summary)
        self.assertNotIn("local_path", summary)
        self.assertNotIn("/secret/internal/path.mp4", blob)

    def test_static_still_summary_label(self):
        art = fb.ClipArtifact(kind="proxy_clip", local_path="/tmp/x.mp4",
                              tier=fb.TIER_STATIC_STILL, duration_seconds=3.0)
        self.assertIn("静态画面", art.operator_summary()["operator_label"])

    def test_no_vendor_or_publish_ready_in_summaries(self):  # FB-8 / FB-9
        art = fb.ClipArtifact(kind="composed_cut", local_path="/tmp/c.mp4", duration_seconds=10.0)
        man = fb.BackboneManifest(shot_clips=(art,), composed_cut=art,
                                  qc=fb.qc_report(_good_probe(duration="10.0")))
        blob = repr(man.operator_summary()).lower()
        for forbidden in ("akool", "kling", "runway", "veo", "provider", "vendor",
                          "local_path", "official_publish_ready=true", "/tmp/"):
            self.assertNotIn(forbidden, blob)
        self.assertFalse(man.operator_summary()["official_publish_ready"])


class TestFallbackPath(unittest.TestCase):
    def test_generate_with_fallback_uses_static_on_proxy_failure(self):  # FB-7
        calls = []

        def flaky_runner(cmd):
            calls.append(cmd)
            joined = " ".join(cmd)
            if "zoompan" in joined:           # the proxy command → fail
                raise fb.BackboneRenderError("simulated proxy failure")
            # the static-still command → succeed
            open(cmd[-1], "wb").close()

        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "shot.mp4")
            art = fb.generate_with_fallback("in.png", out, duration_seconds=3.0,
                                            zoom=fb.ZOOM_IN, runner=flaky_runner)
        self.assertEqual(art.tier, fb.TIER_STATIC_STILL)
        self.assertGreaterEqual(len(calls), 2)  # proxy attempt + fallback

    def test_proxy_success_keeps_proxy_tier(self):
        def ok_runner(cmd):
            open(cmd[-1], "wb").close()

        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "shot.mp4")
            art = fb.generate_with_fallback("in.png", out, duration_seconds=3.0, runner=ok_runner)
        self.assertEqual(art.tier, fb.TIER_PROXY)

    def test_compose_requires_clips(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fb.BackboneRenderError):
                fb.compose_concat([], os.path.join(d, "out.mp4"), work_dir=d, runner=lambda c: None)

    def test_compose_writes_concat_list(self):  # FB-4
        seen = {}

        def runner(cmd):
            seen["cmd"] = cmd

        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "final.mp4")
            fb.compose_concat([os.path.join(d, "a.mp4"), os.path.join(d, "b.mp4")],
                              out, work_dir=d, runner=runner)
            concat = os.path.join(d, "concat.txt")
            self.assertTrue(os.path.exists(concat))
            body = open(concat, encoding="utf-8").read()
            self.assertIn("a.mp4", body)
            self.assertIn("b.mp4", body)

    def test_compose_populates_duration_from_input_durations(self):  # FB-4 evidence accuracy
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "final.mp4")
            cut = fb.compose_concat([os.path.join(d, "a.mp4"), os.path.join(d, "b.mp4")],
                                    out, work_dir=d, clip_durations=[3.0, 2.0],
                                    runner=lambda c: None)
            self.assertEqual(cut.duration_seconds, 5.0)
            self.assertEqual(cut.operator_summary()["duration_seconds"], 5.0)

    def test_compose_duration_defaults_zero_without_durations(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "final.mp4")
            cut = fb.compose_concat([os.path.join(d, "a.mp4")], out, work_dir=d, runner=lambda c: None)
            self.assertEqual(cut.duration_seconds, 0.0)

    def test_compose_duration_length_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fb.BackboneRenderError):
                fb.compose_concat([os.path.join(d, "a.mp4"), os.path.join(d, "b.mp4")],
                                  os.path.join(d, "o.mp4"), work_dir=d,
                                  clip_durations=[3.0], runner=lambda c: None)


class TestTargetedRegenerate(unittest.TestCase):
    """PR-2 targeted-regenerate orchestration (injected runner; no ffmpeg)."""

    def _shots(self):
        return [
            fb.ShotSpec("shot01", "a.png", duration_seconds=2.0, zoom=fb.ZOOM_IN),
            fb.ShotSpec("shot02", "b.png", duration_seconds=3.0, zoom=fb.ZOOM_OUT),
            fb.ShotSpec("shot03", "c.png", duration_seconds=2.0, zoom=fb.ZOOM_IN),
        ]

    def _runner(self, calls):
        def run(cmd):
            calls.append(cmd)
            open(cmd[-1], "wb").close()  # create the declared output file
        return run

    def test_only_changed_shots_regenerated_others_reused(self):  # FB-5
        calls = []
        with tempfile.TemporaryDirectory() as d:
            existing = {"shot01": os.path.join(d, "old01.mp4"),
                        "shot02": os.path.join(d, "old02.mp4"),
                        "shot03": os.path.join(d, "old03.mp4")}
            durations = {"shot01": 2.0, "shot02": 3.0, "shot03": 2.0}
            res = fb.targeted_regenerate(self._shots(), os.path.join(d, "final.mp4"),
                                         work_dir=d, changed_shot_ids={"shot02"},
                                         existing_clips=existing, existing_durations=durations,
                                         runner=self._runner(calls))
        self.assertEqual(res.regenerated_ids(), ["shot02"])
        self.assertEqual(sorted(res.reused_ids()), ["shot01", "shot03"])

    def test_reused_clip_paths_point_to_existing(self):  # FB-5 reuse
        with tempfile.TemporaryDirectory() as d:
            existing = {"shot01": os.path.join(d, "old01.mp4")}
            res = fb.targeted_regenerate(self._shots(), os.path.join(d, "final.mp4"),
                                         work_dir=d, changed_shot_ids=set(),
                                         existing_clips=existing, runner=self._runner([]))
        reused = next(r for r in res.shot_results if r.shot_id == "shot01")
        self.assertEqual(reused.action, fb.ACTION_REUSED)
        self.assertTrue(reused.clip.local_path.endswith("old01.mp4"))
        # shots without an existing clip must be regenerated, not reused
        self.assertEqual([r.shot_id for r in res.shot_results if r.action == fb.ACTION_REGENERATED],
                         ["shot02", "shot03"])

    def test_no_existing_clips_regenerates_all(self):
        with tempfile.TemporaryDirectory() as d:
            res = fb.targeted_regenerate(self._shots(), os.path.join(d, "final.mp4"),
                                         work_dir=d, changed_shot_ids=set(), runner=self._runner([]))
        self.assertEqual(sorted(res.regenerated_ids()), ["shot01", "shot02", "shot03"])
        self.assertEqual(res.reused_ids(), [])

    def test_composed_duration_is_sum_of_all_shots(self):  # FB-4 + FB-5
        with tempfile.TemporaryDirectory() as d:
            existing = {s.shot_id: os.path.join(d, f"old_{s.shot_id}.mp4") for s in self._shots()}
            durations = {"shot01": 2.0, "shot02": 3.0, "shot03": 2.0}
            res = fb.targeted_regenerate(self._shots(), os.path.join(d, "final.mp4"),
                                         work_dir=d, changed_shot_ids={"shot02"},
                                         existing_clips=existing, existing_durations=durations,
                                         runner=self._runner([]))
        self.assertEqual(res.composed_cut.duration_seconds, 7.0)  # 2+3+2

    def test_operator_summary_is_leakage_safe(self):  # FB-8
        with tempfile.TemporaryDirectory() as d:
            existing = {"shot01": "/internal/secret/old01.mp4"}
            res = fb.targeted_regenerate(self._shots(), os.path.join(d, "final.mp4"),
                                         work_dir=d, changed_shot_ids=set(),
                                         existing_clips=existing, runner=self._runner([]))
            blob = repr(res.operator_summary()).lower()
        for forbidden in ("local_path", "/internal/secret", "/tmp/", "provider", "vendor",
                          "akool", "official_publish_ready=true"):
            self.assertNotIn(forbidden, blob)
        self.assertFalse(res.operator_summary()["official_publish_ready"])

    def test_empty_shots_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(fb.BackboneRenderError):
                fb.targeted_regenerate([], os.path.join(d, "o.mp4"), work_dir=d,
                                       changed_shot_ids=set(), runner=self._runner([]))

    def test_fallback_preserved_in_regeneration(self):  # FB-7 within PR-2
        def flaky(cmd):
            if "zoompan" in " ".join(cmd):
                raise fb.BackboneRenderError("proxy fail")
            open(cmd[-1], "wb").close()

        with tempfile.TemporaryDirectory() as d:
            res = fb.targeted_regenerate([fb.ShotSpec("shot01", "a.png", duration_seconds=2.0)],
                                         os.path.join(d, "final.mp4"), work_dir=d,
                                         changed_shot_ids={"shot01"}, runner=flaky)
        regen = res.shot_results[0]
        self.assertEqual(regen.action, fb.ACTION_REGENERATED)
        self.assertEqual(regen.clip.tier, fb.TIER_STATIC_STILL)


@unittest.skipUnless(fb.ffmpeg_available(), "ffmpeg/ffprobe not on PATH (environment limitation)")
class TestRealFfmpegIntegration(unittest.TestCase):
    """Real end-to-end ffmpeg trial — skipped when ffmpeg is absent."""

    def _make_still(self, d):
        still = os.path.join(d, "still.png")
        fb._run([fb.ffmpeg_path(), "-y", "-f", "lavfi", "-i",
                 "color=c=red:s=941x1672:d=1", "-frames:v", "1", still])
        return still

    def test_proxy_compose_qc_end_to_end(self):  # FB-1/FB-4/FB-6
        with tempfile.TemporaryDirectory() as d:
            still = self._make_still(d)
            c1 = fb.generate_kenburns_proxy(still, os.path.join(d, "s1.mp4"),
                                            duration_seconds=2.0, zoom=fb.ZOOM_IN)
            c2 = fb.generate_kenburns_proxy(still, os.path.join(d, "s2.mp4"),
                                            duration_seconds=2.0, zoom=fb.ZOOM_OUT)
            self.assertEqual(fb.qc_probe(c1.local_path, expected_duration_seconds=2.0)["passed"], True)
            cut = fb.compose_concat([c1.local_path, c2.local_path],
                                    os.path.join(d, "final.mp4"), work_dir=d,
                                    clip_durations=[c1.duration_seconds, c2.duration_seconds])
            rep = fb.qc_probe(cut.local_path, expected_duration_seconds=4.0)
            self.assertTrue(rep["passed"], rep)
            self.assertEqual(rep["resolution"], "1080x1920")
            self.assertEqual(rep["codec"], "h264")
            self.assertFalse(rep["official_publish_ready"])
            # descriptor duration now matches the authoritative QC duration (the fix)
            self.assertEqual(cut.duration_seconds, 4.0)
            self.assertEqual(cut.operator_summary()["duration_seconds"], rep["duration_seconds"])

    def test_targeted_regenerate_end_to_end(self):  # FB-5 real ffmpeg
        with tempfile.TemporaryDirectory() as d:
            still = self._make_still(d)
            shots = [fb.ShotSpec("shot01", still, duration_seconds=2.0, zoom=fb.ZOOM_IN),
                     fb.ShotSpec("shot02", still, duration_seconds=2.0, zoom=fb.ZOOM_OUT)]
            # Round 1: no existing clips -> both regenerated.
            r1 = fb.targeted_regenerate(shots, os.path.join(d, "final1.mp4"), work_dir=d,
                                        changed_shot_ids=set())
            self.assertEqual(sorted(r1.regenerated_ids()), ["shot01", "shot02"])
            existing = {r.shot_id: r.clip.local_path for r in r1.shot_results}
            durations = {r.shot_id: r.clip.duration_seconds for r in r1.shot_results}
            # Round 2: only shot02 changed -> shot01 reused, shot02 regenerated.
            r2 = fb.targeted_regenerate(shots, os.path.join(d, "final2.mp4"), work_dir=d,
                                        changed_shot_ids={"shot02"},
                                        existing_clips=existing, existing_durations=durations)
            self.assertEqual(r2.regenerated_ids(), ["shot02"])
            self.assertEqual(r2.reused_ids(), ["shot01"])
            rep = fb.qc_probe(r2.composed_cut.local_path, expected_duration_seconds=4.0)
            self.assertTrue(rep["passed"], rep)
            self.assertEqual(r2.composed_cut.duration_seconds, rep["duration_seconds"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
