import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";
const env = readFileSync("../.env", "utf8");
const token = env.match(/^DEV_TOKEN=(.+)$/m)?.[1] || "";
test("upload, stream, cite, approve and delete a source", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Access token").fill(token);
  await page.getByRole("button", { name: /Enter workspace/ }).click();
  await page.getByRole("button", { name: "⚙ Settings" }).click();
  await page
    .getByLabel("New workspace", { exact: true })
    .fill("Browser " + Date.now());
  await page
    .getByRole("button", { name: "Create workspace", exact: true })
    .click();
  await page.getByLabel("New knowledge base", { exact: true }).fill("Handbook");
  await page
    .getByRole("button", { name: "Create knowledge base", exact: true })
    .click();
  await expect(
    page.getByLabel("Knowledge base", { exact: true }),
  ).not.toHaveValue("");
  await page.getByRole("button", { name: "▤ Knowledge", exact: true }).click();
  await page.getByLabel("Upload documents").setInputFiles({
    name: "policy.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Employees receive twenty days of vacation annually."),
  });
  await expect(page.locator(".status.ready")).toHaveText("ready", {
    timeout: 30000,
  });
  await page.getByRole("button", { name: "◈ Chat", exact: true }).click();
  await page
    .getByLabel("Question", { exact: true })
    .fill("How much vacation do employees receive?");
  await page.getByRole("button", { name: "Ask ↗", exact: true }).click();
  await expect(page.locator(".message.assistant .messageText")).toContainText(
    "twenty days",
    { timeout: 30000 },
  );
  await page
    .getByRole("button", { name: "[1] policy.txt", exact: true })
    .click();
  await expect(page.locator(".sourceText")).toContainText("twenty days");
  await page.screenshot({
    path: "test-results/chat-with-citation.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close source" }).click();
  await page.getByRole("button", { name: "Regenerate", exact: true }).click();
  await expect(page.locator(".message.assistant")).toHaveCount(2);
  await expect(
    page.locator(".message.assistant .messageText").last(),
  ).toContainText("twenty days");
  await page.getByRole("button", { name: "▤ Knowledge", exact: true }).click();
  await page.getByRole("button", { name: "Reprocess", exact: true }).click();
  await page.getByRole("button", { name: "✓ Approvals", exact: true }).click();
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect(page.locator(".approval .status")).toHaveText("completed");
  await page.getByRole("button", { name: "▤ Knowledge", exact: true }).click();
  await expect(page.locator(".status.ready")).toHaveText("ready", {
    timeout: 30000,
  });
  await page.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(page.locator(".document")).toHaveCount(0);
  await page.screenshot({ path: "test-results/workflow.png", fullPage: true });
});

test("mobile sign-in layout stays within the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByLabel("Access token").fill(token);
  await page.getByRole("button", { name: /Enter workspace/ }).click();
  await expect(
    page.getByRole("heading", { name: "Ask with confidence" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({ path: "test-results/mobile.png", fullPage: true });
});
