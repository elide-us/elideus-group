import { useCallback, useEffect, useMemo, useState } from 'react';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
	Box,
	Breadcrumbs,
	Button,
	Chip,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	FormControlLabel,
	IconButton,
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
	deleteModuleMethod,
	getMethodContract,
	getModuleMethods,
	readObjectTreeDetail,
	type MethodContract,
	type ModuleMethod,
	upsertModule,
	upsertModuleMethod,
} from '../api/rpc';
import type { SelectedNode } from './Workbench';

const MODULES_TABLE_GUID = 'D039D8FB-3F95-5A66-B7FB-AB4BA1301FEA';

interface ModulesBuilderProps {
	data: Record<string, unknown>;
	selected: SelectedNode;
}

interface ModuleRow {
	key_guid: string;
	pub_name: string;
	pub_state_attr: string;
	pub_module_path: string;
	pub_is_active: boolean;
	pub_description: string | null;
}

interface ModuleDraft {
	keyGuid: string;
	description: string;
	isActive: boolean;
}

interface MethodDraft {
	keyGuid: string;
	name: string;
	description: string;
	isActive: boolean;
}

const EMPTY_MODULE_DRAFT: ModuleDraft = {
	keyGuid: '',
	description: '',
	isActive: true,
};

const EMPTY_METHOD_DRAFT: MethodDraft = {
	keyGuid: '',
	name: '',
	description: '',
	isActive: true,
};

