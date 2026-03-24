import { useCallback, useEffect, useState, type JSX, type ReactNode } from 'react';
import {
	Box,
	Button,
	Checkbox,
	Chip,
	Collapse,
	FormControl,
	FormControlLabel,
	InputLabel,
	MenuItem,
	Paper,
	Select,
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

type BatchJob = {
	recid?: number | null;
	name: string;
	description?: string | null;
	class_path: string;
	parameters?: string | null;
	cron: string;
	recurrence_type: number;
	run_count_limit?: number | null;
	run_until?: string | null;
	total_runs: number;
	is_enabled: boolean;
	last_run?: string | null;
	next_run?: string | null;
	status: number;
};

type BatchJobHistory = {
	recid: number;
	jobs_recid: number;
	started_on?: string | null;
	ended_on?: string | null;
	status: number;
	error?: string | null;
	result?: string | null;
};

const RECURRENCE_TYPES = [
	{ value: 0, label: 'Once' },
	{ value: 1, label: 'Recurring' },
	{ value: 2, label: 'Run For' },
	{ value: 3, label: 'Run Until' },
];

const STATUS_LABELS: Record<number, string> = {
	0: 'Idle',
	1: 'Running',
	2: 'Succeeded',
	3: 'Failed',
	4: 'Disabled',
	5: 'Completed',
	6: 'Paused',
};

const STATUS_COLORS: Record<number, 'default' | 'success' | 'error' | 'warning' | 'info'> = {
	0: 'default',
	1: 'warning',
	2: 'success',
	3: 'error',
	4: 'default',
	5: 'success',
	6: 'warning',
};

const HISTORY_STATUS: Record<number, string> = {
	1: 'Running',
	2: 'Succeeded',
	3: 'Failed',
};

interface TabPanelProps {
	children?: ReactNode;
	value: number;
	index: number;
}

const EMPTY_FORM: BatchJob = {
	recid: null,
	name: '',
	description: '',
	class_path: '',
	parameters: '',
	cron: '',
	recurrence_type: 0,
	run_count_limit: null,
	run_until: null,
	total_runs: 0,
	is_enabled: true,
	last_run: null,
	next_run: null,
	status: 0,
};

const TabPanel = ({ children, value, index }: TabPanelProps): JSX.Element => (
	<div role="tabpanel" hidden={value !== index}>
		{value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
	</div>
);

const SystemBatchJobsPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);
	const [jobs, setJobs] = useState<BatchJob[]>([]);
	const [historyRows, setHistoryRows] = useState<BatchJobHistory[]>([]);
	const [selectedJobRecid, setSelectedJobRecid] = useState<number | ''>('');
	const [jobForm, setJobForm] = useState<BatchJob>(EMPTY_FORM);
	const [formOpen, setFormOpen] = useState(false);
	const [notification, setNotification] = useState(false);
	const [notificationMessage, setNotificationMessage] = useState('Saved');

	const handleNotificationClose = (): void => {
		setNotification(false);
	};

	const showSuccess = (message: string): void => {
		setNotificationMessage(message);
		setNotification(true);
	};

	const loadJobs = useCallback(async (): Promise<void> => {
		const res: any = await rpcCall('urn:system:batch_jobs:list:1');
		setJobs(res.jobs || []);
	}, []);

	const loadHistory = useCallback(async (jobsRecid: number): Promise<void> => {
		const res: any = await rpcCall('urn:system:batch_jobs:list_history:1', { jobs_recid: jobsRecid });
		setHistoryRows(res.history || []);
	}, []);

	const loadOnMount = useCallback(async (): Promise<void> => {
		try {
			await loadJobs();
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadJobs]);

	useEffect(() => {
		void loadOnMount();
	}, [loadOnMount]);

	useEffect(() => {
		if (tab !== 1 || !selectedJobRecid) {
			return;
		}
		void loadHistory(selectedJobRecid);
	}, [tab, selectedJobRecid, loadHistory]);

	const resetForm = (): void => {
		setJobForm(EMPTY_FORM);
		setFormOpen(false);
	};

	const withRefresh = async (message: string, action: () => Promise<void>): Promise<void> => {
		await action();
		await loadJobs();
		showSuccess(message);
	};

	const upsertJob = async (payload: Partial<BatchJob>, message: string): Promise<void> => {
		await withRefresh(message, async () => {
			await rpcCall('urn:system:batch_jobs:upsert:1', payload);
		});
	};

	const saveForm = async (): Promise<void> => {
		if (!jobForm.name || !jobForm.class_path || !jobForm.cron) {
			return;
		}
		await upsertJob(
			{
				recid: jobForm.recid,
				name: jobForm.name,
				description: jobForm.description || null,
				class_path: jobForm.class_path,
				parameters: jobForm.parameters || null,
				cron: jobForm.cron,
				recurrence_type: Number(jobForm.recurrence_type),
				run_count_limit:
					jobForm.recurrence_type === 2 && jobForm.run_count_limit !== null
						? Number(jobForm.run_count_limit)
						: null,
				run_until: jobForm.recurrence_type === 3 ? jobForm.run_until || null : null,
				is_enabled: jobForm.is_enabled,
				status: Number(jobForm.status),
			},
			jobForm.recid ? 'Job updated' : 'Job created'
		);
		resetForm();
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
			<PageTitle>Batch Jobs</PageTitle>
			<Tabs value={tab} onChange={(_e, v) => setTab(v)} aria-label="batch jobs tabs">
				<Tab label="Jobs" />
				<Tab label="History" />
			</Tabs>

			<TabPanel value={tab} index={0}>
				<Stack spacing={2}>
					<Paper sx={{ p: 2, overflowX: 'auto' }}>
						<Table size="small">
							<TableHead>
								<TableRow>
									<TableCell>Name</TableCell>
									<TableCell>Class Path</TableCell>
									<TableCell>Cron</TableCell>
									<TableCell>Recurrence</TableCell>
									<TableCell>Status</TableCell>
									<TableCell>Enabled</TableCell>
									<TableCell>Total Runs</TableCell>
									<TableCell>Last Run</TableCell>
									<TableCell>Next Run</TableCell>
									<TableCell>Actions</TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{jobs.map((job) => (
									<TableRow key={job.recid ?? job.name} hover>
										<TableCell>{job.name}</TableCell>
										<TableCell sx={{ fontFamily: 'monospace' }}>{job.class_path}</TableCell>
										<TableCell sx={{ fontFamily: 'monospace' }}>{job.cron}</TableCell>
										<TableCell>
											{RECURRENCE_TYPES.find((r) => r.value === Number(job.recurrence_type))?.label ||
												`Type ${job.recurrence_type}`}
										</TableCell>
										<TableCell>
											<Chip
												label={STATUS_LABELS[job.status] || `Status ${job.status}`}
												color={STATUS_COLORS[job.status] || 'default'}
											/>
										</TableCell>
										<TableCell>
											<Checkbox
												checked={Boolean(job.is_enabled)}
												onChange={(_e, checked) => {
													void upsertJob(
														{
															recid: job.recid,
															name: job.name,
															description: job.description,
															class_path: job.class_path,
															parameters: job.parameters,
															cron: job.cron,
															recurrence_type: Number(job.recurrence_type),
															run_count_limit: job.run_count_limit,
															run_until: job.run_until,
															is_enabled: checked,
															status: Number(job.status),
														},
														checked ? 'Job enabled' : 'Job disabled'
													);
												}}
											/>
										</TableCell>
										<TableCell>{job.total_runs}</TableCell>
										<TableCell>{job.last_run || '-'}</TableCell>
										<TableCell>{job.next_run || '-'}</TableCell>
										<TableCell>
											<Stack direction="row" spacing={1} flexWrap="wrap">
												<Button
													size="small"
													variant="outlined"
													disabled={Number(job.status) === 1}
													onClick={() => {
														void withRefresh('Job queued to run', async () => {
															await rpcCall('urn:system:batch_jobs:run_now:1', { recid: job.recid });
														});
													}}
												>
													Run Now
												</Button>
												<Button
													size="small"
													variant="outlined"
													onClick={() => {
														const paused = Number(job.status) === 6;
														void upsertJob(
															{
																recid: job.recid,
																name: job.name,
																description: job.description,
																class_path: job.class_path,
																parameters: job.parameters,
																cron: job.cron,
																recurrence_type: Number(job.recurrence_type),
																run_count_limit: job.run_count_limit,
																run_until: job.run_until,
																is_enabled: job.is_enabled,
																status: paused ? 0 : 6,
															},
															paused ? 'Job resumed' : 'Job paused'
														);
													}}
												>
													{Number(job.status) === 6 ? 'Resume' : 'Pause'}
												</Button>
												<Button
													size="small"
													variant="outlined"
													onClick={() => {
														setJobForm({ ...job });
														setFormOpen(true);
													}}
												>
													Edit
												</Button>
												<Button
													size="small"
													variant="outlined"
													onClick={() => {
														if (job.recid) {
															setSelectedJobRecid(job.recid);
															setTab(1);
														}
													}}
												>
													History
												</Button>
												<Button
													size="small"
													variant="outlined"
													color="error"
													onClick={() => {
														if (!job.recid) {
															return;
														}
														void withRefresh('Job deleted', async () => {
															await rpcCall('urn:system:batch_jobs:delete:1', { recid: job.recid });
														});
													}}
												>
													Delete
												</Button>
											</Stack>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</Paper>

					<Box>
						<Button variant="contained" onClick={() => setFormOpen((prev) => !prev)}>
							{formOpen ? 'Hide Form' : 'Create Job'}
						</Button>
					</Box>

					<Collapse in={formOpen}>
						<Paper sx={{ p: 2 }}>
							<Stack spacing={2}>
								<TextField
									label="Name"
									required
									value={jobForm.name}
									onChange={(e) => setJobForm((prev) => ({ ...prev, name: e.target.value }))}
								/>
								<TextField
									label="Description"
									value={jobForm.description || ''}
									onChange={(e) =>
										setJobForm((prev) => ({ ...prev, description: e.target.value }))
									}
								/>
								<TextField
									label="Class Path"
									required
									value={jobForm.class_path}
									onChange={(e) => setJobForm((prev) => ({ ...prev, class_path: e.target.value }))}
									sx={{ '& input': { fontFamily: 'monospace' } }}
								/>
								<TextField
									label="Parameters"
									multiline
									minRows={3}
									value={jobForm.parameters || ''}
									onChange={(e) => setJobForm((prev) => ({ ...prev, parameters: e.target.value }))}
									sx={{ '& textarea': { fontFamily: 'monospace' } }}
								/>
								<TextField
									label="Cron Expression"
									required
									value={jobForm.cron}
									onChange={(e) => setJobForm((prev) => ({ ...prev, cron: e.target.value }))}
									sx={{ '& input': { fontFamily: 'monospace' } }}
								/>
								<FormControl fullWidth>
									<InputLabel id="recurrence-type-label">Recurrence Type</InputLabel>
									<Select
										labelId="recurrence-type-label"
										label="Recurrence Type"
										value={jobForm.recurrence_type}
										onChange={(e) =>
											setJobForm((prev) => ({ ...prev, recurrence_type: Number(e.target.value) }))
										}
									>
										{RECURRENCE_TYPES.map((item) => (
											<MenuItem key={item.value} value={item.value}>
												{item.label}
											</MenuItem>
										))}
									</Select>
								</FormControl>
								{jobForm.recurrence_type === 2 && (
									<TextField
										type="number"
										label="Run Count Limit"
										value={jobForm.run_count_limit ?? ''}
										onChange={(e) =>
											setJobForm((prev) => ({
												...prev,
												run_count_limit: e.target.value ? Number(e.target.value) : null,
											}))
										}
									/>
								)}
								{jobForm.recurrence_type === 3 && (
									<TextField
										type="datetime-local"
										label="Run Until"
										InputLabelProps={{ shrink: true }}
										value={jobForm.run_until || ''}
										onChange={(e) =>
											setJobForm((prev) => ({ ...prev, run_until: e.target.value || null }))
										}
									/>
								)}
								<FormControlLabel
									control={
										<Checkbox
											checked={Boolean(jobForm.is_enabled)}
											onChange={(_e, checked) =>
												setJobForm((prev) => ({ ...prev, is_enabled: checked }))
											}
										/>
									}
									label="Enabled"
								/>
								<Stack direction="row" spacing={1}>
									<Button variant="contained" onClick={() => { void saveForm(); }}>
										Save
									</Button>
									<Button variant="outlined" onClick={resetForm}>
										Cancel
									</Button>
								</Stack>
							</Stack>
						</Paper>
					</Collapse>
				</Stack>
			</TabPanel>

			<TabPanel value={tab} index={1}>
				<Stack spacing={2}>
					<FormControl sx={{ maxWidth: 420 }}>
						<InputLabel id="history-job-select-label">Select Job</InputLabel>
						<Select
							labelId="history-job-select-label"
							label="Select Job"
							value={selectedJobRecid}
							onChange={(e) => setSelectedJobRecid(Number(e.target.value))}
						>
							{jobs.map((job) => (
								<MenuItem key={job.recid ?? job.name} value={job.recid ?? ''}>
									{job.name}
								</MenuItem>
							))}
						</Select>
					</FormControl>

					<Paper sx={{ p: 2, overflowX: 'auto' }}>
						<Table size="small">
							<TableHead>
								<TableRow>
									<TableCell>Run #</TableCell>
									<TableCell>Started</TableCell>
									<TableCell>Ended</TableCell>
									<TableCell>Status</TableCell>
									<TableCell>Error</TableCell>
									<TableCell>Result</TableCell>
								</TableRow>
							</TableHead>
							<TableBody>
								{historyRows.map((row) => (
									<TableRow key={row.recid}>
										<TableCell>{row.recid}</TableCell>
										<TableCell>{row.started_on || '-'}</TableCell>
										<TableCell>{row.ended_on || '-'}</TableCell>
										<TableCell>
											<Chip
												label={HISTORY_STATUS[row.status] || `Status ${row.status}`}
												color={STATUS_COLORS[row.status] || 'default'}
											/>
										</TableCell>
										<TableCell>
											<Tooltip title={row.error || ''}>
												<Box
													sx={{
														maxWidth: 200,
														overflow: 'hidden',
														textOverflow: 'ellipsis',
														whiteSpace: 'nowrap',
													}}
												>
													{row.error || '-'}
												</Box>
											</Tooltip>
										</TableCell>
										<TableCell>
											<Tooltip title={row.result || ''}>
												<Box
													sx={{
														maxWidth: 200,
														overflow: 'hidden',
														textOverflow: 'ellipsis',
														whiteSpace: 'nowrap',
													}}
												>
													{row.result || '-'}
												</Box>
											</Tooltip>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
					</Paper>
				</Stack>
			</TabPanel>

			<Notification
				open={notification}
				handleClose={handleNotificationClose}
				severity="success"
				message={notificationMessage}
			/>
		</Box>
	);
};

export default SystemBatchJobsPage;
