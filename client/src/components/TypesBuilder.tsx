import { useCallback, useEffect, useMemo, useState } from 'react';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
	Box,
	Breadcrumbs,
	Button,
	Checkbox,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	IconButton,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableRow,
	TextField,
	Typography,
} from '@mui/material';

import {
	deleteType,
	getTypeControls,
	readObjectTreeDetail,
	upsertType,
} from '../api/rpc';
import type { SelectedNode } from './Workbench';

const TYPES_TABLE_GUID = '73377644-3E86-5FE6-B982-0B224749C358';

interface TypesBuilderProps {
	data: Record<string, unknown>;
	selected: SelectedNode;
}

interface TypeRow {
	key_guid: string;
	pub_name: string;
	pub_mssql_type: string;
	pub_postgresql_type?: string | null;
	pub_mysql_type?: string | null;
	pub_python_type: string;
	pub_typescript_type: string;
	pub_json_type: string;
	pub_odbc_type_code?: number | null;
	pub_max_length?: number | null;
	pub_notes?: string | null;
}

interface TypeControlBinding {
	guid: string;
	componentName: string;
	isDefault: boolean;
}

interface TypeDraft {
	keyGuid: string;
	name: string;
	mssqlType: string;
	postgresqlType: string;
	mysqlType: string;
	pythonType: string;
	typescriptType: string;
	jsonType: string;
	odbcTypeCode: string;
	maxLength: string;
	notes: string;
}

const EMPTY_DRAFT: TypeDraft = {
	keyGuid: '',
	name: '',
	mssqlType: '',
	postgresqlType: '',
	mysqlType: '',
	pythonType: '',
	typescriptType: '',
	jsonType: '',
	odbcTypeCode: '',
	maxLength: '',
	notes: '',
};

