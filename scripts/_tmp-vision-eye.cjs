const puppeteer = require("puppeteer");
const https = require("https");
const { readFileSync, existsSync } = require("fs");
const { join } = require("path");
const ROOT = "/Users/shayan/ShayanSpiel.Github.io";
const CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const API_KEY = "sk-nry--LsZ-vF0ZizEzUJzLEmVQnfFxf0_7alYtucxtyhhglE";
const BASE = "https://router.bynara.id/v1";
const MODEL = "mistral-medium-3-5";
const ART = join(ROOT, ".spielos/artifacts/template-preview-20260817/social");

const IMAGES = process.argv.slice(2);
const PROMPT = `You are a design QA vision model acting as eyes for a layout engineer. Describe the image PRECISELY and CRITICALLY. Focus on:
1. Overall composition: where is each major element (headline text, cards/panels, stats grid, journey line, bullseye, footer logo)?
2. Alignment: any elements that look misaligned, off-center, colliding, overlapping, or clipped at the edges?
3. Spacing: is whitespace balanced? any crowding or excessive gaps?
4. Typography: font consistency, any text wrapping badly, too large/small, unreadable?
5. Visual issues: overlapping lines, text-on-line collisions, ugly gaps, color problems.
Report as a numbered list of concrete observations with approximate positions (e.g. "headline at top-left third", "card right side spans y 20%-60%"). Be blunt and specific. If the image is blank or mostly dark, say so explicitly.`;

function downscale(imgPath, maxW, maxH) {
  return puppeteer.launch({ headless: "new", args: ["--no-sandbox"], executablePath: existsSync(CHROME_PATH) ? CHROME_PATH : undefined }).then(async (browser) => {
    const page = await browser.newPage();
    await page.setContent(`<style>body{margin:0;background:#000}</style><img id="i" src="data:image/png;base64,${readFileSync(imgPath).toString("base64")}">`);
    const jpeg = await page.evaluate(async (mw, mh) => {
      const img = document.getElementById("i");
      await img.decode();
      const scale = Math.min(1, mw / img.naturalWidth, mh / img.naturalHeight);
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(img.naturalWidth * scale);
      canvas.height = Math.round(img.naturalHeight * scale);
      const ctx = canvas.getContext("2d");
      ctx.fillStyle = "#000"; ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      return canvas.toDataURL("image/jpeg", 0.85).split(",")[1];
    }, maxW, maxH);
    await browser.close();
    return jpeg;
  });
}

function askVision(imageB64, label) {
  return new Promise((resolve) => {
    const body = JSON.stringify({
      model: MODEL,
      messages: [{ role: "user", content: [
        { type: "text", text: `${PROMPT}\n\nImage being analyzed: ${label}` },
        { type: "image_url", image_url: { url: `data:image/jpeg;base64,${imageB64}` } }
      ] }],
      max_tokens: 900,
    });
    const u = new URL(BASE + "/chat/completions");
    const req = https.request(u, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${API_KEY}` }, timeout: 120000 }, (res) => {
      let d = "";
      res.on("data", (c) => d += c);
      res.on("end", () => {
        try { const j = JSON.parse(d); resolve(j.choices && j.choices[0] && j.choices[0].message ? j.choices[0].message.content : d.slice(0, 500)); }
        catch (e) { resolve("PARSE_ERROR: " + d.slice(0, 300)); }
      });
    });
    req.on("error", (e) => resolve("REQUEST_ERROR: " + e.message));
    req.on("timeout", () => { req.destroy(); resolve("TIMEOUT"); });
    req.end(body);
  });
}

(async () => {
  for (const name of IMAGES) {
    const p = join(ART, name);
    console.log(`\n════════ ${name} ════════`);
    try {
      const jpeg = await downscale(p, 1024, 1024);
      const verdict = await askVision(jpeg, name);
      console.log(verdict);
    } catch (e) {
      console.log("ANALYSIS_ERROR: " + e.message);
    }
  }
})();
