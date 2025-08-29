import React from 'react';
import { describe, it, expect } from 'vitest';
import { renderToString } from 'react-dom/server';
import FileManager from '../src/pages/FileManager';

describe('FileManager component', () => {
	it('should render title', () => {
		const html = renderToString(<FileManager />);
		expect(html).toContain('File Manager');
	});
});
