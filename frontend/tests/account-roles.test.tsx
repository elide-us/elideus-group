import React from 'react';
import { describe, it, expect } from 'vitest';
import { renderToString } from 'react-dom/server';
import AccountRolesPage from '../src/pages/AccountRolesPage';

describe('AccountRolesPage component', () => {
    it('should render title', () => {
        const html = renderToString(<AccountRolesPage />);
        expect(html).toContain('Account Roles');
    });
});

