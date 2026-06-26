import { chromium } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const outputDir = path.resolve(scriptDir, "../../docs/screenshots");
const baseUrl = process.env.CROSSDOC_WEB_URL ?? "http://127.0.0.1:3000";

await mkdir(outputDir, { recursive: true });

let browser;
try {
  browser = await chromium.launch({ channel: "chrome", headless: true });
} catch {
  browser = await chromium.launch({ headless: true });
}

const desktop = await browser.newContext({
  viewport: { width: 1440, height: 960 },
  deviceScaleFactor: 1,
});

const screens = [
  { path: "/dashboard", heading: "Operations overview", file: "01_dashboard.png" },
  { path: "/upload", heading: "Process document bundle", file: "02_process_documents.png" },
  { path: "/documents/1", heading: "Document inspector", file: "03_document_inspector.png" },
  { path: "/system-health", heading: "System health", file: "04_system_health.png" },
];

for (const screen of screens) {
  const page = await desktop.newPage();
  await page.goto(`${baseUrl}${screen.path}`, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: screen.heading }).waitFor();
  await page.locator("aside").first().waitFor({ state: "visible" });
  await page.getByText("New case").waitFor({ state: "visible" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
  await page.screenshot({
    path: path.join(outputDir, screen.file),
    fullPage: true,
  });
  await page.close();
}

const mobile = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 1,
});
const mobilePage = await mobile.newPage();
await mobilePage.goto(`${baseUrl}/dashboard`, { waitUntil: "networkidle" });
await mobilePage.getByRole("heading", { name: "Operations overview" }).waitFor();
await mobilePage.evaluate(() => document.fonts.ready);
await mobilePage.waitForTimeout(500);
await mobilePage.screenshot({
  path: path.join(outputDir, "05_dashboard_mobile.png"),
  fullPage: true,
});

await browser.close();
console.log(`Captured ${screens.length + 1} real application screenshots in ${outputDir}`);