export function TypesBuilder({ data, selected }: TypesBuilderProps): JSX.Element {
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [types, setTypes] = useState<TypeRow[]>([]);
	const [bindings, setBindings] = useState<TypeControlBinding[]>([]);
	const [dialogOpen, setDialogOpen] = useState(false);
	const [draft, setDraft] = useState<TypeDraft>(EMPTY_DRAFT);

	const selectedType = useMemo(
		() => types.find((row) => row.key_guid === selected.nodeGuid) ?? null,
		[types, selected.nodeGuid],
	);

	const refreshTypes = useCallback(async (): Promise<void> => {
		const detail = await readObjectTreeDetail(TYPES_TABLE_GUID, 1000);
		const rows = Array.isArray(detail.rows)
			? detail.rows.map((row) => {
					const payload = row as Record<string, unknown>;
					return {
						key_guid: String(payload.key_guid ?? ''),
						pub_name: String(payload.pub_name ?? ''),
						pub_mssql_type: String(payload.pub_mssql_type ?? ''),
						pub_postgresql_type: payload.pub_postgresql_type ? String(payload.pub_postgresql_type) : null,
						pub_mysql_type: payload.pub_mysql_type ? String(payload.pub_mysql_type) : null,
						pub_python_type: String(payload.pub_python_type ?? ''),
						pub_typescript_type: String(payload.pub_typescript_type ?? ''),
						pub_json_type: String(payload.pub_json_type ?? ''),
						pub_odbc_type_code: payload.pub_odbc_type_code ? Number(payload.pub_odbc_type_code) : null,
						pub_max_length: payload.pub_max_length ? Number(payload.pub_max_length) : null,
						pub_notes: payload.pub_notes ? String(payload.pub_notes) : null,
					};
				})
			: [];
		setTypes(rows);
	}, []);

	const refreshBindings = useCallback(async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setBindings([]);
			return;
		}
		const rows = await getTypeControls(selected.nodeGuid);
		setBindings(rows);
	}, [selected.nodeGuid]);

	useEffect(() => {
		void refreshTypes();
	}, [refreshTypes]);

	useEffect(() => {
		void refreshBindings();
	}, [refreshBindings]);

	const renderFrame = (content: JSX.Element): JSX.Element => (
		<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, color: '#FFFFFF' }}>{content}</Box>
	);

	const openEditDialog = (row: TypeRow): void => {
		setDraft({
			keyGuid: row.key_guid,
			name: row.pub_name,
			mssqlType: row.pub_mssql_type,
			postgresqlType: row.pub_postgresql_type ?? '',
			mysqlType: row.pub_mysql_type ?? '',
			pythonType: row.pub_python_type,
			typescriptType: row.pub_typescript_type,
			jsonType: row.pub_json_type,
			odbcTypeCode: row.pub_odbc_type_code === null || row.pub_odbc_type_code === undefined ? '' : String(row.pub_odbc_type_code),
			maxLength: row.pub_max_length === null || row.pub_max_length === undefined ? '' : String(row.pub_max_length),
			notes: row.pub_notes ?? '',
		});
		setDialogOpen(true);
	};

	const saveDraft = async (): Promise<void> => {
		await upsertType({
			keyGuid: draft.keyGuid || null,
			name: draft.name,
			mssqlType: draft.mssqlType,
			postgresqlType: draft.postgresqlType || null,
			mysqlType: draft.mysqlType || null,
			pythonType: draft.pythonType,
			typescriptType: draft.typescriptType,
			jsonType: draft.jsonType,
			odbcTypeCode: draft.odbcTypeCode === '' ? null : Number(draft.odbcTypeCode),
			maxLength: draft.maxLength === '' ? null : Number(draft.maxLength),
			notes: draft.notes || null,
		});
		setDialogOpen(false);
		setDraft(EMPTY_DRAFT);
		await refreshTypes();
		if (selected.nodeGuid) {
			await refreshBindings();
		}
	};

	const saveDetail = async (): Promise<void> => {
		if (!selected.nodeGuid) {
			return;
		}
		await upsertType({
			keyGuid: selected.nodeGuid,
			name: draft.name,
			mssqlType: draft.mssqlType,
			postgresqlType: draft.postgresqlType || null,
			mysqlType: draft.mysqlType || null,
			pythonType: draft.pythonType,
			typescriptType: draft.typescriptType,
			jsonType: draft.jsonType,
			odbcTypeCode: draft.odbcTypeCode === '' ? null : Number(draft.odbcTypeCode),
			maxLength: draft.maxLength === '' ? null : Number(draft.maxLength),
			notes: draft.notes || null,
		});
		await refreshTypes();
	};

	useEffect(() => {
		if (!selectedType) {
			return;
		}
		setDraft({
			keyGuid: selectedType.key_guid,
			name: selectedType.pub_name,
			mssqlType: selectedType.pub_mssql_type,
			postgresqlType: selectedType.pub_postgresql_type ?? '',
			mysqlType: selectedType.pub_mysql_type ?? '',
			pythonType: selectedType.pub_python_type,
			typescriptType: selectedType.pub_typescript_type,
			jsonType: selectedType.pub_json_type,
			odbcTypeCode:
				selectedType.pub_odbc_type_code === null || selectedType.pub_odbc_type_code === undefined
					? ''
					: String(selectedType.pub_odbc_type_code),
			maxLength:
				selectedType.pub_max_length === null || selectedType.pub_max_length === undefined
					? ''
					: String(selectedType.pub_max_length),
			notes: selectedType.pub_notes ?? '',
		});
	}, [selectedType]);

	if (!selected.nodeGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Types</Typography>
				</Breadcrumbs>
				<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
					<Typography variant="h5">Types</Typography>
					<Button
						variant="contained"
						onClick={() => {
							setDraft(EMPTY_DRAFT);
							setDialogOpen(true);
						}}
					>
						New Type
					</Button>
				</Box>
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>Name</TableCell>
							<TableCell>MSSQL</TableCell>
							<TableCell>Python</TableCell>
							<TableCell>TypeScript</TableCell>
							<TableCell>JSON</TableCell>
							<TableCell align="right">Actions</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{types.map((row) => (
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
								<TableCell>{row.pub_mssql_type}</TableCell>
								<TableCell>{row.pub_python_type}</TableCell>
								<TableCell>{row.pub_typescript_type}</TableCell>
								<TableCell>{row.pub_json_type}</TableCell>
								<TableCell align="right">
									<IconButton onClick={() => openEditDialog(row)}>
										<EditIcon fontSize="small" />
									</IconButton>
									<IconButton
										onClick={async () => {
											await deleteType(row.key_guid);
											await refreshTypes();
										}}
									>
										<DeleteIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
				<Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
					<DialogTitle>{draft.keyGuid ? 'Edit Type' : 'New Type'}</DialogTitle>
					<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 480, pt: '12px !important' }}>
						<TextField label="Type Name" value={draft.name} onChange={(event) => setDraft((prev) => ({ ...prev, name: event.target.value }))} />
						<TextField label="MSSQL Type" value={draft.mssqlType} onChange={(event) => setDraft((prev) => ({ ...prev, mssqlType: event.target.value }))} />
						<TextField label="PostgreSQL Type" value={draft.postgresqlType} onChange={(event) => setDraft((prev) => ({ ...prev, postgresqlType: event.target.value }))} />
						<TextField label="MySQL Type" value={draft.mysqlType} onChange={(event) => setDraft((prev) => ({ ...prev, mysqlType: event.target.value }))} />
						<TextField label="Python Type" value={draft.pythonType} onChange={(event) => setDraft((prev) => ({ ...prev, pythonType: event.target.value }))} />
						<TextField label="TypeScript Type" value={draft.typescriptType} onChange={(event) => setDraft((prev) => ({ ...prev, typescriptType: event.target.value }))} />
						<TextField label="JSON Type" value={draft.jsonType} onChange={(event) => setDraft((prev) => ({ ...prev, jsonType: event.target.value }))} />
						<TextField type="number" label="ODBC Type Code" value={draft.odbcTypeCode} onChange={(event) => setDraft((prev) => ({ ...prev, odbcTypeCode: event.target.value }))} />
						<TextField type="number" label="Max Length" value={draft.maxLength} onChange={(event) => setDraft((prev) => ({ ...prev, maxLength: event.target.value }))} />
						<TextField label="Notes" multiline minRows={3} value={draft.notes} onChange={(event) => setDraft((prev) => ({ ...prev, notes: event.target.value }))} />
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setDialogOpen(false)}>Cancel</Button>
						<Button onClick={() => void saveDraft()} variant="contained">
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
				<Typography color="#4CAF50">Types</Typography>
				<Typography color="#4CAF50">{selectedType?.pub_name ?? selected.nodeName ?? ''}</Typography>
			</Breadcrumbs>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
				<Typography variant="h5">Type Properties</Typography>
				<Box sx={{ display: 'flex', gap: 1 }}>
					<Button
						variant="outlined"
						onClick={() =>
							selectNode?.({
								categoryGuid: selected.categoryGuid,
								categoryName: selected.categoryName,
								nodeGuid: null,
								nodeName: null,
								childGuid: null,
								childName: null,
							})
						}
					>
						Back
					</Button>
					<Button variant="contained" onClick={() => void saveDetail()}>
						Save
					</Button>
					<Button
						color="error"
						variant="outlined"
						onClick={async () => {
							if (!selected.nodeGuid) {
								return;
							}
							await deleteType(selected.nodeGuid);
							await refreshTypes();
							selectNode?.({
								categoryGuid: selected.categoryGuid,
								categoryName: selected.categoryName,
								nodeGuid: null,
								nodeName: null,
								childGuid: null,
								childName: null,
							});
						}}
					>
						Delete
					</Button>
				</Box>
			</Box>
			<Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(220px, 1fr))', gap: 1, maxWidth: 900, mb: 2 }}>
				<TextField label="Type Name" value={draft.name} onChange={(event) => setDraft((prev) => ({ ...prev, name: event.target.value }))} />
				<TextField label="MSSQL Type" value={draft.mssqlType} onChange={(event) => setDraft((prev) => ({ ...prev, mssqlType: event.target.value }))} />
				<TextField label="PostgreSQL Type" value={draft.postgresqlType} onChange={(event) => setDraft((prev) => ({ ...prev, postgresqlType: event.target.value }))} />
				<TextField label="MySQL Type" value={draft.mysqlType} onChange={(event) => setDraft((prev) => ({ ...prev, mysqlType: event.target.value }))} />
				<TextField label="Python Type" value={draft.pythonType} onChange={(event) => setDraft((prev) => ({ ...prev, pythonType: event.target.value }))} />
				<TextField label="TypeScript Type" value={draft.typescriptType} onChange={(event) => setDraft((prev) => ({ ...prev, typescriptType: event.target.value }))} />
				<TextField label="JSON Type" value={draft.jsonType} onChange={(event) => setDraft((prev) => ({ ...prev, jsonType: event.target.value }))} />
				<TextField type="number" label="ODBC Type Code" value={draft.odbcTypeCode} onChange={(event) => setDraft((prev) => ({ ...prev, odbcTypeCode: event.target.value }))} />
				<TextField type="number" label="Max Length" value={draft.maxLength} onChange={(event) => setDraft((prev) => ({ ...prev, maxLength: event.target.value }))} />
				<TextField label="Notes" multiline minRows={3} value={draft.notes} onChange={(event) => setDraft((prev) => ({ ...prev, notes: event.target.value }))} sx={{ gridColumn: '1 / -1' }} />
			</Box>
			<Typography variant="h6" sx={{ mb: 1 }}>
				Component Bindings
			</Typography>
			<Table size="small" sx={{ maxWidth: 700, '& td, & th': { borderColor: '#1A1A1A' } }}>
				<TableHead>
					<TableRow>
						<TableCell>Component</TableCell>
						<TableCell>Is Default</TableCell>
					</TableRow>
				</TableHead>
				<TableBody>
					{bindings.map((binding) => (
						<TableRow key={binding.guid} hover>
							<TableCell>{binding.componentName}</TableCell>
							<TableCell>
								<Checkbox checked={binding.isDefault} disabled size="small" />
							</TableCell>
						</TableRow>
					))}
				</TableBody>
			</Table>
		</>,
	);
}
