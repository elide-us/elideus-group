import { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Button, Chip, CircularProgress, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';

import { analyzePage, type PageAnalysis } from '../../api/rpc';

interface QueryPreviewPanelProps {
	pageGuid: string | null;
}

const SOURCE_COLORS: Record<string, string> = {
	literal: '#2E7D32',
	column: '#1565C0',
	config: '#EF6C00',
	function: '#6A1B9A',
};

export function QueryPreviewPanel({ pageGuid }: QueryPreviewPanelProps): JSX.Element {
	const [analysis, setAnalysis] = useState<PageAnalysis | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const load = useCallback(async () => {
		if (!pageGuid) {
			setAnalysis(null);
			setError(null);
			setLoading(false);
			return;
		}
		setLoading(true);
		setError(null);
		try {
			const result = await analyzePage(pageGuid);
			setAnalysis(result);
		} catch {
			setAnalysis(null);
			setError('Unable to analyze this selection.');
		} finally {
			setLoading(false);
		}
	}, [pageGuid]);

	useEffect(() => {
		void load();
	}, [load]);

	const fields = useMemo(() => analysis?.output_model?.fields ?? [], [analysis]);

	return (
		<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#000000', display: 'grid', gap: 1.5 }}>
			<Stack direction="row" justifyContent="space-between" alignItems="center">
				<Typography variant="subtitle2">Query Preview</Typography>
				<Button size="small" variant="outlined" onClick={() => void load()} disabled={!pageGuid || loading}>
					Refresh
				</Button>
			</Stack>

			{loading ? (
				<Stack direction="row" spacing={1} alignItems="center">
					<CircularProgress size={16} />
					<Typography variant="body2">Analyzing bindings…</Typography>
				</Stack>
			) : null}

			{error ? <Typography variant="body2" sx={{ color: '#E57373' }}>{error}</Typography> : null}

			<Box>
				<Typography variant="subtitle2" sx={{ mb: 0.5 }}>Query</Typography>
				{analysis?.query ? (
					<Box
						component="pre"
						sx={{
							m: 0,
							p: 1,
							bgcolor: '#0A0A0A',
							border: '1px solid #1A1A1A',
							fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
							fontSize: 12,
							whiteSpace: 'pre-wrap',
						}}
					>
						{analysis.query}
					</Box>
				) : (
					<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
						No database query — all static values.
					</Typography>
				)}
			</Box>

			<Box>
				<Typography variant="subtitle2" sx={{ mb: 0.5 }}>
					Model: {analysis?.output_model?.name ?? 'No model available'}
				</Typography>
				{fields.length > 0 ? (
					<Table size="small" sx={{ border: '1px solid #1A1A1A' }}>
						<TableHead>
							<TableRow>
								<TableCell>Name</TableCell>
								<TableCell>Type</TableCell>
								<TableCell>Nullable</TableCell>
								<TableCell>Source</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{fields.map((field) => (
								<TableRow key={`${field.name}-${field.source}`}>
									<TableCell>{field.name}</TableCell>
									<TableCell>{field.type}</TableCell>
									<TableCell>{field.nullable ? 'Yes' : 'No'}</TableCell>
									<TableCell>
										<Chip
											size="small"
											label={field.source}
											sx={{
												bgcolor: SOURCE_COLORS[field.source] ?? '#455A64',
												color: '#FFFFFF',
												textTransform: 'capitalize',
											}}
										/>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				) : (
					<Typography variant="body2" sx={{ color: '#BDBDBD' }}>
						No bound fields found.
					</Typography>
				)}
			</Box>

			<Box sx={{ display: 'grid', gap: 0.75 }}>
				<Typography variant="subtitle2">Tables</Typography>
				{analysis?.tables?.length ? (
					<Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
						{analysis.tables.map((table) => (
							<Chip key={table} size="small" variant="outlined" label={table} />
						))}
					</Stack>
				) : (
					<Typography variant="body2" sx={{ color: '#BDBDBD' }}>No tables required.</Typography>
				)}
				{analysis?.joins?.length ? (
					<Box sx={{ display: 'grid', gap: 0.5 }}>
						{analysis.joins.map((join, idx) => (
							<Typography key={`${join.from}-${join.to}-${idx}`} variant="caption" sx={{ color: '#D0D0D0' }}>
								{join.from} → {join.to}
							</Typography>
						))}
					</Box>
				) : null}
			</Box>
		</Box>
	);
}
