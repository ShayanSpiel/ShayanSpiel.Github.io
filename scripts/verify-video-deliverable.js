#!/usr/bin/env node
/** Verify one final campaign Short and write its machine-readable QA report. */

import { createHash } from "crypto";
import { existsSync, readFileSync, writeFileSync } from "fs";
import { basename, dirname, join, resolve } from "path";
import { spawnSync } from "child_process";
import { fileURLToPath } from "url";

const ROOT = resolve(fileURLToPath(new URL("..", import.meta.url)));
const AUDIO_ROOT = join(ROOT, "public/videos/audio");
const VOICE_MANIFEST = join(AUDIO_ROOT, ".voice-manifest.json");
const NARRATION = join(ROOT, ".agents/company/departments/design/templates/video/narration.json");

function run(command, args) {
  const result = spawnSync(command, args, { encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  if (result.status !== 0) throw new Error(`${command} failed: ${(result.stderr || result.stdout).trim()}`);
  return `${result.stdout || ""}${result.stderr || ""}`;
}

function probe(path) {
  return JSON.parse(run("ffprobe", ["-v", "error", "-show_streams", "-show_format", "-of", "json", path]));
}

function ratio(value) {
  const [a, b] = String(value || "0/1").split("/").map(Number);
  return b ? a / b : 0;
}

function lastNumber(text, expression) {
  const found = [...text.matchAll(expression)];
  return found.length ? Number(found.at(-1)[1]) : NaN;
}

function metricDefects(metrics) {
  const defects = [];
  if (!metrics.hasVideo) defects.push("missing video stream");
  if (!metrics.hasAudio) defects.push("missing narration audio stream");
  if (metrics.width !== 1080 || metrics.height !== 1920) defects.push("Short must be 1080x1920");
  if (Math.abs(metrics.fps - 30) > 0.02) defects.push("Short must be 30fps");
  if (metrics.audioCodec !== "aac" || metrics.sampleRate !== 48000) defects.push("narration must be 48kHz AAC");
  if (!Number.isFinite(metrics.integratedLufs) || metrics.integratedLufs < -18.5 || metrics.integratedLufs > -13.5) defects.push("narration loudness must remain near -16 LUFS");
  if (!Number.isFinite(metrics.truePeakDbfs) || metrics.truePeakDbfs > -0.5 || metrics.truePeakDbfs < -4) defects.push("narration true peak is outside the audible delivery range");
  if (metrics.speechSeconds < Math.max(1, metrics.sourceSpeechSeconds * 0.65)) defects.push("final mix does not contain enough audible speech for the generated narration");
  if (!metrics.provenanceMatches) defects.push("voice/campaign provenance does not match this item");
  if (!metrics.sourceClipsAudible) defects.push("one or more source narration clips is silent or stale");
  if (!metrics.thumbnailMatches) defects.push("thumbnail is missing or has the wrong dimensions");
  if (Math.abs(metrics.duration - metrics.expectedDuration) > 0.08) defects.push("video duration does not match the narration-led scene schedule");
  return defects;
}

function selfTest() {
  const passing = {
    hasVideo: true, hasAudio: true, width: 1080, height: 1920, fps: 30,
    audioCodec: "aac", sampleRate: 48000, integratedLufs: -16.1,
    truePeakDbfs: -1.3, speechSeconds: 11, sourceSpeechSeconds: 12,
    provenanceMatches: true, sourceClipsAudible: true, thumbnailMatches: true,
    duration: 21.1, expectedDuration: 21.1,
  };
  if (metricDefects(passing).length) throw new Error("QA self-test rejected a valid fixture");
  if (!metricDefects({ ...passing, hasAudio: false, speechSeconds: 0 }).length) throw new Error("QA self-test accepted silent delivery");
  console.log("Video deliverable QA self-test OK: stream, loudness, speech, provenance, timing, and thumbnail gates");
}

if (process.argv[2] === "--self-test") {
  selfTest();
  process.exit(0);
}

const videoPath = resolve(process.argv[2] || "");
const reportPath = resolve(process.argv[3] || join(dirname(videoPath), "qa.json"));
const thumbnailPath = join(dirname(videoPath), "thumbnail.jpg");
if (!existsSync(videoPath)) throw new Error(`Video missing: ${videoPath}`);
if (!existsSync(thumbnailPath)) throw new Error(`Thumbnail missing: ${thumbnailPath}`);
if (!existsSync(VOICE_MANIFEST) || !existsSync(NARRATION)) throw new Error("Narration provenance is missing");

const itemId = basename(dirname(videoPath));
const voiceManifest = JSON.parse(readFileSync(VOICE_MANIFEST, "utf8"));
const matches = Object.entries(voiceManifest.scenarios || {}).filter(([, value]) => value.item_id === itemId);
if (matches.length !== 1) throw new Error(`Expected one voice-provenance scenario for ${itemId}, found ${matches.length}`);
const [scenario, provenance] = matches[0];
const narration = JSON.parse(readFileSync(NARRATION, "utf8"));
const batchRoot = dirname(dirname(dirname(videoPath)));
const campaignPath = join(dirname(batchRoot), `${basename(batchRoot)}-campaign.json`);
let campaignTiming = null;
if (existsSync(campaignPath)) {
  const campaign = JSON.parse(readFileSync(campaignPath, "utf8"));
  const campaignItem = (campaign.items || []).find((item) => item.item_id === itemId);
  campaignTiming = campaignItem?.renditions?.youtube?.narration?.scene_timing || null;
}
const timing = campaignTiming || narration.scene_timing?.[scenario];
if (!timing?.duration) throw new Error(`Narration-led timing missing for scenario ${scenario}`);

let sourceSpeechSeconds = 0;
let sourceClipsAudible = true;
for (const [scene, recordedDuration] of Object.entries(provenance.clips || {})) {
  const clip = join(AUDIO_ROOT, `${scenario}-${scene}.wav`);
  if (!existsSync(clip)) { sourceClipsAudible = false; continue; }
  const clipProbe = probe(clip);
  const measured = Number(clipProbe.format?.duration || 0);
  const volume = run("ffmpeg", ["-hide_banner", "-nostats", "-i", clip, "-af", "volumedetect", "-f", "null", "-"]);
  const mean = lastNumber(volume, /mean_volume:\s*(-?[\d.]+) dB/g);
  if (!Number.isFinite(mean) || mean < -45 || Math.abs(measured - Number(recordedDuration)) > 0.12) sourceClipsAudible = false;
  sourceSpeechSeconds += measured;
}

const videoProbe = probe(videoPath);
const thumbnailProbe = probe(thumbnailPath);
const video = (videoProbe.streams || []).find((stream) => stream.codec_type === "video");
const audio = (videoProbe.streams || []).find((stream) => stream.codec_type === "audio");
const thumb = (thumbnailProbe.streams || []).find((stream) => stream.codec_type === "video");
const duration = Number(videoProbe.format?.duration || 0);
const loudness = run("ffmpeg", ["-hide_banner", "-nostats", "-i", videoPath, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"]);
const silence = run("ffmpeg", ["-hide_banner", "-nostats", "-i", videoPath, "-map", "0:a:0", "-af", "silencedetect=noise=-45dB:d=0.35", "-f", "null", "-"]);
const silentSeconds = [...silence.matchAll(/silence_duration:\s*([\d.]+)/g)].reduce((sum, match) => sum + Number(match[1]), 0);

const metrics = {
  hasVideo: Boolean(video),
  hasAudio: Boolean(audio),
  width: Number(video?.width || 0),
  height: Number(video?.height || 0),
  fps: ratio(video?.avg_frame_rate),
  audioCodec: audio?.codec_name || null,
  sampleRate: Number(audio?.sample_rate || 0),
  integratedLufs: lastNumber(loudness, /I:\s*(-?[\d.]+) LUFS/g),
  truePeakDbfs: lastNumber(loudness, /Peak:\s*(-?[\d.]+) dBFS/g),
  duration,
  expectedDuration: Number(timing.duration),
  speechSeconds: Math.max(0, duration - silentSeconds),
  sourceSpeechSeconds,
  provenanceMatches: timing.voice === voiceManifest.voice
    && timing.provider === provenance.provider
    && timing.provider_voice === provenance.provider_voice,
  sourceClipsAudible,
  thumbnailMatches: Boolean(thumb) && thumb.width === video?.width && thumb.height === video?.height,
};
const defects = metricDefects(metrics);
const report = {
  schema_version: "1.0",
  render_report_id: `video-qa-${itemId}`,
  item_id: itemId,
  scenario,
  status: defects.length ? "failed" : "passed",
  video: videoPath,
  thumbnail: thumbnailPath,
  sha256: createHash("sha256").update(readFileSync(videoPath)).digest("hex"),
  voice: timing.voice,
  provider: timing.provider,
  provider_voice: timing.provider_voice,
  metrics,
  defects,
  checked_at: new Date().toISOString(),
};
writeFileSync(reportPath, JSON.stringify(report, null, 2) + "\n");
if (defects.length) {
  console.error(`Video QA failed: ${defects.join("; ")}`);
  process.exit(1);
}
console.log(`Video QA passed → ${reportPath}`);
