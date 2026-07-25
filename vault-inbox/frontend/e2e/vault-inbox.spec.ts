import { expect, test } from "@playwright/test";

test("renders command center and redacted health", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "vault-inbox" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Validate vault/i })).toBeVisible();
  await expect(page.locator("pre")).toContainText('"vault"');
  await expect(page.locator("pre")).not.toContainText("/vault");
});

test("captures text through the real API", async ({ page }) => {
  await page.goto("/");

  await page.getByPlaceholder(/Drop a thought/i).fill("E2E capture should create a queued job.");
  await page.getByRole("button", { name: /^Capture$/ }).click();

  await expect(page.getByText("Captured. Job queued.")).toBeVisible();
  await expect(page.locator(".row strong", { hasText: "queued" }).first()).toBeVisible();
});

test("searches fixture vault notes through the backend", async ({ page }) => {
  await page.goto("/");

  await page.getByPlaceholder(/Search titles/i).fill("fixture-memory");
  await page.locator(".searchLine button").click();

  await expect(page.locator(".result strong", { hasText: "Fixture Memory" })).toBeVisible();
  await expect(page.getByText("Homelab/Memory/Fixture Memory.md")).toBeVisible();
});
