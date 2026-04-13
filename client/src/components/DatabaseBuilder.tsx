import { useEffect, useMemo, useState } from 'react';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
	Box,
	Breadcrumbs,
	Button,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	FormControlLabel,
	IconButton,
	MenuItem,
	Select,
	Switch,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableRow,
	TextField,
	Typography,
} from '@mui/material';

import {
	deleteDatabaseColumn,
	deleteDatabaseTable,
	readObjectTreeChildren,
	readObjectTreeDetail,
	type ObjectTreeColumn,
	upsertDatabaseColumn,
	upsertDatabaseTable,
} from '../api/rpc';
import type { SelectedNode } from './Workbench';

const DATABASE_TABLES_GUID = '78D4E217-6810-5A05-8999-ED57016229B6';
const DATABASE_COLUMNS_GUID = '4241CCF3-A1F8-5A80-86BD-82632E121495';
const TYPES_CATEGORY_GUID = 'EFAB32FE-8DF8-58FD-8C68-39D3B9E3BE00';

interface DatabaseBuilderProps {
	data: Record<string, unknown>;
	selected: SelectedNode;
}

interface TableRow {
	key_guid: string;
	pub_name: string;
	pub_schema: string;
	priv_created_on?: string;
	priv_modified_on?: string;
}

interface ColumnRow extends ObjectTreeColumn {
	ref_type_guid?: string | null;
	pub_default?: string | null;
	pub_is_identity?: boolean;
}

interface TypeRow {
	guid: string;
	name: string;
}

