import { useCallback, useEffect, useMemo, useState, type JSX } from 'react';
import {
	Box,
	Button,
	Chip,
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
import {
	rpcCall,
	SystemTaskEventItem1,
	SystemTaskEventsList1,
	SystemTaskItem1,
	SystemTaskList1,
} from '../../shared/RpcModels';

const STATUS_LABELS: Record<number, string> = {
	0: 'Queued',
	1: 'Running',
	2: 'Polling',
	3: 'Waiting',
	4: 'Completed',
	5: 'Failed',
	6: 'Cancelled',
	7: 'Timed Out',
};

const STATUS_COLORS: Record<number, 'default' | 'warning' | 'info' | 'success' | 'error'> = {
	0: 'default',
	1: 'warning',
	2: 'info',
	3: 'info',
	4: 'success',
	5: 'error',
	6: 'default',
	7: 'error',
};

const ACTIVE_STATUSES = new Set([0, 1, 2, 3]);

const formatJson = (value: unknown): string => JSON.stringify(value, null, 2);

const SystemAsyncTasksPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);
	const [tasks, setTasks] = useState<SystemTaskItem1[]>([]);
	const [events, setEvents] = useState<SystemTaskEventItem1[]>([]);
	const [selectedTask, setSelectedTask] = useState<SystemTaskItem1 | null>(null);
	const [selectedTaskGuid, setSelectedTaskGuid] = useState('');
	const [notification, setNotification] = useState(false);
	const [notificationMessage, setNotificationMessage] = useState('Done');
	const [notificationSeverity, setNotificationSeverity] = useState<'success' | 'error'>('success');

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

	const showNotification = (message: string, severity: 'success' | 'error' = 'success'): void => {
		setNotificationMessage(message);
		setNotificationSeverity(severity);
		setNotification(true);
	};

	const loadOnMount = useCallback(async (): Promise<void> => {
		try {
			await loadTasks();
			setForbidden(false);
		} catch (error: any) {
			if (error?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw error;
		}
	}, [loadTasks]);

	useEffect(() => {
		void loadOnMount();
	}, [loadOnMount]);

	useEffect(() => {
		if (tab !== 1 || !selectedTaskGuid) {
			return;
		}
		void loadEvents(selectedTaskGuid);
	}, [tab, selectedTaskGuid, loadEvents]);

	const hasActiveTasks = useMemo(() => tasks.some((task) => ACTIVE_STATUSES.has(task.status)), [tasks]);

	useEffect(() => {
		if (!hasActiveTasks) {
			return;
		}
		const intervalId = window.setInterval(() => {
			void loadTasks();
		}, 10000);
		return () => {
			window.clearInterval(intervalId);
		};
	}, [hasActiveTasks, loadTasks]);

	const runAction = async (guid: string, action: 'cancel' | 'retry'): Promise<void> => {
		const isCancel = action === 'cancel';
		const confirmed = window.confirm(isCancel ? 'Cancel this task?' : 'Retry this task?');
		if (!confirmed) {
			return;
		}
		await rpcCall(isCancel ? 'urn:system:tasks:cancel:1' : 'urn:system:tasks:retry:1', { guid });
		showNotification(isCancel ? 'Task cancelled' : 'Task retried');
		await loadTasks();
		if (tab === 1 && selectedTaskGuid) {
			await loadEvents(selectedTaskGuid);
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
			<PageTitle>Async Tasks</PageTitle>
			<Tabs value={tab} onChange={(_event, value) => setTab(value)}>
				<Tab label="Tasks" />
				<Tab label="Events" />
			</Tabs>

			{tab === 0 && (
				<Paper sx={{ p: 2, mt: 2, overflowX: 'auto' }}>
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
										<Chip size="small" label={task.handler_type || '-'} />
									</TableCell>
									<TableCell>
										<Chip size="small" label={STATUS_LABELS[task.status] || String(task.status)} color={STATUS_COLORS[task.status] || 'default'} />
									</TableCell>
									<TableCell>{task.handler_type === 'pipeline' ? (task.current_step || '') : ''}</TableCell>
									<TableCell>{String(task.source_type || '')}</TableCell>
									<TableCell>{String(task.created_on || '')}</TableCell>
									<TableCell>{String(task.modified_on || '')}</TableCell>
									<TableCell align="right" onClick={(event) => event.stopPropagation()}>
										<Stack direction="row" spacing={1} justifyContent="flex-end">
											<Button size="small" onClick={() => setSelectedTask(task)}>Details</Button>
											{ACTIVE_STATUSES.has(task.status) && (
												<Button size="small" color="warning" onClick={() => void runAction(task.guid, 'cancel')}>Cancel</Button>
											)}
											{task.status === 5 && (
												<Button size="small" color="error" onClick={() => void runAction(task.guid, 'retry')}>Retry</Button>
											)}
										</Stack>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Paper>
			)}

			{tab === 1 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
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

			<Dialog open={Boolean(selectedTask)} onClose={() => setSelectedTask(null)} maxWidth="md" fullWidth>
				<DialogTitle>Task Details</DialogTitle>
				<DialogContent>
					{selectedTask && (
						<Stack spacing={2} sx={{ mt: 1 }}>
							<Typography variant="body2">External ID: {String(selectedTask.external_id || '-')}</Typography>
							<Typography variant="body2">Retries: {selectedTask.retry_count} / {selectedTask.max_retries}</Typography>
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
				open={notification}
				handleClose={() => setNotification(false)}
				message={notificationMessage}
				severity={notificationSeverity}
			/>
		</Box>
	);
};

export default SystemAsyncTasksPage;
