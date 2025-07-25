import { describe, it, expect } from 'vitest';
import { isValidElement } from 'react';
import ColumnHeader from '../src/shared/ColumnHeader';

describe('ColumnHeader', () => {
    it('creates a valid React element', () => {
        const el = <ColumnHeader title='Test' />;
        expect(isValidElement(el)).toBe(true);
    });
});