export function DatabaseBuilder({ data, selected }: DatabaseBuilderProps): JSX.Element {
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [tables, setTables] = useState<TableRow[]>([]);
	const [columns, setColumns] = useState<ColumnRow[]>([]);
	const [types, setTypes] = useState<TypeRow[]>([]);
	const [tableDialogOpen, setTableDialogOpen] = useState(false);
	const [columnDialogOpen, setColumnDialogOpen] = useState(false);
	const [tableDraft, setTableDraft] = useState({ keyGuid: '', name: '', schema: 'dbo' });
	const [columnDraft, setColumnDraft] = useState({
		keyGuid: '',
		name: '',
		typeGuid: '',
		ordinal: 1,
		isNullable: true,
		isPrimaryKey: false,
		isIdentity: false,
		defaultValue: '',
		maxLength: '',
	});

	const selectedColumn = useMemo(
		() => columns.find((column) => column.guid === selected.childGuid) ?? null,
		[columns, selected.childGuid],
	);

	const refreshTables = async (): Promise<void> => {
		const detail = await readObjectTreeDetail(DATABASE_TABLES_GUID, 1000);
		const nextRows = Array.isArray(detail.rows)
			? detail.rows.map((row) => {
					const payload = row as Record<string, unknown>;
					return {
						key_guid: String(payload.key_guid ?? ''),
						pub_name: String(payload.pub_name ?? ''),
						pub_schema: String(payload.pub_schema ?? 'dbo'),
						priv_created_on: payload.priv_created_on ? String(payload.priv_created_on) : undefined,
						priv_modified_on: payload.priv_modified_on ? String(payload.priv_modified_on) : undefined,
					};
				})
			: [];
		setTables(nextRows);
	};

	const refreshColumns = async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setColumns([]);
			return;
		}
		const treeColumns = await readObjectTreeChildren(selected.categoryGuid, selected.nodeGuid);
		const detail = await readObjectTreeDetail(DATABASE_COLUMNS_GUID, 2000);
		const detailRows = Array.isArray(detail.rows) ? detail.rows : [];
		const byGuid = new Map(
			detailRows
				.filter((row) => String((row as { ref_table_guid?: string }).ref_table_guid || '') === selected.nodeGuid)
				.map((row) => [String((row as { key_guid?: string }).key_guid || ''), row]),
		);
		const merged = (treeColumns as ObjectTreeColumn[]).map((column) => {
			const detailRow = byGuid.get(column.guid) as Record<string, unknown> | undefined;
			return {
				...column,
				ref_type_guid: (detailRow?.ref_type_guid as string | undefined) ?? null,
				pub_default: (detailRow?.pub_default as string | undefined) ?? null,
				pub_is_identity: Boolean(detailRow?.pub_is_identity ?? false),
			};
		});
		setColumns(merged);
	};

	useEffect(() => {
		void refreshTables();
	}, []);

	useEffect(() => {
		void refreshColumns();
	}, [selected.categoryGuid, selected.nodeGuid]);

	useEffect(() => {
		let mounted = true;
		const loadTypes = async (): Promise<void> => {
			const values = await readObjectTreeChildren(TYPES_CATEGORY_GUID);
			if (!mounted) {
				return;
			}
			setTypes((values as { guid: string; name: string }[]).map((row) => ({ guid: row.guid, name: row.name })));
		};
		void loadTypes();
		return () => {
			mounted = false;
		};
	}, []);

	const renderFrame = (content: JSX.Element): JSX.Element => (
		<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, color: '#FFFFFF' }}>{content}</Box>
	);

	const saveTable = async (): Promise<void> => {
		await upsertDatabaseTable({
			keyGuid: tableDraft.keyGuid || undefined,
			name: tableDraft.name,
			schema: tableDraft.schema || 'dbo',
		});
		setTableDialogOpen(false);
		setTableDraft({ keyGuid: '', name: '', schema: 'dbo' });
		await refreshTables();
	};

	const saveColumn = async (): Promise<void> => {
		if (!selected.nodeGuid) {
			return;
		}
		await upsertDatabaseColumn({
			keyGuid: columnDraft.keyGuid || undefined,
			tableGuid: selected.nodeGuid,
			typeGuid: columnDraft.typeGuid,
			name: columnDraft.name,
			ordinal: Number(columnDraft.ordinal),
			isNullable: columnDraft.isNullable,
			isPrimaryKey: columnDraft.isPrimaryKey,
			isIdentity: columnDraft.isIdentity,
			defaultValue: columnDraft.defaultValue || null,
			maxLength: columnDraft.maxLength === '' ? null : Number(columnDraft.maxLength),
		});
		setColumnDialogOpen(false);
		await refreshColumns();
	};

	if (!selected.nodeGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Database</Typography>
				</Breadcrumbs>
				<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
					<Typography variant="h5">Tables</Typography>
					<Button variant="contained" onClick={() => setTableDialogOpen(true)}>
						New Table
					</Button>
				</Box>
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>Name</TableCell>
							<TableCell>Schema</TableCell>
							<TableCell>Created</TableCell>
							<TableCell>Modified</TableCell>
							<TableCell align="right">Actions</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{tables.map((row) => (
							<TableRow key={row.key_guid} hover>
								<TableCell>
									<Button
										variant="text"
										onClick={() =>
											selectNode?.({
												categoryGuid: selected.categoryGuid,
												categoryName: selected.categoryName,
												nodeGuid: row.key_guid,
												nodeName: row.pub_name,
												childGuid: null,
												childName: null,
											})
										}
									>
										{row.pub_name}
									</Button>
								</TableCell>
								<TableCell>{row.pub_schema}</TableCell>
								<TableCell>{row.priv_created_on ?? ''}</TableCell>
								<TableCell>{row.priv_modified_on ?? ''}</TableCell>
								<TableCell align="right">
									<IconButton
										onClick={() => {
											setTableDraft({ keyGuid: row.key_guid, name: row.pub_name, schema: row.pub_schema });
											setTableDialogOpen(true);
										}}
									>
										<EditIcon fontSize="small" />
									</IconButton>
									<IconButton
										onClick={async () => {
											await deleteDatabaseTable(row.key_guid);
											await refreshTables();
										}}
									>
										<DeleteIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
				<Dialog open={tableDialogOpen} onClose={() => setTableDialogOpen(false)}>
					<DialogTitle>{tableDraft.keyGuid ? 'Edit Table' : 'New Table'}</DialogTitle>
					<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 320, pt: '12px !important' }}>
						<TextField
							label="Name"
							value={tableDraft.name}
							onChange={(event) => setTableDraft((prev) => ({ ...prev, name: event.target.value }))}
						/>
						<TextField
							label="Schema"
							value={tableDraft.schema}
							onChange={(event) => setTableDraft((prev) => ({ ...prev, schema: event.target.value }))}
						/>
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setTableDialogOpen(false)}>Cancel</Button>
						<Button onClick={() => void saveTable()} variant="contained">
							Save
						</Button>
					</DialogActions>
				</Dialog>
			</>,
		);
	}

	if (!selected.childGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Database</Typography>
					<Typography color="#4CAF50">{selected.nodeName}</Typography>
				</Breadcrumbs>
				<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
					<Typography variant="h5">Columns</Typography>
					<Button
						variant="contained"
						onClick={() => {
							setColumnDraft({
								keyGuid: '',
								name: '',
								typeGuid: types[0]?.guid ?? '',
								ordinal: columns.length + 1,
								isNullable: true,
								isPrimaryKey: false,
								isIdentity: false,
								defaultValue: '',
								maxLength: '',
							});
							setColumnDialogOpen(true);
						}}
					>
						Add Column
					</Button>
				</Box>
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>#</TableCell>
							<TableCell>Name</TableCell>
							<TableCell>Type</TableCell>
							<TableCell>PK</TableCell>
							<TableCell>Nullable</TableCell>
							<TableCell>Identity</TableCell>
							<TableCell>Default</TableCell>
							<TableCell>Max Length</TableCell>
							<TableCell align="right">Actions</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{columns.map((column) => (
							<TableRow key={column.guid} hover>
								<TableCell>{column.ordinal}</TableCell>
								<TableCell>
									<Button
										variant="text"
										onClick={() =>
											selectNode?.({
												categoryGuid: selected.categoryGuid,
												categoryName: selected.categoryName,
												nodeGuid: selected.nodeGuid,
												nodeName: selected.nodeName,
												childGuid: column.guid,
												childName: column.name,
											})
										}
									>
										{column.name}
									</Button>
								</TableCell>
								<TableCell>{column.typeName ?? ''}</TableCell>
								<TableCell>{column.isPrimaryKey ? '✓' : ''}</TableCell>
								<TableCell>{column.isNullable ? '✓' : ''}</TableCell>
								<TableCell>{column.pub_is_identity ? '✓' : ''}</TableCell>
								<TableCell>{column.pub_default ?? ''}</TableCell>
								<TableCell>{column.maxLength ?? ''}</TableCell>
								<TableCell align="right">
									<IconButton
										onClick={() => {
											setColumnDraft({
												keyGuid: column.guid,
												name: column.name,
												typeGuid: column.ref_type_guid ?? '',
												ordinal: column.ordinal,
												isNullable: column.isNullable,
												isPrimaryKey: column.isPrimaryKey,
												isIdentity: Boolean(column.pub_is_identity),
												defaultValue: column.pub_default ?? '',
												maxLength: column.maxLength === null ? '' : String(column.maxLength),
											});
											setColumnDialogOpen(true);
										}}
									>
										<EditIcon fontSize="small" />
									</IconButton>
									<IconButton
										onClick={async () => {
											await deleteDatabaseColumn(column.guid);
											await refreshColumns();
										}}
									>
										<DeleteIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
				<Dialog open={columnDialogOpen} onClose={() => setColumnDialogOpen(false)}>
					<DialogTitle>{columnDraft.keyGuid ? 'Edit Column' : 'Add Column'}</DialogTitle>
					<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 360, pt: '12px !important' }}>
						<TextField
							label="Name"
							value={columnDraft.name}
							onChange={(event) => setColumnDraft((prev) => ({ ...prev, name: event.target.value }))}
						/>
						<Select
							value={columnDraft.typeGuid}
							onChange={(event) => setColumnDraft((prev) => ({ ...prev, typeGuid: String(event.target.value) }))}
						>
							{types.map((type) => (
								<MenuItem key={type.guid} value={type.guid}>
									{type.name}
								</MenuItem>
							))}
						</Select>
						<TextField
							type="number"
							label="Ordinal"
							value={columnDraft.ordinal}
							onChange={(event) =>
								setColumnDraft((prev) => ({ ...prev, ordinal: Number(event.target.value) || 1 }))
							}
						/>
						<TextField
							label="Default"
							value={columnDraft.defaultValue}
							onChange={(event) => setColumnDraft((prev) => ({ ...prev, defaultValue: event.target.value }))}
						/>
						<TextField
							type="number"
							label="Max Length"
							value={columnDraft.maxLength}
							onChange={(event) => setColumnDraft((prev) => ({ ...prev, maxLength: event.target.value }))}
						/>
						<FormControlLabel
							control={
								<Switch
									checked={columnDraft.isNullable}
									onChange={(event) => setColumnDraft((prev) => ({ ...prev, isNullable: event.target.checked }))}
								/>
							}
							label="Nullable"
						/>
						<FormControlLabel
							control={
								<Switch
									checked={columnDraft.isPrimaryKey}
									onChange={(event) =>
										setColumnDraft((prev) => ({ ...prev, isPrimaryKey: event.target.checked }))
									}
								/>
							}
							label="Primary Key"
						/>
						<FormControlLabel
							control={
								<Switch
									checked={columnDraft.isIdentity}
									onChange={(event) => setColumnDraft((prev) => ({ ...prev, isIdentity: event.target.checked }))}
								/>
							}
							label="Identity"
						/>
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setColumnDialogOpen(false)}>Cancel</Button>
						<Button onClick={() => void saveColumn()} variant="contained">
							Save
						</Button>
					</DialogActions>
				</Dialog>
			</>,
		);
	}

	return renderFrame(
		<>
			<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
				<Typography color="#4CAF50">Database</Typography>
				<Typography color="#4CAF50">{selected.nodeName}</Typography>
				<Typography color="#4CAF50">{selected.childName}</Typography>
			</Breadcrumbs>
			<Typography variant="h6" sx={{ mb: 1 }}>
				Column Details
			</Typography>
			{selectedColumn ? (
				<Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(220px, 1fr))', gap: 1, maxWidth: 900 }}>
					<TextField
						label="Column Name"
						value={columnDraft.name || selectedColumn.name}
						onChange={(event) => setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, name: event.target.value }))}
					/>
					<TextField
						type="number"
						label="Ordinal"
						value={columnDraft.keyGuid ? columnDraft.ordinal : selectedColumn.ordinal}
						onChange={(event) =>
							setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, ordinal: Number(event.target.value) || 1 }))
						}
					/>
					<Select
						value={columnDraft.typeGuid || selectedColumn.ref_type_guid || ''}
						onChange={(event) =>
							setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, typeGuid: String(event.target.value) }))
						}
					>
						{types.map((type) => (
							<MenuItem key={type.guid} value={type.guid}>
								{type.name}
							</MenuItem>
						))}
					</Select>
					<TextField
						label="Default Value"
						value={columnDraft.keyGuid ? columnDraft.defaultValue : selectedColumn.pub_default || ''}
						onChange={(event) =>
							setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, defaultValue: event.target.value }))
						}
					/>
					<TextField
						type="number"
						label="Max Length"
						value={columnDraft.keyGuid ? columnDraft.maxLength : selectedColumn.maxLength || ''}
						onChange={(event) =>
							setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, maxLength: event.target.value }))
						}
					/>
					<FormControlLabel
						control={
							<Switch
								checked={columnDraft.keyGuid ? columnDraft.isNullable : selectedColumn.isNullable}
								onChange={(event) =>
									setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, isNullable: event.target.checked }))
								}
							/>
						}
						label="Nullable"
					/>
					<FormControlLabel
						control={
							<Switch
								checked={columnDraft.keyGuid ? columnDraft.isPrimaryKey : selectedColumn.isPrimaryKey}
								onChange={(event) =>
									setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, isPrimaryKey: event.target.checked }))
								}
							/>
						}
						label="Primary Key"
					/>
					<FormControlLabel
						control={
							<Switch
								checked={columnDraft.keyGuid ? columnDraft.isIdentity : Boolean(selectedColumn.pub_is_identity)}
								onChange={(event) =>
									setColumnDraft((prev) => ({ ...prev, keyGuid: selectedColumn.guid, isIdentity: event.target.checked }))
								}
							/>
						}
						label="Identity"
					/>
				</Box>
			) : null}
			<Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
				<Button variant="contained" onClick={() => void saveColumn()}>
					Save
				</Button>
				<Button
					color="error"
					onClick={async () => {
						if (!selected.childGuid) {
							return;
						}
						await deleteDatabaseColumn(selected.childGuid);
						selectNode?.({ ...selected, childGuid: null, childName: null });
						await refreshColumns();
					}}
				>
					Delete
				</Button>
				<Button onClick={() => selectNode?.({ ...selected, childGuid: null, childName: null })}>Back to Table</Button>
			</Box>
		</>,
	);
}
