import { Fragment, useCallback, useEffect, useMemo, useState, type JSX } from 'react';
import {
	Box,
	Button,
	Chip,
	Collapse,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	Paper,
	Stack,
	Tab,
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableRow,
	Tabs,
	TextField,
	Tooltip,
	Typography,
} from '@mui/material';
import Notification from '../../components/Notification';
import PageTitle from '../../components/PageTitle';
import { rpcCall } from '../../shared/RpcModels';
import type {
	SystemWorkflowActionItem1,
	SystemWorkflowDetail1,
	SystemWorkflowItem1,
	SystemWorkflowList1,
	SystemWorkflowRunActionItem1,
	SystemWorkflowRunActionList1,
	SystemWorkflowRunItem1,
	SystemWorkflowRunList1,
} from '../../shared/RpcModels';

const WORKFLOW_STATUS_LABELS: Record<number, string> = {
	0: 'Draft',
	1: 'Published',
	2: 'Retired',
};

const WORKFLOW_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning'> = {
	0: 'default',
	1: 'success',
	2: 'warning',
};

const RUN_STATUS_LABELS: Record<number, string> = {
	0: 'Pending',
	1: 'Running',
	2: 'Completed',
	3: 'Failed',
	4: 'Cancelled',
	5: 'Waiting',
	6: 'Paused',
	7: 'Rolling Back',
	8: 'Rolled Back',
	9: 'Rollback Failed',
	10: 'Stalled',
};

const RUN_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
	0: 'info',
	1: 'warning',
	2: 'success',
	3: 'error',
	4: 'error',
	5: 'info',
	6: 'default',
	7: 'warning',
	8: 'error',
	9: 'error',
	10: 'warning',
};

const ACTION_STATUS_LABELS: Record<number, string> = {
	0: 'Pending',
	1: 'Running',
	2: 'Completed',
	3: 'Failed',
	4: 'Cancelled',
	5: 'Waiting',
	6: 'Paused',
	10: 'Stalled',
};

const ACTION_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning' | 'error'> = {
	0: 'default',
	1: 'warning',
	2: 'success',
	3: 'error',
	4: 'error',
	5: 'info' as 'default',
	10: 'warning',
};

const DISPOSITION_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success'> = {
	pure: 'default',
	reversible: 'info',
	irreversible: 'warning',
	idempotent: 'success',
};

const TRIGGER_TYPE_LABELS: Record<number, string> = {
	0: 'Manual',
	1: 'Schedule',
	2: 'RPC',
	3: 'MCP',
	4: 'Discord',
	5: 'Workflow',
	6: 'Webhook',
	7: 'Poll',
};

const ACTIVE_RUN_STATUSES = new Set([0, 1, 5, 7]);

const formatJson = (value: unknown): string => JSON.stringify(value, null, 2);

const getGuidLabel = (guid: unknown): string => {
	const value = String(guid || '');
	return value ? value.slice(0, 8) : '-';
};

const getActionProgressLabel = (run: SystemWorkflowRunItem1): string => {
	const actionIndex = Number(run.action_index || 0);
	const context = run.context as Record<string, any> | null;
	const contextTotal = Number(context?.action_count || context?.total_actions || 0);
	if (contextTotal > 0) {
		return `${actionIndex}/${contextTotal}`;
	}
	return String(actionIndex);
};

const SystemWorkflowsPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [workflows, setWorkflows] = useState<SystemWorkflowItem1[]>([]);
	const [selectedWorkflow, setSelectedWorkflow] = useState<SystemWorkflowDetail1 | null>(null);
	const [workflowDetailOpen, setWorkflowDetailOpen] = useState(false);

	const [runs, setRuns] = useState<SystemWorkflowRunItem1[]>([]);
	const [selectedRun, setSelectedRun] = useState<SystemWorkflowRunItem1 | null>(null);
	const [runActions, setRunActions] = useState<SystemWorkflowRunActionItem1[]>([]);
	const [runDetailOpen, setRunDetailOpen] = useState(false);
	const [expandedRunActionGuid, setExpandedRunActionGuid] = useState<string | null>(null);
	const [showRunPayload, setShowRunPayload] = useState(false);
	const [showRunContext, setShowRunContext] = useState(false);

	const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
	const [submitPayloadText, setSubmitPayloadText] = useState('{}');
	const [submitTriggerRef, setSubmitTriggerRef] = useState('');

	const [notificationOpen, setNotificationOpen] = useState(false);
	const [notificationMessage, setNotificationMessage] = useState('Done');
	const [notificationSeverity, setNotificationSeverity] = useState<'success' | 'info' | 'warning' | 'error'>('success');

	const showNotification = (
		message: string,
		severity: 'success' | 'info' | 'warning' | 'error' = 'success'
	): void => {
		setNotificationMessage(message);
		setNotificationSeverity(severity);
		setNotificationOpen(true);
	};

	const loadWorkflows = useCallback(async (): Promise<void> => {
		const response = await rpcCall<SystemWorkflowList1>('urn:system:workflows:list_workflows:1', {});
		setWorkflows(response.workflows || []);
	}, []);

	const loadWorkflow = useCallback(async (name: string): Promise<void> => {
		const response = await rpcCall<SystemWorkflowDetail1>('urn:system:workflows:get_workflow:1', { name });
		setSelectedWorkflow(response);
		setWorkflowDetailOpen(true);
	}, []);

	const loadRuns = useCallback(async (): Promise<void> => {
		const response = await rpcCall<SystemWorkflowRunList1>('urn:system:workflows:list_runs:1', {});
		setRuns(response.runs || []);
	}, []);

	const loadRunActions = useCallback(async (runGuid: string): Promise<void> => {
		const response = await rpcCall<SystemWorkflowRunActionList1>('urn:system:workflows:list_run_actions:1', { run_guid: runGuid });
		setRunActions(response.actions || []);
	}, []);

	const loadOnMount = useCallback(async (): Promise<void> => {
		try {
			await loadWorkflows();
			setForbidden(false);
		} catch (error: any) {
			if (error?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw error;
		}
	}, [loadWorkflows]);

	useEffect(() => {
		void loadOnMount();
	}, [loadOnMount]);

	useEffect(() => {
		if (tab !== 1) {
			return;
		}
		void loadRuns();
	}, [tab, loadRuns]);

	const hasActiveRuns = useMemo(() => runs.some((run) => ACTIVE_RUN_STATUSES.has(run.status)), [runs]);

	useEffect(() => {
		if (tab !== 1 || !hasActiveRuns) {
			return;
		}
		const intervalId = window.setInterval(() => {
			void loadRuns();
		}, 5000);
		return () => {
			window.clearInterval(intervalId);
		};
	}, [tab, hasActiveRuns, loadRuns]);

	const handleWorkflowRowClick = async (workflow: SystemWorkflowItem1): Promise<void> => {
		if (selectedWorkflow?.name === workflow.name && workflowDetailOpen) {
			setWorkflowDetailOpen(false);
			return;
		}
		await loadWorkflow(workflow.name);
	};

	const handleRunRowClick = async (run: SystemWorkflowRunItem1): Promise<void> => {
		if (selectedRun?.guid === run.guid && runDetailOpen) {
			setRunDetailOpen(false);
			return;
		}
		setSelectedRun(run);
		setExpandedRunActionGuid(null);
		await loadRunActions(run.guid);
		setRunDetailOpen(true);
	};

	const handleSubmitRun = async (): Promise<void> => {
		if (!selectedWorkflow?.name) {
			return;
		}
		let payloadValue: Record<string, any>;
		try {
			payloadValue = JSON.parse(submitPayloadText);
		} catch {
			showNotification('Payload must be valid JSON', 'error');
			return;
		}
		await rpcCall<SystemWorkflowRunItem1>('urn:system:workflows:submit_run:1', {
			workflow_name: selectedWorkflow.name,
			payload: payloadValue,
			trigger_type: 2,
			trigger_ref: submitTriggerRef || null,
		});
		showNotification('Workflow run submitted');
		setSubmitDialogOpen(false);
		setTab(1);
		await loadRuns();
	};

	const handleCancelRun = async (runGuid: string): Promise<void> => {
		if (!window.confirm('Cancel this run?')) {
			return;
		}
		await rpcCall<SystemWorkflowRunItem1>('urn:system:workflows:cancel_run:1', { guid: runGuid });
		showNotification('Run cancelled');
		await loadRuns();
		if (selectedRun?.guid === runGuid) {
			await loadRunActions(runGuid);
		}
	};

	const handleRollbackRun = async (runGuid: string): Promise<void> => {
		if (!window.confirm('Rollback this run?')) {
			return;
		}
		await rpcCall<SystemWorkflowRunItem1>('urn:system:workflows:rollback_run:1', { guid: runGuid });
		showNotification('Rollback started');
		await loadRuns();
		if (selectedRun?.guid === runGuid) {
			await loadRunActions(runGuid);
		}
	};

	const handleResumeRun = async (runGuid: string): Promise<void> => {
		await rpcCall<SystemWorkflowRunItem1>('urn:system:workflows:resume_run:1', { guid: runGuid });
		showNotification('Run resumed');
		await loadRuns();
		if (selectedRun?.guid === runGuid) {
			await loadRunActions(runGuid);
		}
	};

	if (forbidden) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h6">Forbidden</Typography>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Workflow Management</PageTitle>
			<Tabs value={tab} onChange={(_event, value) => setTab(value)}>
				<Tab label="Workflows" />
				<Tab label="Runs" />
			</Tabs>

			{tab === 0 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2, overflowX: 'auto' }}>
						<Table size="small">
							<TableHead>
								<TableRow>
									<TableCell>Name</TableCell>
									<TableCell>Version</TableCell>
									<TableCell>Status</TableCell>
									<TableCell>Active</TableCell>
									<TableCell>Description</TableCell>
									<TableCell>Created</TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{workflows.map((workflow) => {
									const description = String(workflow.description || '');
									const truncatedDescription = description.length > 100 ? `${description.slice(0, 100)}...` : description;
									return (
										<TableRow
											hover
											key={workflow.guid}
											sx={{ cursor: 'pointer' }}
											onClick={() => void handleWorkflowRowClick(workflow)}
										>
											<TableCell>{workflow.name}</TableCell>
											<TableCell>{workflow.version}</TableCell>
											<TableCell>
												<Chip
													label={WORKFLOW_STATUS_LABELS[workflow.status] || String(workflow.status)}
													color={WORKFLOW_STATUS_COLORS[workflow.status] || 'default'}
												/>
											</TableCell>
											<TableCell>{workflow.is_active ? 'Yes' : 'No'}</TableCell>
											<TableCell>
												<Tooltip title={description || '-'}>
													<Typography variant="body2">{truncatedDescription || '-'}</Typography>
												</Tooltip>
											</TableCell>
											<TableCell>{String(workflow.created_on || '-')}</TableCell>
										</TableRow>
									);
								})}
							</TableBody>
						</Table>
					</Paper>

					<Collapse in={workflowDetailOpen && Boolean(selectedWorkflow)}>
						<Paper sx={{ p: 2 }}>
							{selectedWorkflow && (
								<Stack spacing={2}>
									<Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between">
										<Box>
											<Typography variant="h6">{selectedWorkflow.name}</Typography>
											<Typography variant="body2">Version: {selectedWorkflow.version}</Typography>
											<Typography variant="body2">GUID: {selectedWorkflow.guid}</Typography>
										</Box>
										<Stack spacing={1} alignItems={{ xs: 'flex-start', md: 'flex-end' }}>
											<Chip
												label={WORKFLOW_STATUS_LABELS[selectedWorkflow.status] || String(selectedWorkflow.status)}
												color={WORKFLOW_STATUS_COLORS[selectedWorkflow.status] || 'default'}
											/>
											<Button variant="contained" onClick={() => setSubmitDialogOpen(true)}>
												Submit Run
											</Button>
										</Stack>
									</Stack>
									<Typography variant="body2">Description: {String(selectedWorkflow.description || '-')}</Typography>
									<Paper variant="outlined" sx={{ p: 1, overflowX: 'auto' }}>
										<Table size="small">
											<TableHead>
												<TableRow>
													<TableCell>Sequence</TableCell>
													<TableCell>Name</TableCell>
													<TableCell>Disposition</TableCell>
													<TableCell>Module</TableCell>
													<TableCell>Method</TableCell>
													<TableCell>Optional</TableCell>
													<TableCell>Active</TableCell>
												</TableRow>
											</TableHead>
											<TableBody>
												{(selectedWorkflow.actions || []).map((action: SystemWorkflowActionItem1) => (
													<TableRow key={action.guid} hover>
														<TableCell>{action.sequence}</TableCell>
														<TableCell>{action.name}</TableCell>
														<TableCell>
															<Chip
																label={action.disposition_name || '-'}
																color={DISPOSITION_COLORS[action.disposition_name || ''] || 'default'}
																size="small"
															/>
														</TableCell>
														<TableCell sx={{ fontFamily: 'monospace' }}>{action.module_attr || '-'}</TableCell>
														<TableCell sx={{ fontFamily: 'monospace' }}>{action.method_name || '-'}</TableCell>
														<TableCell>{action.is_optional ? 'Yes' : 'No'}</TableCell>
														<TableCell>{action.is_active ? 'Yes' : 'No'}</TableCell>
													</TableRow>
												))}
											</TableBody>
										</Table>
									</Paper>
								</Stack>
							)}
						</Paper>
					</Collapse>
				</Stack>
			)}

			{tab === 1 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2, overflowX: 'auto' }}>
						<Table size="small">
							<TableHead>
								<TableRow>
									<TableCell>Workflow GUID</TableCell>
									<TableCell>Status</TableCell>
									<TableCell>Current Action</TableCell>
									<TableCell>Progress</TableCell>
									<TableCell>Trigger</TableCell>
									<TableCell>Started</TableCell>
									<TableCell>Ended</TableCell>
									<TableCell align="right">Actions</TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{runs.map((run) => (
									<TableRow hover key={run.guid} sx={{ cursor: 'pointer' }} onClick={() => void handleRunRowClick(run)}>
										<TableCell>
											<Tooltip title={run.workflows_guid || '-'}>
												<Typography variant="body2">{getGuidLabel(run.workflows_guid)}</Typography>
											</Tooltip>
										</TableCell>
										<TableCell>
											<Chip label={RUN_STATUS_LABELS[run.status] || String(run.status)} color={RUN_STATUS_COLORS[run.status] || 'default'} />
										</TableCell>
										<TableCell>{String(run.current_action || '-')}</TableCell>
										<TableCell>{getActionProgressLabel(run)}</TableCell>
										<TableCell>
											{TRIGGER_TYPE_LABELS[run.trigger_type ?? -1] || String(run.trigger_type ?? '-')}
											{run.trigger_ref ? ` / ${run.trigger_ref}` : ''}
										</TableCell>
										<TableCell>{String(run.started_on || '-')}</TableCell>
										<TableCell>{String(run.ended_on || '-')}</TableCell>
										<TableCell align="right" onClick={(event) => event.stopPropagation()}>
											<Stack direction="row" spacing={1} justifyContent="flex-end">
												{(run.status === 0 || run.status === 1) && (
													<Button size="small" color="error" onClick={() => void handleCancelRun(run.guid)}>
														Cancel
													</Button>
												)}
												{(run.status === 3 || run.status === 5 || run.status === 6 || run.status === 10) && (
													<Button size="small" color="info" onClick={() => void handleResumeRun(run.guid)}>
														Resume
													</Button>
												)}
												{run.status === 3 && (
													<Button size="small" color="warning" onClick={() => void handleRollbackRun(run.guid)}>
														Rollback
													</Button>
												)}
											</Stack>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</Paper>

					<Collapse in={runDetailOpen && Boolean(selectedRun)}>
						<Paper sx={{ p: 2 }}>
							{selectedRun && (
								<Stack spacing={2}>
									<Typography variant="h6">Run Details</Typography>
									<Typography variant="body2">Run GUID: {selectedRun.guid}</Typography>
									<Typography variant="body2">Workflow GUID: {selectedRun.workflows_guid}</Typography>
									<Typography variant="body2">
										Trigger: {TRIGGER_TYPE_LABELS[selectedRun.trigger_type ?? -1] || String(selectedRun.trigger_type ?? '-')}
										{selectedRun.trigger_ref ? ` / ${selectedRun.trigger_ref}` : ''}
									</Typography>
									<Typography variant="body2">Created: {String(selectedRun.created_on || '-')}</Typography>
									<Typography variant="body2">Started: {String(selectedRun.started_on || '-')}</Typography>
									<Typography variant="body2">Ended: {String(selectedRun.ended_on || '-')}</Typography>

									{selectedRun.error && (
										<Paper sx={{ bgcolor: 'error.light', color: 'error.contrastText', p: 1 }}>
											<Typography variant="subtitle2">Run Error</Typography>
											<pre>{formatJson(selectedRun.error)}</pre>
										</Paper>
									)}

									<Box>
										<Button onClick={() => setShowRunPayload((prev) => !prev)}>
											{showRunPayload ? 'Hide Payload' : 'Show Payload'}
										</Button>
										<Collapse in={showRunPayload}>
											<Box sx={{ maxHeight: 300, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
												<pre>{formatJson(selectedRun.payload)}</pre>
											</Box>
										</Collapse>
									</Box>

									<Box>
										<Button onClick={() => setShowRunContext((prev) => !prev)}>
											{showRunContext ? 'Hide Context' : 'Show Context'}
										</Button>
										<Collapse in={showRunContext}>
											<Box sx={{ maxHeight: 320, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
												<pre>{formatJson(selectedRun.context)}</pre>
											</Box>
										</Collapse>
									</Box>

									<Paper variant="outlined" sx={{ p: 1, overflowX: 'auto' }}>
										<Table size="small">
											<TableHead>
												<TableRow>
													<TableCell>Seq</TableCell>
													<TableCell>Action</TableCell>
													<TableCell>Status</TableCell>
													<TableCell>Retry</TableCell>
													<TableCell>Started</TableCell>
													<TableCell>Ended</TableCell>
													<TableCell>Error</TableCell>
												</TableRow>
											</TableHead>
											<TableBody>
											{runActions.map((action) => {
												const expanded = expandedRunActionGuid === action.guid;
												return (
													<Fragment key={action.guid}>
														<TableRow
															hover
															sx={{ cursor: 'pointer' }}
															onClick={() => setExpandedRunActionGuid(expanded ? null : action.guid)}
														>
																<TableCell>{action.sequence ?? '-'}</TableCell>
																<TableCell>
																	<Tooltip title={action.actions_guid || '-'}>
																		<Typography variant="body2">{getGuidLabel(action.actions_guid)}</Typography>
																	</Tooltip>
																</TableCell>
																<TableCell>
																	<Chip
																		label={ACTION_STATUS_LABELS[action.status] || String(action.status)}
																		color={ACTION_STATUS_COLORS[action.status] || 'default'}
																		size="small"
																	/>
																</TableCell>
																<TableCell>{action.retry_count > 0 ? action.retry_count : '-'}</TableCell>
																<TableCell>{String(action.started_on || '-')}</TableCell>
																<TableCell>{String(action.ended_on || '-')}</TableCell>
																<TableCell>
																	{action.error ? (
																		<Tooltip title={String(action.error)}>
																			<Typography variant="body2" color="error.main">
																				Error
																			</Typography>
																		</Tooltip>
																	) : (
																		'-'
																	)}
																</TableCell>
															</TableRow>
															<TableRow>
																<TableCell colSpan={7} sx={{ py: 0, border: 0 }}>
																	<Collapse in={expanded} timeout="auto" unmountOnExit>
																		<Stack spacing={2} sx={{ py: 1 }}>
																			<Box sx={{ maxHeight: 220, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
																				<Typography variant="subtitle2">Input</Typography>
																				<pre>{formatJson(action.input)}</pre>
																			</Box>
																			<Box sx={{ maxHeight: 220, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
																				<Typography variant="subtitle2">Output</Typography>
																				<pre>{formatJson(action.output)}</pre>
																			</Box>
																			{action.external_ref && (
																				<Typography variant="body2">External Ref: {action.external_ref}</Typography>
																			)}
																			{action.error && (
																				<Paper sx={{ bgcolor: 'error.light', color: 'error.contrastText', p: 1 }}>
																					<Typography variant="subtitle2">Action Error</Typography>
																					<pre>{formatJson(action.error)}</pre>
																				</Paper>
																			)}
																		</Stack>
																	</Collapse>
																</TableCell>
															</TableRow>
													</Fragment>
												);
											})}
											</TableBody>
										</Table>
									</Paper>
								</Stack>
							)}
						</Paper>
					</Collapse>
				</Stack>
			)}

			<Dialog open={submitDialogOpen} onClose={() => setSubmitDialogOpen(false)} maxWidth="md" fullWidth>
				<DialogTitle>Submit Workflow Run</DialogTitle>
				<DialogContent>
					<Stack spacing={2} sx={{ mt: 1 }}>
						<Typography variant="body2">Workflow: {selectedWorkflow?.name || '-'}</Typography>
						<TextField
							label="Payload JSON"
							multiline
							minRows={8}
							value={submitPayloadText}
							onChange={(event) => setSubmitPayloadText(event.target.value)}
							sx={{ '& textarea': { fontFamily: 'monospace' } }}
						/>
						<TextField
							label="Trigger Reference"
							value={submitTriggerRef}
							onChange={(event) => setSubmitTriggerRef(event.target.value)}
							helperText="Optional reference for this trigger (e.g., operator name)"
						/>
					</Stack>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setSubmitDialogOpen(false)}>Cancel</Button>
					<Button variant="contained" onClick={() => void handleSubmitRun()}>
						Submit
					</Button>
				</DialogActions>
			</Dialog>

			<Notification
				open={notificationOpen}
				handleClose={() => setNotificationOpen(false)}
				message={notificationMessage}
				severity={notificationSeverity}
			/>
		</Box>
	);
};

export default SystemWorkflowsPage;