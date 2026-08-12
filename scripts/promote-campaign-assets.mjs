#!/usr/bin/env node

import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, dirname, resolve } from "node:path";
import { createHash } from "node:crypto";

const ORIGIN = "https://spielos.xyz";

const readFlag = (args, flag) => {
  const index = args.indexOf(flag);
  return index < 0 ? "" : String(args[index + 1] || "");
};

const approvalId = (batchApprovalId, contentId, checksum) =>
  `batch-${createHash("sha256").update(`${batchApprovalId}|${contentId}|${checksum}`).digest("hex").slice(0, 20)}`;

async function promote(args) {
  const manifestPath = readFlag(args, "--manifest");
  const batchApprovalId = readFlag(args, "--approval-id");
  if (!manifestPath || !batchApprovalId) throw new Error("Expected --manifest and --approval-id");
  const manifest = JSON.parse(await readFile(resolve(manifestPath), "utf8"));
  if (manifest.phase !== "rendered") throw new Error("Campaign Artifact must be rendered before promotion");
  const output = resolve(readFlag(args, "--output") || manifestPath.replace(/\.json$/, "-approved.json"));
  const result = structuredClone(manifest);
  const approvals = [];
  for (const item of result.items || []) {
    for (const platform of ["threads", "youtube"]) {
      const rendition = item.renditions?.[platform];
      const asset = rendition?.asset;
      if (!rendition?.content_id || !asset?.local_path || !asset?.sha256) {
        throw new Error(`Missing rendered provenance for ${item.item_id}/${platform}`);
      }
      const publicPath = `/campaign-assets/${result.batch_id}/${platform}/${rendition.content_id}-${basename(asset.local_path)}`;
      await mkdir(dirname(resolve("public", `.${publicPath}`)), { recursive: true });
      await copyFile(resolve(asset.local_path), resolve("public", `.${publicPath}`));
      const id = approvalId(batchApprovalId, rendition.content_id, asset.sha256);
      asset.public_url = `${ORIGIN}${publicPath}`;
      rendition.approval = { status: "approved", approval_id: id };
      approvals.push({ item_id: item.item_id, platform, approval_id: id, public_url: asset.public_url });
    }
  }
  result.phase = "approved";
  result.handoffs = [...(result.handoffs || []), {
    from: "rendered", to: "approved",
    evidence: { batch_approval_id: batchApprovalId, approvals, asset_host: ORIGIN },
  }];
  await writeFile(output, `${JSON.stringify(result, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({ ok: true, output, approvals }, null, 2)}\n`);
}

const args = process.argv.slice(2);
if (args.includes("--check")) {
  process.stdout.write(JSON.stringify({ ok: true, origin: ORIGIN }) + "\n");
} else {
  promote(args).catch((error) => {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  });
}
