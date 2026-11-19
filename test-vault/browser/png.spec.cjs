const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test, expect } = require('@playwright/test');

const assetDir = process.env.BRAND_BROWSER_ASSETS;
if (!assetDir) {
  throw new Error('Run bash test-vault/tests/browser.sh from the repository root.');
}
const manifest = JSON.parse(readFileSync(path.join(assetDir, 'manifest.json'), 'utf8'));
const origin = 'https://brand-pngs.invalid';

test.beforeEach(async ({ page }) => {
  const files = new Set(manifest.assets.map(({ file }) => file));
  await page.route(`${origin}/**`, async (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (pathname === '/') {
      await route.fulfill({ contentType: 'text/html', body: '<!doctype html><title>PNG decode</title>' });
    } else if (files.has(pathname.slice(1))) {
      await route.fulfill({ contentType: 'image/png', path: path.join(assetDir, pathname.slice(1)) });
    } else {
      await route.fulfill({ status: 404 });
    }
  });
  await page.goto(origin);
});

async function draw(page, filename, background) {
  return page.evaluate(async ({ filename, background }) => {
    const image = new Image();
    image.src = `/${filename}`;
    await image.decode();
    const canvas = document.createElement('canvas');
    canvas.width = image.naturalWidth;
    canvas.height = image.naturalHeight;
    const context = canvas.getContext('2d');
    if (background) {
      context.fillStyle = background;
      context.fillRect(0, 0, canvas.width, canvas.height);
    }
    context.drawImage(image, 0, 0);
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
    return { width: image.naturalWidth, height: image.naturalHeight, pixels: [...pixels] };
  }, { filename, background });
}

const encodings = [
  ['rgba.png', [255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 255, 128, 0, 255, 0, 255]],
  ['indexed.png', [255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 255, 128, 255, 255, 255, 255]],
  ['grayscale-alpha.png', [0, 0, 0, 255, 0, 0, 0, 0, 128, 128, 128, 128, 255, 255, 255, 255]],
  ['rgb.png', [255, 0, 0, 255, 0, 255, 0, 255, 0, 0, 255, 255, 255, 255, 255, 255]],
];

for (const [filename, pixels] of encodings) {
  test(`PNG-010 decodes registered ${filename} with the expected dimensions and pixels`, async ({ page }) => {
    expect(await draw(page, filename)).toEqual({ width: 4, height: 1, pixels });
  });
}

test('PNG-012 decodes a truecolor transparency key without losing other colors', async ({ page }) => {
  expect(await draw(page, 'rgb-keyed.png')).toEqual({
    width: 4,
    height: 1,
    pixels: [255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 255, 255, 255, 255, 255, 255],
  });
});

test('PNG-012 converts 16-bit samples while preserving the alpha pattern', async ({ page }) => {
  expect(await draw(page, 'rgba16.png')).toEqual({
    width: 4,
    height: 1,
    pixels: [255, 0, 0, 255, 0, 0, 0, 0, 0, 0, 255, 128, 64, 128, 255, 255],
  });
});

test('PNG-012 reconstructs a diagonal across all seven Adam7 passes', async ({ page }) => {
  const expected = [];
  for (let y = 0; y < 5; y += 1) {
    for (let x = 0; x < 5; x += 1) {
      const level = x === y ? 255 : 0;
      expected.push(level, level, level, 255);
    }
  }
  expect(await draw(page, 'adam7-diagonal.png')).toEqual({ width: 5, height: 5, pixels: expected });
});

for (const [theme, background, empty, edge] of [
  ['light', '#ffffff', [255, 255, 255, 255], [127, 127, 255, 255]],
  ['dark', '#000000', [0, 0, 0, 255], [0, 0, 128, 255]],
]) {
  for (const file of ['rgba.png', 'indexed.png']) {
    test(`PNG-011 composites ${file} over a ${theme} background`, async ({ page }) => {
      const { pixels } = await draw(page, file, background);
      expect(pixels.slice(0, 4)).toEqual([255, 0, 0, 255]);
      expect(pixels.slice(4, 8)).toEqual(empty);
      expect(pixels.slice(8, 12)).toEqual(edge);
    });
  }
}
