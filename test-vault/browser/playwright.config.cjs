const { defineConfig } = require('@playwright/test');

const executablePath = process.env.BRAND_BROWSER_EXECUTABLE;
module.exports = defineConfig({
  testDir: '.',
  fullyParallel: true,
  workers: 2,
  reporter: 'list',
  forbidOnly: Boolean(process.env.CI),
  use: {
    browserName: 'chromium',
    launchOptions: executablePath ? { executablePath } : {},
  },
});
