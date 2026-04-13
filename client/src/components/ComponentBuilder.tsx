import { useCallback, useEffect, useMemo, useState } from 'react';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import DeleteIcon from '@mui/icons-material/Delete';
import {
	Box,
	Breadcrumbs,
	Button,
	Chip,
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
	getPageTree,
	listComponents,
	moveTreeNode,
	type ComponentEntry,
	type PageTreeNode,
	updateTreeNode,
} from '../api/rpc';
import type { SelectedNode } from './Workbench';

interface ComponentBuilderProps {
	data: Record<string, unknown>;
	selected: SelectedNode;
}

interface NodeDraft {
	keyGuid: string;
	componentGuid: string;
	label: string;
	fieldBinding: string;
	sequence: number;
	rpcOperation: string;
	rpcContract: string;
}

interface AddDraft {
	parentGuid: string;
	componentGuid: string;
	label: string;
	fieldBinding: string;
	sequence: number;
}

const EMPTY_NODE_DRAFT: NodeDraft = {
	keyGuid: '',
	componentGuid: '',
	label: '',
	fieldBinding: '',
	sequence: 0,
	rpcOperation: '',
	rpcContract: '',
};

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

export function ComponentBuilder({ data, selected }: ComponentBuilderProps): JSX.Element {
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [treeRows, setTreeRows] = useState<PageTreeNode[]>([]);
	const [components, setComponents] = useState<ComponentEntry[]>([]);
	const [detailDraft, setDetailDraft] = useState<NodeDraft>(EMPTY_NODE_DRAFT);
	const [addDialogOpen, setAddDialogOpen] = useState(false);
	const [addDraft, setAddDraft] = useState<AddDraft>({
		parentGuid: '',
		componentGuid: '',
		label: '',
		fieldBinding: '',
		sequence: 0,
	});

	const selectedNode = useMemo(
		() => treeRows.find((row) => row.guid === selected.childGuid) ?? null,
		[treeRows, selected.childGuid],
	);

	const refreshTree = useCallback(async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setTreeRows([]);
			return;
		}
		const rows = await getPageTree(selected.nodeGuid);
		setTreeRows(rows);
	}, [selected.nodeGuid]);

	useEffect(() => {
		void refreshTree();
	}, [refreshTree]);

	useEffect(() => {
		let mounted = true;
		const loadComponents = async (): Promise<void> => {
			const rows = await listComponents();
			if (mounted) {
				setComponents(rows);
			}
		};
		void loadComponents();
		return () => {
			mounted = false;
		};
	}, []);

	useEffect(() => {
		if (!selectedNode) {
			setDetailDraft(EMPTY_NODE_DRAFT);
			return;
		}
		setDetailDraft({
			keyGuid: selectedNode.guid,
			componentGuid: selectedNode.component_guid,
			label: selectedNode.label ?? '',
			fieldBinding: selectedNode.field_binding ?? '',
			sequence: selectedNode.sequence,
			rpcOperation: selectedNode.rpc_operation ?? '',
			rpcContract: selectedNode.rpc_contract ?? '',
		});
	}, [selectedNode]);

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

	const renderFrame = (content: JSX.Element): JSX.Element => (
		<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, color: '#FFFFFF', bgcolor: '#000000' }}>
			{content}
		</Box>
	);

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
		if (!selected.nodeGuid || !addDraft.componentGuid) {
			return;
		}
		await createTreeNode({
			pageGuid: selected.nodeGuid,
			parentGuid: addDraft.parentGuid || null,
			componentGuid: addDraft.componentGuid,
			label: addDraft.label || null,
			fieldBinding: addDraft.fieldBinding || null,
			sequence: Number(addDraft.sequence || 0),
		});
		setAddDialogOpen(false);
		await refreshTree();
	};

	if (!selected.nodeGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Pages</Typography>
				</Breadcrumbs>
				<Typography variant="body1">Select a page node to open ComponentBuilder.</Typography>
			</>,
		);
	}

	if (!selected.childGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Pages</Typography>
					<Typography color="#4CAF50">{selected.nodeName}</Typography>
				</Breadcrumbs>
				<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
					<Typography variant="h5">Component Tree</Typography>
					<Button variant="contained" onClick={() => openAddDialog(null)}>
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
							<TableRow key={row.guid} hover>
								<TableCell>
									<Button
										variant="text"
										sx={{ pl: row.level * 2, justifyContent: 'flex-start' }}
										onClick={() =>
											selectNode?.({
												categoryGuid: selected.categoryGuid,
												categoryName: selected.categoryName,
												nodeGuid: selected.nodeGuid,
												nodeName: selected.nodeName,
												childGuid: row.guid,
												childName: row.component_name,
											})
										}
									>
										{row.component_name}
									</Button>
								</TableCell>
								<TableCell>
									<Chip
										label={row.component_category}
										size="small"
										sx={{ bgcolor: categoryColor(row.component_category), color: '#FFFFFF' }}
									/>
								</TableCell>
								<TableCell>{row.label ?? '—'}</TableCell>
								<TableCell sx={{ color: '#4CAF50', fontFamily: 'monospace' }}>
									{row.field_binding ?? '—'}
								</TableCell>
								<TableCell>{row.sequence}</TableCell>
								<TableCell align="right">
									<IconButton
										onClick={async () => {
											await moveTreeNode({
												keyGuid: row.guid,
												newParentGuid: row.parent_guid,
												newSequence: row.sequence - 1,
											});
											await refreshTree();
										}}
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
											await refreshTree();
										}}
									>
										<ArrowDownwardIcon fontSize="small" />
									</IconButton>
									<IconButton
										onClick={async () => {
											await deleteTreeNode(row.guid);
											await refreshTree();
										}}
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
			</>,
		);
	}

	return renderFrame(
		<>
			<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
				<Typography color="#4CAF50">Pages</Typography>
				<Typography color="#4CAF50">{selected.nodeName}</Typography>
				<Typography color="#4CAF50">{selected.childName ?? 'Component'}</Typography>
			</Breadcrumbs>
			<Typography variant="h5" sx={{ mb: 2 }}>
				Node Detail
			</Typography>
			<Box sx={{ display: 'grid', gap: 1.5, maxWidth: 600 }}>
				<Select
					value={detailDraft.componentGuid}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, componentGuid: String(event.target.value) }))}
				>
					{components.map((component) => (
						<MenuItem key={component.guid} value={component.guid}>
							{component.name}
						</MenuItem>
					))}
				</Select>
				<TextField
					label="Label"
					value={detailDraft.label}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, label: event.target.value }))}
				/>
				<TextField
					label="Field Binding"
					value={detailDraft.fieldBinding}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, fieldBinding: event.target.value }))}
					sx={{ '& input': { fontFamily: 'monospace' } }}
				/>
				<TextField
					type="number"
					label="Sequence"
					value={detailDraft.sequence}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, sequence: Number(event.target.value || 0) }))}
				/>
				<TextField
					label="RPC Operation"
					value={detailDraft.rpcOperation}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, rpcOperation: event.target.value }))}
					sx={{ '& input': { fontFamily: 'monospace' } }}
				/>
				<TextField
					label="RPC Contract"
					value={detailDraft.rpcContract}
					onChange={(event) => setDetailDraft((prev) => ({ ...prev, rpcContract: event.target.value }))}
					sx={{ '& input': { fontFamily: 'monospace' } }}
				/>
				<TextField label="GUID" value={detailDraft.keyGuid} InputProps={{ readOnly: true }} sx={{ '& input': { fontFamily: 'monospace' } }} />
				<Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
					<Button
						variant="contained"
						onClick={async () => {
							await updateTreeNode({
								keyGuid: detailDraft.keyGuid,
								label: detailDraft.label || null,
								fieldBinding: detailDraft.fieldBinding || null,
								sequence: detailDraft.sequence,
								rpcOperation: detailDraft.rpcOperation || null,
								rpcContract: detailDraft.rpcContract || null,
								componentGuid: detailDraft.componentGuid,
							});
							await refreshTree();
						}}
					>
						Save
					</Button>
					<Button variant="outlined" onClick={() => openAddDialog(detailDraft.keyGuid)}>
						Add Child
					</Button>
					<Button
						variant="outlined"
						color="error"
						onClick={async () => {
							await deleteTreeNode(detailDraft.keyGuid);
							selectNode?.({
								categoryGuid: selected.categoryGuid,
								categoryName: selected.categoryName,
								nodeGuid: selected.nodeGuid,
								nodeName: selected.nodeName,
								childGuid: null,
								childName: null,
							});
							await refreshTree();
						}}
					>
						Delete
					</Button>
					<Button
						onClick={() =>
							selectNode?.({
								categoryGuid: selected.categoryGuid,
								categoryName: selected.categoryName,
								nodeGuid: selected.nodeGuid,
								nodeName: selected.nodeName,
								childGuid: null,
								childName: null,
							})
						}
					>
						Back to Tree
					</Button>
				</Box>
			</Box>
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
		</>,
	);
}
