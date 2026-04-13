import { useMemo, useState } from 'react';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteIcon from '@mui/icons-material/Delete';
import {
	Box,
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	IconButton,
	MenuItem,
	Select,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableRow,
	TextField,
	Typography,
} from '@mui/material';

import {
	createTreeNode,
	deleteTreeNode,
	moveTreeNode,
	type ComponentEntry,
	type PageTreeNode,
} from '../../api/rpc';

interface ComponentTreePanelProps {
	treeRows: PageTreeNode[];
	components: ComponentEntry[];
	selectedNodeGuid: string | null;
	pageGuid: string | null;
	onSelectNode: (guid: string, name: string) => void;
	onRefreshTree: () => Promise<void>;
}

interface AddDraft {
	parentGuid: string;
	componentGuid: string;
	label: string;
	fieldBinding: string;
	sequence: number;
}

function categoryColor(category: string): string {
	if (category === 'page') {
		return '#1565C0';
	}
	if (category === 'section') {
		return '#2E7D32';
	}
	if (category === 'control') {
		return '#E65100';
	}
	return '#616161';
}

export function ComponentTreePanel({
	treeRows,
	components,
	selectedNodeGuid,
	pageGuid,
	onSelectNode,
	onRefreshTree,
}: ComponentTreePanelProps): JSX.Element {
	const [addDialogOpen, setAddDialogOpen] = useState(false);
	const [addDraft, setAddDraft] = useState<AddDraft>({
		parentGuid: '',
		componentGuid: '',
		label: '',
		fieldBinding: '',
		sequence: 0,
	});

	const nestedRows = useMemo(() => {
		const byParent = new Map<string | null, PageTreeNode[]>();
		for (const row of treeRows) {
			const parent = row.parent_guid;
			const list = byParent.get(parent) ?? [];
			list.push(row);
			byParent.set(parent, list);
		}
		for (const rows of byParent.values()) {
			rows.sort((a, b) => a.sequence - b.sequence);
		}
		const flattened: Array<PageTreeNode & { level: number }> = [];
		const walk = (parentGuid: string | null, level: number): void => {
			const children = byParent.get(parentGuid) ?? [];
			for (const child of children) {
				flattened.push({ ...child, level });
				walk(child.guid, level + 1);
			}
		};
		walk(null, 0);
		return flattened;
	}, [treeRows]);

	const openAddDialog = (parentGuid: string | null): void => {
		setAddDraft({
			parentGuid: parentGuid ?? '',
			componentGuid: components[0]?.guid ?? '',
			label: '',
			fieldBinding: '',
			sequence: 0,
		});
		setAddDialogOpen(true);
	};

	const saveAdd = async (): Promise<void> => {
		if (!pageGuid || !addDraft.componentGuid) {
			return;
		}
		await createTreeNode({
			pageGuid,
			parentGuid: addDraft.parentGuid || null,
			componentGuid: addDraft.componentGuid,
			label: addDraft.label || null,
			fieldBinding: addDraft.fieldBinding || null,
			sequence: Number(addDraft.sequence || 0),
		});
		setAddDialogOpen(false);
		await onRefreshTree();
	};

	return (
		<Box sx={{ p: 1.5, border: '1px solid #1A1A1A', bgcolor: '#000000' }}>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
				<Typography variant="h6">Component Tree</Typography>
				<Button variant="contained" onClick={() => openAddDialog(null)} disabled={!pageGuid}>
					Add Node
				</Button>
			</Box>
			<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
				<TableHead>
					<TableRow>
						<TableCell>Component</TableCell>
						<TableCell>Category</TableCell>
						<TableCell>Label</TableCell>
						<TableCell>Field Binding</TableCell>
						<TableCell>Sequence</TableCell>
						<TableCell align="right">Actions</TableCell>
					</TableRow>
				</TableHead>
				<TableBody>
					{nestedRows.map((row) => (
						<TableRow key={row.guid} hover selected={selectedNodeGuid === row.guid}>
							<TableCell>
								<Button
									variant="text"
									sx={{ pl: row.level * 2, justifyContent: 'flex-start' }}
									onClick={() => onSelectNode(row.guid, row.component_name)}
								>
									{row.component_name}
								</Button>
							</TableCell>
							<TableCell>
								<Box
									sx={{
										px: 1,
										borderRadius: 1,
										display: 'inline-block',
										bgcolor: categoryColor(row.component_category),
									}}
								>
									{row.component_category}
								</Box>
							</TableCell>
							<TableCell>{row.label ?? '—'}</TableCell>
							<TableCell sx={{ color: '#4CAF50', fontFamily: 'monospace' }}>{row.field_binding ?? '—'}</TableCell>
							<TableCell>{row.sequence}</TableCell>
							<TableCell align="right">
								<IconButton
									onClick={async () => {
										await moveTreeNode({
											keyGuid: row.guid,
											newParentGuid: row.parent_guid,
											newSequence: row.sequence - 1,
										});
										await onRefreshTree();
									}}
									disabled={!pageGuid}
								>
									<ArrowUpwardIcon fontSize="small" />
								</IconButton>
								<IconButton
									onClick={async () => {
										await moveTreeNode({
											keyGuid: row.guid,
											newParentGuid: row.parent_guid,
											newSequence: row.sequence + 1,
										});
										await onRefreshTree();
									}}
									disabled={!pageGuid}
								>
									<ArrowDownwardIcon fontSize="small" />
								</IconButton>
								<IconButton
									onClick={async () => {
										await deleteTreeNode(row.guid);
										await onRefreshTree();
									}}
									disabled={!pageGuid}
								>
									<DeleteIcon fontSize="small" />
								</IconButton>
							</TableCell>
						</TableRow>
					))}
				</TableBody>
			</Table>
			<Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)}>
				<DialogTitle>Add Node</DialogTitle>
				<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 360, pt: '12px !important' }}>
					<Select
						value={addDraft.parentGuid}
						onChange={(event) => setAddDraft((prev) => ({ ...prev, parentGuid: String(event.target.value) }))}
					>
						<MenuItem value="">(Root)</MenuItem>
						{nestedRows.map((row) => (
							<MenuItem key={row.guid} value={row.guid}>
								{`${'\u00A0\u00A0'.repeat(row.level)}${row.component_name}`}
							</MenuItem>
						))}
					</Select>
					<Select
						value={addDraft.componentGuid}
						onChange={(event) => setAddDraft((prev) => ({ ...prev, componentGuid: String(event.target.value) }))}
					>
						{components.map((component) => (
							<MenuItem key={component.guid} value={component.guid}>
								{component.name}
							</MenuItem>
						))}
					</Select>
					<TextField
						label="Label"
						value={addDraft.label}
						onChange={(event) => setAddDraft((prev) => ({ ...prev, label: event.target.value }))}
					/>
					<TextField
						label="Field Binding"
						value={addDraft.fieldBinding}
						onChange={(event) => setAddDraft((prev) => ({ ...prev, fieldBinding: event.target.value }))}
						sx={{ '& input': { fontFamily: 'monospace' } }}
					/>
					<TextField
						type="number"
						label="Sequence"
						value={addDraft.sequence}
						onChange={(event) => setAddDraft((prev) => ({ ...prev, sequence: Number(event.target.value || 0) }))}
					/>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setAddDialogOpen(false)}>Cancel</Button>
					<Button variant="contained" onClick={() => void saveAdd()}>
						Create
					</Button>
				</DialogActions>
			</Dialog>
		</Box>
	);
}
