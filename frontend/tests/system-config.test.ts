import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe('system config page', () => {
    it('has Misc tab', () => {
        const src = readFileSync(
            join(__dirname, '../src/pages/system/SystemConfigPage.tsx'),
            'utf8',
        );
        expect(src).toMatch(/label="Misc"/);
    });
});

