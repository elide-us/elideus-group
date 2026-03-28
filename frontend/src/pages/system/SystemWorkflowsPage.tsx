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
	MenuItem,
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
	SystemTaskEventItem1,
	SystemTaskEventsList1,
	SystemTaskItem1,
	SystemTaskList1,
	SystemWorkflowDetail1,
	SystemWorkflowItem1,
	SystemWorkflowList1,
	SystemWorkflowRunItem1,
	SystemWorkflowRunList1,
	SystemWorkflowRunStepItem1,
	SystemWorkflowRunStepList1,
	SystemWorkflowStepItem1,
} from '../../shared/RpcModels';

const WORKFLOW_STATUS_LABELS: Record<number, string> = {
	0: 'Inactive',
	1: 'Active',
	2: 'Deprecated',
};

const WORKFLOW_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning'> = {
	0: 'default',
	1: 'success',
	2: 'warning',
};

const RUN_STATUS_LABELS: Record<number, string> = {
	0: 'Queued',
	1: 'Running',
	4: 'Completed',
	5: 'Failed',
	6: 'Cancelled',
	7: 'Rolling Back',
	8: 'Rolled Back',
};

const RUN_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
	0: 'info',
	1: 'warning',
	4: 'success',
	5: 'error',
	6: 'error',
	7: 'warning',
	8: 'error',
};

const RUN_STEP_STATUS_LABELS: Record<number, string> = {
	0: 'Pending',
	1: 'Running',
	4: 'Completed',
	5: 'Failed',
	6: 'Skipped',
	7: 'Rolled Back',
};

const RUN_STEP_STATUS_COLORS: Record<number, 'default' | 'success' | 'warning' | 'error'> = {
	0: 'default',
	1: 'warning',
	4: 'success',
	5: 'error',
	6: 'default',
	7: 'warning',
};

const DISPOSITION_COLORS: Record<string, 'default' | 'info' | 'warning'> = {
	harmless: 'default',
	reversible: 'info',
	irreversible: 'warning',
};

const STEP_TYPE_COLORS: Record<string, 'default' | 'info'> = {
	pipe: 'default',
	stack: 'info',
};

const TASK_STATUS_LABELS: Record<number, string> = {
	0: 'Queued',
	1: 'Running',
	2: 'Polling',
	3: 'Waiting',
	4: 'Completed',
	5: 'Failed',
	6: 'Cancelled',
	7: 'Timed Out',
};

const TASK_STATUS_COLORS: Record<number, 'default' | 'warning' | 'info' | 'success' | 'error'> = {
	0: 'info',
	1: 'warning',
	2: 'info',
	3: 'info',
	4: 'success',
	5: 'error',
	6: 'error',
	7: 'error',
};

const ACTIVE_TASK_STATUSES = new Set([0, 1, 2, 3]);
const ACTIVE_RUN_STATUSES = new Set([0, 1, 7]);

const formatJson = (value: unknown): string => JSON.stringify(value, null, 2);

const getGuidLabel = (guid: unknown): string => {
	const value = String(guid || '');
	return value ? value.slice(0, 8) : '-';
};

const getStepProgressLabel = (run: SystemWorkflowRunItem1): string => {
	const stepIndex = Number(run.step_index || 0);
	const context = run.context as Record<string, any> | null;
	const contextTotal = Number(context?.step_count || context?.total_steps || 0);
	if (contextTotal > 0) {
		return `${stepIndex}/${contextTotal}`;
	}
	return String(stepIndex);
};

const SystemWorkflowsPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [legacyTab, setLegacyTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [workflows, setWorkflows] = useState<SystemWorkflowItem1[]>([]);
	const [selectedWorkflow, setSelectedWorkflow] = useState<SystemWorkflowDetail1 | null>(null);
	const [workflowDetailOpen, setWorkflowDetailOpen] = useState(false);

	const [runs, setRuns] = useState<SystemWorkflowRunItem1[]>([]);
	const [selectedRun, setSelectedRun] = useState<SystemWorkflowRunItem1 | null>(null);
	const [runSteps, setRunSteps] = useState<SystemWorkflowRunStepItem1[]>([]);
	const [runDetailOpen, setRunDetailOpen] = useState(false);
	const [expandedRunStepGuid, setExpandedRunStepGuid] = useState<string | null>(null);
	const [showRunPayload, setShowRunPayload] = useState(false);
	const [showRunContext, setShowRunContext] = useState(false);

	const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
	const [submitPayloadText, setSubmitPayloadText] = useState('{}');
	const [submitSourceType, setSubmitSourceType] = useState('rpc');
	const [submitSourceId, setSubmitSourceId] = useState('');

	const [tasks, setTasks] = useState<SystemTaskItem1[]>([]);
	const [events, setEvents] = useState<SystemTaskEventItem1[]>([]);
	const [selectedTask, setSelectedTask] = useState<SystemTaskItem1 | null>(null);
	const [selectedTaskGuid, setSelectedTaskGuid] = useState('');

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

	const loadRunSteps = useCallback(async (runGuid: string): Promise<void> => {
		const response = await rpcCall<SystemWorkflowRunStepList1>('urn:system:workflows:list_run_steps:1', { run_guid: runGuid });
		setRunSteps(response.steps || []);
	}, []);

	const loadTasks = useCallback(async (): Promise<void> => {
		const response = await rpcCall<SystemTaskList1>('urn:system:tasks:list:1');
		const nextTasks = response.tasks || [];
		setTasks(nextTasks);
		if (!selectedTaskGuid && nextTasks.length > 0) {
			setSelectedTaskGuid(nextTasks[0].guid);
		}
	}, [selectedTaskGuid]);

	const loadEvents = useCallback(async (guid: string): Promise<void> => {
		if (!guid) {
			setEvents([]);
			return;
		}
		const response = await rpcCall<SystemTaskEventsList1>('urn:system:tasks:events:1', { guid });
		setEvents(response.events || []);
	}, []);

	const loadOnMount = useCallback(async (): Promise<void> => {
		try {
			await Promise.all([loadWorkflows(), loadTasks()]);
			setForbidden(false);
		} catch (error: any) {
			if (error?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw error;
		}
	}, [loadTasks, loadWorkflows]);

	useEffect(() => {
		void loadOnMount();
	}, [loadOnMount]);

	useEffect(() => {
		if (tab !== 1) {
			return;
		}
		void loadRuns();
	}, [tab, loadRuns]);

	useEffect(() => {
		if (tab !== 2 || legacyTab !== 1 || !selectedTaskGuid) {
			return;
		}
		void loadEvents(selectedTaskGuid);
	}, [tab, legacyTab, selectedTaskGuid, loadEvents]);

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

	const hasActiveTasks = useMemo(() => tasks.some((task) => ACTIVE_TASK_STATUSES.has(task.status)), [tasks]);

	useEffect(() => {
		if (tab !== 2 || !hasActiveTasks) {
			return;
		}
		const intervalId = window.setInterval(() => {
			void loadTasks();
		}, 10000);
		return () => {
			window.clearInterval(intervalId);
		};
	}, [tab, hasActiveTasks, loadTasks]);

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
		setExpandedRunStepGuid(null);
		await loadRunSteps(run.guid);
		setRunDetailOpen(true);
	};

	const runAction = async (guid: string, action: 'cancel' | 'retry'): Promise<void> => {
		const isCancel = action === 'cancel';
		const confirmed = window.confirm(isCancel ? 'Cancel this task?' : 'Retry this task?');
		if (!confirmed) {
			return;
		}
		await rpcCall(isCancel ? 'urn:system:tasks:cancel:1' : 'urn:system:tasks:retry:1', { guid });
		showNotification(isCancel ? 'Task cancelled' : 'Task retried');
		await loadTasks();
		if (legacyTab === 1 && selectedTaskGuid) {
			await loadEvents(selectedTaskGuid);
		}
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
			source_type: submitSourceType || null,
			source_id: submitSourceId || null,
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
			await loadRunSteps(runGuid);
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
			await loadRunSteps(runGuid);
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
				<Tab label="Legacy Tasks" />
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
									<TableCell>Step Count</TableCell>
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
											<TableCell>{String(workflow.step_count || '-')}</TableCell>
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
													<TableCell>Type</TableCell>
													<TableCell>Disposition</TableCell>
													<TableCell>Class Path</TableCell>
													<TableCell>Optional</TableCell>
													<TableCell>Timeout</TableCell>
												</TableRow>
											</TableHead>
											<TableBody>
												{(selectedWorkflow.steps || []).map((step: SystemWorkflowStepItem1) => (
													<TableRow key={step.guid} hover>
														<TableCell>{step.sequence}</TableCell>
														<TableCell>{step.name}</TableCell>
														<TableCell>
															<Chip label={step.step_type || '-'} color={STEP_TYPE_COLORS[step.step_type] || 'default'} size="small" />
														</TableCell>
														<TableCell>
															<Chip
																label={step.disposition || '-'}
																color={DISPOSITION_COLORS[step.disposition] || 'default'}
																size="small"
															/>
														</TableCell>
														<TableCell sx={{ fontFamily: 'monospace' }}>{step.class_path}</TableCell>
														<TableCell>{step.is_optional ? 'Yes' : 'No'}</TableCell>
														<TableCell>{String(step.timeout_seconds || '-')}</TableCell>
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
									<TableCell>Current Step</TableCell>
									<TableCell>Step Progress</TableCell>
									<TableCell>Source</TableCell>
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
										<TableCell>{String(run.current_step || '-')}</TableCell>
										<TableCell>{getStepProgressLabel(run)}</TableCell>
										<TableCell>
											{String(run.source_type || '-')} / {String(run.source_id || '-')}
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
												{run.status === 5 && (
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
										Source: {String(selectedRun.source_type || '-')} / {String(selectedRun.source_id || '-')}
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
													<TableCell>Step</TableCell>
													<TableCell>Disposition</TableCell>
													<TableCell>Status</TableCell>
													<TableCell>Started</TableCell>
													<TableCell>Ended</TableCell>
													<TableCell>Error</TableCell>
												</TableRow>
											</TableHead>
											<TableBody>
											{runSteps.map((step) => {
												const expanded = expandedRunStepGuid === step.guid;
												return (
													<Fragment key={step.guid}>
														<TableRow
															hover
															sx={{ cursor: 'pointer' }}
															onClick={() => setExpandedRunStepGuid(expanded ? null : step.guid)}
														>
																<TableCell>
																	<Tooltip title={step.steps_guid || '-'}>
																		<Typography variant="body2">{getGuidLabel(step.steps_guid)}</Typography>
																	</Tooltip>
																</TableCell>
																<TableCell>
																	<Chip
																		label={step.disposition || '-'}
																		color={DISPOSITION_COLORS[step.disposition] || 'default'}
																		size="small"
																	/>
																</TableCell>
																<TableCell>
																	<Chip
																		label={RUN_STEP_STATUS_LABELS[step.status] || String(step.status)}
																		color={RUN_STEP_STATUS_COLORS[step.status] || 'default'}
																		size="small"
																	/>
																</TableCell>
																<TableCell>{String(step.started_on || '-')}</TableCell>
																<TableCell>{String(step.ended_on || '-')}</TableCell>
																<TableCell>
																	{step.error ? (
																		<Tooltip title={String(step.error)}>
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
																<TableCell colSpan={6} sx={{ py: 0, border: 0 }}>
																	<Collapse in={expanded} timeout="auto" unmountOnExit>
																		<Stack spacing={2} sx={{ py: 1 }}>
																			<Box sx={{ maxHeight: 220, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
																				<Typography variant="subtitle2">Input</Typography>
																				<pre>{formatJson(step.input)}</pre>
																			</Box>
																			<Box sx={{ maxHeight: 220, overflow: 'auto', p: 1, bgcolor: 'background.default' }}>
																				<Typography variant="subtitle2">Output</Typography>
																				<pre>{formatJson(step.output)}</pre>
																			</Box>
																			{step.error && (
																				<Paper sx={{ bgcolor: 'error.light', color: 'error.contrastText', p: 1 }}>
																					<Typography variant="subtitle2">Step Error</Typography>
																					<pre>{formatJson(step.error)}</pre>
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

			{tab === 2 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Tabs value={legacyTab} onChange={(_event, value) => setLegacyTab(value)}>
						<Tab label="Tasks" />
						<Tab label="Events" />
					</Tabs>

					{legacyTab === 0 && (
						<Paper sx={{ p: 2, overflowX: 'auto' }}>
							<Table size="small">
								<TableHead>
									<TableRow>
										<TableCell>Handler Name</TableCell>
										<TableCell>Handler Type</TableCell>
										<TableCell>Status</TableCell>
										<TableCell>Current Step</TableCell>
										<TableCell>Source Type</TableCell>
										<TableCell>Created</TableCell>
										<TableCell>Modified</TableCell>
										<TableCell align="right">Actions</TableCell>
									</TableRow>
								</TableHead>
								<TableBody>
									{tasks.map((task) => (
										<TableRow
											hover
											key={task.guid}
											sx={{ cursor: 'pointer' }}
											onClick={() => setSelectedTask(task)}
										>
											<TableCell>{task.handler_name}</TableCell>
											<TableCell>
												<Chip label={task.handler_type || '-'} />
											</TableCell>
											<TableCell>
												<Chip label={TASK_STATUS_LABELS[task.status] || String(task.status)} color={TASK_STATUS_COLORS[task.status] || 'default'} />
											</TableCell>
											<TableCell>{task.handler_type === 'pipeline' ? (task.current_step || '') : ''}</TableCell>
											<TableCell>{String(task.source_type || '')}</TableCell>
											<TableCell>{String(task.created_on || '')}</TableCell>
											<TableCell>{String(task.modified_on || '')}</TableCell>
											<TableCell align="right" onClick={(event) => event.stopPropagation()}>
												<Stack direction="row" spacing={1} justifyContent="flex-end">
													<Button size="small" onClick={() => setSelectedTask(task)}>
														Details
													</Button>
													{ACTIVE_TASK_STATUSES.has(task.status) && (
														<Button size="small" color="error" onClick={() => void runAction(task.guid, 'cancel')}>
															Cancel
														</Button>
													)}
													{task.status === 5 && (
														<Button size="small" color="error" onClick={() => void runAction(task.guid, 'retry')}>
															Retry
														</Button>
													)}
												</Stack>
											</TableCell>
										</TableRow>
									))}
								</TableBody>
							</Table>
						</Paper>
					)}

					{legacyTab === 1 && (
						<Stack spacing={2}>
							<TextField
								select
								label="Task"
								value={selectedTaskGuid}
								onChange={(event) => setSelectedTaskGuid(event.target.value)}
								sx={{ maxWidth: 520 }}
							>
								{tasks.map((task) => (
									<MenuItem key={task.guid} value={task.guid}>
										{task.handler_name} ({task.guid.slice(0, 8)})
									</MenuItem>
								))}
							</TextField>
							<Paper sx={{ p: 2, overflowX: 'auto' }}>
								<Table size="small">
									<TableHead>
										<TableRow>
											<TableCell>Event Type</TableCell>
											<TableCell>Step Name</TableCell>
											<TableCell>Detail</TableCell>
											<TableCell>Timestamp</TableCell>
										</TableRow>
									</TableHead>
									<TableBody>
										{events.map((event) => {
											const detail = String(event.element_detail || '');
											const truncated = detail.length > 80 ? `${detail.slice(0, 80)}...` : detail;
											return (
												<TableRow key={event.recid}>
													<TableCell>{event.element_event_type}</TableCell>
													<TableCell>{event.element_step_name || '-'}</TableCell>
													<TableCell>
														<Tooltip title={detail || '-'}>
															<Typography variant="body2">{truncated || '-'}</Typography>
														</Tooltip>
													</TableCell>
													<TableCell>{event.element_created_on}</TableCell>
												</TableRow>
											);
										})}
									</TableBody>
								</Table>
							</Paper>
						</Stack>
					)}
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
							label="Source Type"
							value={submitSourceType}
							onChange={(event) => setSubmitSourceType(event.target.value)}
						/>
						<TextField
							label="Source ID"
							value={submitSourceId}
							onChange={(event) => setSubmitSourceId(event.target.value)}
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

			<Dialog open={Boolean(selectedTask)} onClose={() => setSelectedTask(null)} maxWidth="md" fullWidth>
				<DialogTitle>Task Details</DialogTitle>
				<DialogContent>
					{selectedTask && (
						<Stack spacing={2} sx={{ mt: 1 }}>
							<Typography variant="body2">External ID: {String(selectedTask.external_id || '-')}</Typography>
							<Typography variant="body2">
								Retries: {selectedTask.retry_count} / {selectedTask.max_retries}
							</Typography>
							<Typography variant="body2">Timeout Seconds: {String(selectedTask.timeout_seconds || '-')}</Typography>
							<Typography variant="body2">Timeout At: {String(selectedTask.timeout_at || '-')}</Typography>
							<Typography variant="body2">Current Step: {String(selectedTask.current_step || '-')}</Typography>
							<Typography variant="body2">Step Index: {selectedTask.step_index}</Typography>
							<Box>
								<Typography variant="subtitle2">Payload</Typography>
								<pre>{formatJson(selectedTask.payload)}</pre>
							</Box>
							{selectedTask.result !== null && selectedTask.result !== undefined && (
								<Box>
									<Typography variant="subtitle2">Result</Typography>
									<pre>{formatJson(selectedTask.result)}</pre>
								</Box>
							)}
							{selectedTask.error && (
								<Box>
									<Typography variant="subtitle2">Error</Typography>
									<pre>{formatJson(selectedTask.error)}</pre>
								</Box>
							)}
						</Stack>
					)}
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setSelectedTask(null)}>Close</Button>
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