export function ModulesBuilder({ data, selected }: ModulesBuilderProps): JSX.Element {
	const selectNode = data.__selectNode as ((node: SelectedNode | null) => void) | undefined;
	const [modules, setModules] = useState<ModuleRow[]>([]);
	const [methods, setMethods] = useState<ModuleMethod[]>([]);
	const [contracts, setContracts] = useState<MethodContract[]>([]);
	const [moduleDialogOpen, setModuleDialogOpen] = useState(false);
	const [methodDialogOpen, setMethodDialogOpen] = useState(false);
	const [moduleDialogDraft, setModuleDialogDraft] = useState<ModuleDraft>(EMPTY_MODULE_DRAFT);
	const [methodDialogDraft, setMethodDialogDraft] = useState<MethodDraft>(EMPTY_METHOD_DRAFT);
	const [moduleDetailDraft, setModuleDetailDraft] = useState<ModuleDraft>(EMPTY_MODULE_DRAFT);
	const [methodDetailDraft, setMethodDetailDraft] = useState<MethodDraft>(EMPTY_METHOD_DRAFT);

	const selectedModule = useMemo(
		() => modules.find((row) => row.key_guid === selected.nodeGuid) ?? null,
		[modules, selected.nodeGuid],
	);

	const selectedMethod = useMemo(
		() => methods.find((row) => row.guid === selected.childGuid) ?? null,
		[methods, selected.childGuid],
	);

	const refreshModules = useCallback(async (): Promise<void> => {
		const detail = await readObjectTreeDetail(MODULES_TABLE_GUID, 1000);
		const rows = Array.isArray(detail.rows)
			? detail.rows.map((row) => {
					const payload = row as Record<string, unknown>;
					return {
						key_guid: String(payload.key_guid ?? ''),
						pub_name: String(payload.pub_name ?? ''),
						pub_state_attr: String(payload.pub_state_attr ?? ''),
						pub_module_path: String(payload.pub_module_path ?? ''),
						pub_is_active: Boolean(payload.pub_is_active ?? false),
						pub_description: payload.pub_description ? String(payload.pub_description) : null,
					};
			  })
			: [];
		setModules(rows);
	}, []);

	const refreshMethods = useCallback(async (): Promise<void> => {
		if (!selected.nodeGuid) {
			setMethods([]);
			return;
		}
		const rows = await getModuleMethods(selected.nodeGuid);
		setMethods(rows);
	}, [selected.nodeGuid]);

	const refreshContracts = useCallback(async (): Promise<void> => {
		if (!selected.childGuid) {
			setContracts([]);
			return;
		}
		const rows = await getMethodContract(selected.childGuid);
		setContracts(rows);
	}, [selected.childGuid]);

	useEffect(() => {
		void refreshModules();
	}, [refreshModules]);

	useEffect(() => {
		void refreshMethods();
	}, [refreshMethods]);

	useEffect(() => {
		void refreshContracts();
	}, [refreshContracts]);

	useEffect(() => {
		if (!selectedModule) {
			setModuleDetailDraft(EMPTY_MODULE_DRAFT);
			return;
		}
		setModuleDetailDraft({
			keyGuid: selectedModule.key_guid,
			description: selectedModule.pub_description ?? '',
			isActive: selectedModule.pub_is_active,
		});
	}, [selectedModule]);

	useEffect(() => {
		if (!selectedMethod) {
			setMethodDetailDraft(EMPTY_METHOD_DRAFT);
			return;
		}
		setMethodDetailDraft({
			keyGuid: selectedMethod.guid,
			name: selectedMethod.name,
			description: selectedMethod.description ?? '',
			isActive: selectedMethod.isActive,
		});
	}, [selectedMethod]);

	const renderFrame = (content: JSX.Element): JSX.Element => (
		<Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2, color: '#FFFFFF' }}>{content}</Box>
	);

	const saveModuleDraft = async (draft: ModuleDraft): Promise<void> => {
		await upsertModule({
			keyGuid: draft.keyGuid,
			description: draft.description || null,
			isActive: draft.isActive,
		});
		await refreshModules();
	};

	const saveMethodDraft = async (draft: MethodDraft): Promise<void> => {
		if (!selected.nodeGuid) {
			return;
		}
		await upsertModuleMethod({
			keyGuid: draft.keyGuid || null,
			moduleGuid: selected.nodeGuid,
			name: draft.name,
			description: draft.description || null,
			isActive: draft.isActive,
		});
		await refreshMethods();
	};

	if (!selected.nodeGuid) {
		return renderFrame(
			<>
				<Breadcrumbs sx={{ color: '#4CAF50', mb: 1 }}>
					<Typography color="#4CAF50">Modules</Typography>
				</Breadcrumbs>
				<Typography variant="h5" sx={{ mb: 1 }}>
					Modules
				</Typography>
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>Name</TableCell>
							<TableCell>State Attr</TableCell>
							<TableCell>Module Path</TableCell>
							<TableCell>Active</TableCell>
							<TableCell>Description</TableCell>
							<TableCell align="right">Actions</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{modules.map((row) => (
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
								<TableCell>{row.pub_state_attr}</TableCell>
								<TableCell>{row.pub_module_path}</TableCell>
								<TableCell>{row.pub_is_active ? 'Yes' : 'No'}</TableCell>
								<TableCell>{row.pub_description ?? '—'}</TableCell>
								<TableCell align="right">
									<IconButton
										onClick={() => {
											setModuleDialogDraft({
												keyGuid: row.key_guid,
												description: row.pub_description ?? '',
												isActive: row.pub_is_active,
											});
											setModuleDialogOpen(true);
										}}
									>
										<EditIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
				<Dialog open={moduleDialogOpen} onClose={() => setModuleDialogOpen(false)}>
					<DialogTitle>Edit Module</DialogTitle>
					<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 360, pt: '12px !important' }}>
						<TextField
							label="Description"
							multiline
							minRows={2}
							value={moduleDialogDraft.description}
							onChange={(event) =>
								setModuleDialogDraft((prev) => ({ ...prev, description: event.target.value }))
							}
						/>
						<FormControlLabel
							label="Active"
							control={
								<Switch
									checked={moduleDialogDraft.isActive}
									onChange={(_, checked) =>
										setModuleDialogDraft((prev) => ({ ...prev, isActive: checked }))
									}
								/>
							}
						/>
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setModuleDialogOpen(false)}>Cancel</Button>
						<Button
							onClick={async () => {
								await saveModuleDraft(moduleDialogDraft);
								setModuleDialogOpen(false);
								setModuleDialogDraft(EMPTY_MODULE_DRAFT);
							}}
						>
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
					<Button
						variant="text"
						sx={{ color: '#4CAF50', p: 0, minWidth: 'auto' }}
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
						Modules
					</Button>
					<Typography color="#4CAF50">{selected.nodeName ?? selectedModule?.pub_name ?? ''}</Typography>
				</Breadcrumbs>
				<Typography variant="h5" sx={{ mb: 1 }}>
					Module Detail
				</Typography>
				<Box sx={{ display: 'grid', gap: 1, maxWidth: 640, mb: 2 }}>
					<TextField label="Name" value={selectedModule?.pub_name ?? ''} InputProps={{ readOnly: true }} />
					<TextField label="State Attr" value={selectedModule?.pub_state_attr ?? ''} InputProps={{ readOnly: true }} />
					<TextField label="Module Path" value={selectedModule?.pub_module_path ?? ''} InputProps={{ readOnly: true }} />
					<TextField
						label="Description"
						multiline
						minRows={2}
						value={moduleDetailDraft.description}
						onChange={(event) => setModuleDetailDraft((prev) => ({ ...prev, description: event.target.value }))}
					/>
					<FormControlLabel
						label="Active"
						control={
							<Switch
								checked={moduleDetailDraft.isActive}
								onChange={(_, checked) => setModuleDetailDraft((prev) => ({ ...prev, isActive: checked }))}
							/>
						}
					/>
					<Box>
						<Button
							variant="contained"
							onClick={async () => {
								await saveModuleDraft({ ...moduleDetailDraft, keyGuid: selected.nodeGuid ?? '' });
							}}
						>
							Save Module
						</Button>
					</Box>
				</Box>

				<Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
					<Typography variant="h6">Methods</Typography>
					<Button
						variant="contained"
						onClick={() => {
							setMethodDialogDraft(EMPTY_METHOD_DRAFT);
							setMethodDialogOpen(true);
						}}
					>
						Add Method
					</Button>
				</Box>
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>Name</TableCell>
							<TableCell>Description</TableCell>
							<TableCell>Request Model</TableCell>
							<TableCell>Response Model</TableCell>
							<TableCell>Active</TableCell>
							<TableCell align="right">Actions</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{methods.map((method) => (
							<TableRow key={method.guid} hover>
								<TableCell>
									<Button
										variant="text"
										onClick={() =>
											selectNode?.({
												categoryGuid: selected.categoryGuid,
												categoryName: selected.categoryName,
												nodeGuid: selected.nodeGuid,
												nodeName: selected.nodeName,
												childGuid: method.guid,
												childName: method.name,
											})
										}
									>
										{method.name}
									</Button>
								</TableCell>
								<TableCell>{method.description ?? '—'}</TableCell>
								<TableCell>{method.requestModelName ?? '—'}</TableCell>
								<TableCell>{method.responseModelName ?? '—'}</TableCell>
								<TableCell>{method.isActive ? 'Yes' : 'No'}</TableCell>
								<TableCell align="right">
									<IconButton
										onClick={() => {
											setMethodDialogDraft({
												keyGuid: method.guid,
												name: method.name,
												description: method.description ?? '',
												isActive: method.isActive,
											});
											setMethodDialogOpen(true);
										}}
									>
										<EditIcon fontSize="small" />
									</IconButton>
									<IconButton
										onClick={async () => {
											await deleteModuleMethod(method.guid);
											await refreshMethods();
										}}
									>
										<DeleteIcon fontSize="small" />
									</IconButton>
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
				<Dialog open={methodDialogOpen} onClose={() => setMethodDialogOpen(false)}>
					<DialogTitle>{methodDialogDraft.keyGuid ? 'Edit Method' : 'Add Method'}</DialogTitle>
					<DialogContent sx={{ display: 'grid', gap: 1, minWidth: 420, pt: '12px !important' }}>
						<TextField
							label="Name"
							value={methodDialogDraft.name}
							onChange={(event) => setMethodDialogDraft((prev) => ({ ...prev, name: event.target.value }))}
						/>
						<TextField
							label="Description"
							multiline
							minRows={2}
							value={methodDialogDraft.description}
							onChange={(event) =>
								setMethodDialogDraft((prev) => ({ ...prev, description: event.target.value }))
							}
						/>
						<FormControlLabel
							label="Active"
							control={
								<Switch
									checked={methodDialogDraft.isActive}
									onChange={(_, checked) =>
										setMethodDialogDraft((prev) => ({ ...prev, isActive: checked }))
									}
								/>
							}
						/>
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setMethodDialogOpen(false)}>Cancel</Button>
						<Button
							onClick={async () => {
								await saveMethodDraft(methodDialogDraft);
								setMethodDialogOpen(false);
								setMethodDialogDraft(EMPTY_METHOD_DRAFT);
							}}
						>
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
				<Button
					variant="text"
					sx={{ color: '#4CAF50', p: 0, minWidth: 'auto' }}
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
					Modules
				</Button>
				<Button
					variant="text"
					sx={{ color: '#4CAF50', p: 0, minWidth: 'auto' }}
					onClick={() => selectNode?.({ ...selected, childGuid: null, childName: null })}
				>
					{selected.nodeName ?? selectedModule?.pub_name ?? ''}
				</Button>
				<Typography color="#4CAF50">{selected.childName ?? selectedMethod?.name ?? ''}</Typography>
			</Breadcrumbs>
			<Typography variant="h5" sx={{ mb: 1 }}>
				Method Detail
			</Typography>
			<Box sx={{ display: 'grid', gap: 1, maxWidth: 640, mb: 2 }}>
				<TextField
					label="Name"
					value={methodDetailDraft.name}
					onChange={(event) => setMethodDetailDraft((prev) => ({ ...prev, name: event.target.value }))}
				/>
				<TextField
					label="Description"
					multiline
					minRows={2}
					value={methodDetailDraft.description}
					onChange={(event) => setMethodDetailDraft((prev) => ({ ...prev, description: event.target.value }))}
				/>
				<FormControlLabel
					label="Active"
					control={
						<Switch
							checked={methodDetailDraft.isActive}
							onChange={(_, checked) => setMethodDetailDraft((prev) => ({ ...prev, isActive: checked }))}
						/>
					}
				/>
				<Box sx={{ display: 'flex', gap: 1 }}>
					<Button
						variant="contained"
						onClick={async () => {
							if (!selected.nodeGuid || !selected.childGuid) {
								return;
							}
							await upsertModuleMethod({
								keyGuid: selected.childGuid,
								moduleGuid: selected.nodeGuid,
								name: methodDetailDraft.name,
								description: methodDetailDraft.description || null,
								isActive: methodDetailDraft.isActive,
							});
							await refreshMethods();
						}}
					>
						Save Method
					</Button>
					<Button variant="outlined" onClick={() => selectNode?.({ ...selected, childGuid: null, childName: null })}>
						Back
					</Button>
					<Button
						color="error"
						variant="outlined"
						onClick={async () => {
							if (!selected.childGuid) {
								return;
							}
							await deleteModuleMethod(selected.childGuid);
							await refreshMethods();
							selectNode?.({ ...selected, childGuid: null, childName: null });
						}}
					>
						Delete Method
					</Button>
				</Box>
			</Box>

			<Typography variant="h6" sx={{ mb: 1 }}>
				Contract
			</Typography>
			{contracts.length === 0 ? (
				<Typography color="text.secondary">No contract defined</Typography>
			) : (
				<Table size="small" sx={{ '& td, & th': { borderColor: '#1A1A1A' } }}>
					<TableHead>
						<TableRow>
							<TableCell>Contract</TableCell>
							<TableCell>Version</TableCell>
							<TableCell>Async</TableCell>
							<TableCell>Internal</TableCell>
							<TableCell>Request Model</TableCell>
							<TableCell>Response Model</TableCell>
						</TableRow>
					</TableHead>
					<TableBody>
						{contracts.map((contract) => (
							<TableRow key={contract.contractGuid}>
								<TableCell>{contract.contractName}</TableCell>
								<TableCell>{contract.version}</TableCell>
								<TableCell>{contract.isAsync ? 'Yes' : 'No'}</TableCell>
								<TableCell>{contract.isInternalOnly ? 'Yes' : 'No'}</TableCell>
								<TableCell>
									{contract.requestModelName ? <Chip size="small" label={contract.requestModelName} /> : '—'}
								</TableCell>
								<TableCell>
									{contract.responseModelName ? <Chip size="small" label={contract.responseModelName} /> : '—'}
								</TableCell>
							</TableRow>
						))}
					</TableBody>
				</Table>
			)}
		</>,
	);
}
