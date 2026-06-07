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
                                    os.path.join(d, "final.mp4"), work_dir=d)
            rep = fb.qc_probe(cut.local_path, expected_duration_seconds=4.0)
            self.assertTrue(rep["passed"], rep)
            self.assertEqual(rep["resolution"], "1080x1920")
            self.assertEqual(rep["codec"], "h264")
            self.assertFalse(rep["official_publish_ready"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
