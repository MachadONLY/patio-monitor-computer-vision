import { chromium, expect } from "@playwright/test";
import { execFileSync } from "node:child_process";
import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

// Prova de navegação na versão publicada: a gravação anotada e seus
// cruzamentos são servidos pela API, sem respostas controladas ou capturas estáticas.
const base = "https://patio-monitor-production.up.railway.app";
const output = resolve("../../docs/gs/cv/demonstracao-cv-navegador-real.mp4");
const browser = await chromium.launch({
  headless: true,
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  deviceScaleFactor: 1,
  reducedMotion: "reduce",
  recordVideo: {
    dir: "test-results/cv-real-recording",
    size: { width: 1280, height: 720 },
  },
});
const page = await context.newPage();
const exceptions = [];
page.on("pageerror", e => exceptions.push(e.message));
try {
  const response = await page.goto(base, { waitUntil: "domcontentloaded", timeout: 40_000 });
  expect(response?.status()).toBe(200);
  await expect(page.getByRole("button", { name: "Câmera do portão", exact: true })).toBeVisible();
  await expect(page.locator(".viewport")).toHaveAttribute("data-ready", "true", { timeout: 50_000 });
  await page.waitForTimeout(4200);

  const visionResponse = page.waitForResponse(
    r => new URL(r.url()).pathname === "/api/gs/vision" && r.ok(), { timeout: 40_000 }
  );
  await page.getByRole("button", { name: "Câmera do portão", exact: true }).click();
  const apiResult = await visionResponse;
  const report = await apiResult.json();
  expect(report.data_origin).toBe("PUBLIC_VIDEO");
  expect(report.events.length).toBeGreaterThan(0);
  expect(report.events[0].timestamp_seconds).toBeCloseTo(7.44, 1);

  const camera = page.getByRole("dialog", { name: "Câmera do portão" });
  const video = camera.locator("video");
  await expect(camera.getByText("Cruzamentos detectados")).toBeVisible();
  await expect.poll(() => video.evaluate(
    el => el.error === null && el.readyState >= 1 && el.videoWidth >= 700 && el.duration > 7.44
  ), { timeout: 40_000 }).toBe(true);
  await page.waitForTimeout(6500);

  // O navegador reproduz o vídeo anotado do detector por tempo real de reprodução.
  await video.evaluate(async el => { el.muted = true; el.currentTime = 0; await el.play(); });
  await expect.poll(() => video.evaluate(el => el.currentTime), { timeout: 18_000 })
    .toBeGreaterThan(5);
  await page.waitForTimeout(5500);
  await video.evaluate(el => el.pause());
  await page.waitForTimeout(2500);

  const event = camera.getByRole("button", { name: /Esquerda.*direita.*00:07,4/ });
  await event.click();
  await expect(event).toHaveAttribute("aria-pressed", "true");
  await expect.poll(() => video.evaluate(el => Math.abs(el.currentTime - 7.44)), { timeout: 12_000 })
    .toBeLessThan(0.1);
  await expect(camera.getByText("confiança do modelo")).toBeVisible();
  await expect(camera.getByRole("link", { name: /Gravação original/ })).toBeVisible();
  await page.waitForTimeout(8000);

  // Revisão visual da fonte da gravação e do instante vinculado ao evento.
  await video.evaluate(async el => { el.muted = true; await el.play(); });
  await page.waitForTimeout(5500);
  await video.evaluate(el => el.pause());
  await page.waitForTimeout(3000);

  await camera.getByRole("button", { name: "Fechar câmera do portão" }).click();
  await page.waitForTimeout(3600);
  expect(exceptions).toEqual([]);
  const recording = page.video();
  await context.close();
  const source = await recording.path();
  await mkdir(resolve("../../docs/gs/cv"), { recursive: true });
  execFileSync("ffmpeg", [
    "-hide_banner", "-loglevel", "error", "-y", "-i", source,
    "-vf", "fps=24,format=yuv420p",
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-movflags", "+faststart", output,
  ], { stdio: "inherit" });
  console.log("Recorded real production camera walkthrough:", output);
} finally {
  await browser.close();
}
