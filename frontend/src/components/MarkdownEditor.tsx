import { useRef, useState } from 'react';
import {
	Code as CodeIcon,
	FormatBold,
	FormatItalic,
	FormatListBulleted,
	FormatListNumbered,
	InsertLink,
	IntegrationInstructions,
	Title,
} from '@mui/icons-material';
import { Box, IconButton, ToggleButton, ToggleButtonGroup, Tooltip, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';

interface MarkdownEditorProps {
	value: string;
	onChange: (value: string) => void;
	minHeight?: number;
	placeholder?: string;
}

function insertMarkdown(
	textarea: HTMLTextAreaElement,
	before: string,
	after: string,
	defaultText: string,
	onChange: (value: string) => void,
	lineStart?: boolean,
): void {
	const source = textarea.value;
	let selectionStart = textarea.selectionStart;
	const selectionEnd = textarea.selectionEnd;

	if (lineStart) {
		selectionStart = source.lastIndexOf('\n', Math.max(0, selectionStart - 1)) + 1;
	}

	const selectedText = source.slice(selectionStart, selectionEnd);
	const innerText = selectedText || defaultText;
	const insertion = `${before}${innerText}${after}`;
	const nextValue = `${source.slice(0, selectionStart)}${insertion}${source.slice(selectionEnd)}`;
	onChange(nextValue);

	requestAnimationFrame(() => {
		textarea.focus();
		if (selectedText) {
			const highlightStart = selectionStart + before.length;
			const highlightEnd = highlightStart + selectedText.length;
			textarea.setSelectionRange(highlightStart, highlightEnd);
			return;
		}
		const cursor = selectionStart + before.length + innerText.length;
		textarea.setSelectionRange(cursor, cursor);
	});
}

const markdownBodySx = {
	'& h1, & h2, & h3, & h4, & h5, & h6': { mt: 3, mb: 1 },
	'& p': { mt: 1, mb: 1 },
	'& ul, & ol': { pl: 3 },
	'& a': { color: 'primary.main' },
};

const MarkdownEditor = ({
	value,
	onChange,
	minHeight = 280,
	placeholder = 'Write markdown...',
}: MarkdownEditorProps): JSX.Element => {
	const [mode, setMode] = useState<'write' | 'preview'>('write');
	const textareaRef = useRef<HTMLTextAreaElement | null>(null);

	const withSelection = (
		before: string,
		after: string,
		defaultText: string,
		lineStart = false,
	): void => {
		if (!textareaRef.current) {
			return;
		}
		insertMarkdown(textareaRef.current, before, after, defaultText, onChange, lineStart);
	};

	return (
		<Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden' }}>
			<Box sx={{ p: 1, borderBottom: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' }}>
				<ToggleButtonGroup
					exclusive
					size="small"
					value={mode}
					onChange={(_evt, next) => {
						if (next) {
							setMode(next);
						}
					}}
				>
					<ToggleButton value="write">Write</ToggleButton>
					<ToggleButton value="preview">Preview</ToggleButton>
				</ToggleButtonGroup>
			</Box>

			{mode === 'write' ? (
				<>
					<Box
						sx={{
							display: 'flex',
							alignItems: 'center',
							gap: 0.5,
							p: 0.5,
							borderBottom: '1px solid',
							borderColor: 'divider',
							bgcolor: 'background.paper',
						}}
					>
						<Tooltip title="Bold">
							<IconButton size="small" onClick={() => withSelection('**', '**', 'bold text')}>
								<FormatBold fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Italic">
							<IconButton size="small" onClick={() => withSelection('*', '*', 'italic text')}>
								<FormatItalic fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Heading 2">
							<IconButton size="small" onClick={() => withSelection('## ', '', 'Heading', true)}>
								<Title fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Heading 3">
							<IconButton size="small" onClick={() => withSelection('### ', '', 'Heading', true)}>
								<Typography variant="caption" sx={{ fontWeight: 700 }}>
									H3
								</Typography>
							</IconButton>
						</Tooltip>
						<Tooltip title="Link">
							<IconButton size="small" onClick={() => withSelection('[', '](url)', 'link text')}>
								<InsertLink fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Bulleted list">
							<IconButton size="small" onClick={() => withSelection('- ', '', 'List item', true)}>
								<FormatListBulleted fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Numbered list">
							<IconButton size="small" onClick={() => withSelection('1. ', '', 'List item', true)}>
								<FormatListNumbered fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Inline code">
							<IconButton size="small" onClick={() => withSelection('`', '`', 'code')}>
								<CodeIcon fontSize="small" />
							</IconButton>
						</Tooltip>
						<Tooltip title="Code block">
							<IconButton
								size="small"
								onClick={() => withSelection('```\n', '\n```', 'code block')}
							>
								<IntegrationInstructions fontSize="small" />
							</IconButton>
						</Tooltip>
					</Box>
					<textarea
						ref={textareaRef}
						value={value}
						placeholder={placeholder}
						onChange={(event) => {
							onChange(event.target.value);
						}}
						style={{
							display: 'block',
							width: '100%',
							minHeight: `${minHeight}px`,
							border: 'none',
							outline: 'none',
							padding: '12px',
							fontSize: '0.95rem',
							lineHeight: 1.5,
							fontFamily: 'monospace',
							resize: 'vertical',
							backgroundColor: 'var(--mui-palette-background-paper)',
							color: 'var(--mui-palette-text-primary)',
						}}
					/>
				</>
			) : (
				<Box sx={{ p: 2, minHeight, ...markdownBodySx }}>
					<ReactMarkdown>{value}</ReactMarkdown>
				</Box>
			)}
		</Box>
	);
};

export default MarkdownEditor;
