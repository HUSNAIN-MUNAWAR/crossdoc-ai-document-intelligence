import { test, expect } from "@playwright/test"; test("dashboard", async ({page})=>{await page.goto("/dashboard"); await expect(page.getByText("Dashboard overview")).toBeVisible();});
