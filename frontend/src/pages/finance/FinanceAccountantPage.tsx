import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Alert,
	Box,
	Button,
	Checkbox,
	Chip,
	Collapse,
	CircularProgress,
	Dialog,
	DialogActions,
	DialogContent,
	DialogContentText,
	DialogTitle,
	Divider,
	FormControlLabel,
	LinearProgress,
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
	Typography,
} from "@mui/material";
import Notification from "../../components/Notification";
import PageTitle from "../../components/PageTitle";
import { fetchCreate, fetchLines, fetchPost, fetchReverse } from "../../rpc/finance/journals/index";
import { fetchCreate as fetchCreditCreate, fetchExpire, fetchListEvents } from "../../rpc/finance/credit_lots/index";
import { fetchCreditLotSummary, fetchJournalSummary, fetchPeriodStatus } from "../../rpc/finance/reporting/index";
import {
	rpcCall,
	CreditLotCreate1,
	CreditLotEventItem1,
	CreditLotEventList1,
	CreditLotSummaryList1,
	FinanceAccountsItem1,
	FinanceAccountsList1,
	FinancePeriodsItem1,
	FinancePeriodsList1,
	JournalCreate1,
	JournalCreateLine1,
	JournalLineItem1,
	JournalLineList1,
	JournalSummaryList1,
	PeriodStatusList1,
	FinanceStagingAccountMapItem1,
	FinanceStagingAccountMapList1,
	StagingImportItem1,
	StagingImportList1,
	StagingPromoteResult1,
} from "../../shared/RpcModels";

type JournalSummaryRow = {
	recid: number;
	posting_key: string;
	name: string;
	source_type: string;
	period_name: string;
	journal_status: number;
	line_count: number;
	total_debit: string;
	total_credit: string;
	posted_by: string | null;
	created_on: string;
};

type CreditLotSummaryRow = {
	recid: number;
	lot_number: string;
	users_guid: string;
	source_type: string;
	credits_original: number;
	credits_remaining: number;
	unit_price: string;
	total_paid: string;
	expired: boolean;
	event_count: number;
	total_consumed: number;
	created_on: string;
};

type PeriodStatusRow = {
	guid: string;
	period_name: string;
	start_date: string;
	end_date: string;
	close_type: number;
	total_journals: number;
	unposted_count: number;
	posted_count: number;
	reversed_count: number;
	year?: number;
};

type JournalLineForm = JournalCreateLine1;

type VendorItem = {
	recid: number;
	element_name: string;
};

type StagingLineItem = {
	recid: number;
	imports_recid: number;
	vendors_recid: number;
	vendor_name?: string | null;
	element_date?: string | null;
	element_service?: string | null;
	element_category?: string | null;
	element_description?: string | null;
	element_quantity?: string | null;
	element_amount?: string | null;
	element_currency?: string | null;
};

type FinanceLedger = {
	recid: number;
	element_name: string;
};

type StagingImportRow = StagingImportItem1 & {
	element_requested_by: string | null;
	element_approved_by: string | null;
	element_approved_on: string | null;
};

type AsyncTask = {
	guid: string;
	status: number;
	handler_name: string | null;
	current_step: string | null;
	step_index: number | null;
	step_count: number | null;
	result: Record<string, any> | null;
	error: string | null;
};

type AsyncTaskEvent = Record<string, any>;

interface MappingFormState {
	recid: number | null;
	vendors_recid: number | null;
	element_service_pattern: string;
	element_meter_pattern: string;
	accounts_guid: string;
	element_priority: number;
	element_description: string;
	element_status: boolean;
}

const EMPTY_MAPPING_FORM: MappingFormState = {
	recid: null,
	vendors_recid: null,
	element_service_pattern: "",
	element_meter_pattern: "",
	accounts_guid: "",
	element_priority: 0,
	element_description: "",
	element_status: true,
};

const PROMOTE_PIPELINE_STEPS = ["validate_import", "classify_costs", "create_journal", "mark_promoted"] as const;

const IMPORT_STATUS_CONFIG: Record<number, { label: string; color: "default" | "success" | "error" | "info" | "warning" }> = {
	0: { label: "Pending", color: "warning" },
	1: { label: "Approved", color: "success" },
	2: { label: "Failed", color: "error" },
	3: { label: "Promoted", color: "info" },
	4: { label: "Pending Approval", color: "warning" },
	5: { label: "Rejected", color: "error" },
};

const getPeriodDisplayLabel = (period: FinancePeriodsItem1): string => {
	const periodYear = (period as any).year ?? (period as any).fiscal_year ?? (period as any).element_year;
	return `FY${periodYear ?? "-"} - ${period.period_name}`;
};

const DEFAULT_JOURNAL_LINE = (lineNumber: number): JournalLineForm => ({
	line_number: lineNumber,
	accounts_guid: "",
	debit: "0",
	credit: "0",
	description: "",
	dimension_recids: [],
});

const FinanceAccountantPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [periods, setPeriods] = useState<FinancePeriodsItem1[]>([]);
	const [accounts, setAccounts] = useState<FinanceAccountsItem1[]>([]);
	const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
	const [selectedPeriodGuid, setSelectedPeriodGuid] = useState<string>("");
	const [journalStatus, setJournalStatus] = useState<string>("");

	const [journals, setJournals] = useState<JournalSummaryRow[]>([]);
	const [journalLines, setJournalLines] = useState<JournalLineItem1[]>([]);
	const [selectedJournal, setSelectedJournal] = useState<JournalSummaryRow | null>(null);
	const [journalDialogOpen, setJournalDialogOpen] = useState(false);
	const [createJournalOpen, setCreateJournalOpen] = useState(false);
	const [journalForm, setJournalForm] = useState<JournalCreate1>({
		name: "",
		description: "",
		posting_key: null,
		source_type: "manual",
		source_id: null,
		periods_guid: null,
		ledgers_recid: null,
		lines: [DEFAULT_JOURNAL_LINE(1)],
		post: false,
	});

	const [lots, setLots] = useState<CreditLotSummaryRow[]>([]);
	const [lotUserGuid, setLotUserGuid] = useState("");
	const [lotEvents, setLotEvents] = useState<CreditLotEventItem1[]>([]);
	const [selectedLotRecid, setSelectedLotRecid] = useState<number | null>(null);
	const [lotEventDialogOpen, setLotEventDialogOpen] = useState(false);
	const [grantDialogOpen, setGrantDialogOpen] = useState(false);
	const [grantForm, setGrantForm] = useState<CreditLotCreate1>({
		users_guid: "",
		source_type: "grant_owner",
		credits: 0,
		total_paid: "0",
		currency: "USD",
		expires_at: null,
		source_id: null,
	});

	const [periodStatusRows, setPeriodStatusRows] = useState<PeriodStatusRow[]>([]);
	const [periodYearFilter, setPeriodYearFilter] = useState<number>(new Date().getFullYear());

	const [imports, setImports] = useState<StagingImportRow[]>([]);
	const [selectedImport, setSelectedImport] = useState<number | null>(null);
	const [normalizedLineItems, setNormalizedLineItems] = useState<StagingLineItem[]>([]);
	const [purgeLogs, setPurgeLogs] = useState<any[]>([]);
	const [accountMappings, setAccountMappings] = useState<FinanceStagingAccountMapItem1[]>([]);
	const [vendors, setVendors] = useState<VendorItem[]>([]);
	const [mappingVendorFilter, setMappingVendorFilter] = useState<string>("");
	const [mappingFormOpen, setMappingFormOpen] = useState(false);
	const [mappingForm, setMappingForm] = useState<MappingFormState>(EMPTY_MAPPING_FORM);
	const [ledgers, setLedgers] = useState<FinanceLedger[]>([]);
	const [selectedLedgerRecid, setSelectedLedgerRecid] = useState<number | null>(null);
	const [promotingImport, setPromotingImport] = useState<number | null>(null);
	const [promoteTaskGuid, setPromoteTaskGuid] = useState<string | null>(null);
	const [promoteTaskStatus, setPromoteTaskStatus] = useState<AsyncTask | null>(null);
	const [promoteTaskEvents, setPromoteTaskEvents] = useState<AsyncTaskEvent[]>([]);
	const [promoteConfirmOpen, setPromoteConfirmOpen] = useState(false);
	const [notification, setNotification] = useState(false);
	const [notificationMessage, setNotificationMessage] = useState("Done");
	const [notificationSeverity, setNotificationSeverity] = useState<"success" | "error">("success");

	const fiscalYears = useMemo(() => {
		const years = new Set<number>();
		periods.forEach((period) => {
			if (typeof period.year === "number") {
				years.add(period.year);
			}
		});
		if (!years.size) {
			years.add(new Date().getFullYear());
		}
		return Array.from(years).sort((a, b) => b - a);
	}, [periods]);

	const periodsForSelectedYear = useMemo(
		() => periods.filter((period) => period.year === selectedYear),
		[periods, selectedYear],
	);

	const postingAccounts = useMemo(
		() => accounts.filter((account) => account.is_posting),
		[accounts],
	);

	const showNotification = (message: string, severity: "success" | "error" = "success"): void => {
		setNotificationMessage(message);
		setNotificationSeverity(severity);
		setNotification(true);
	};

	const openMappingForm = (mapping?: FinanceStagingAccountMapItem1): void => {
		if (!mapping) {
			setMappingForm(EMPTY_MAPPING_FORM);
			setMappingFormOpen(true);
			return;
		}
		setMappingForm({
			recid: typeof mapping.recid === "number" ? mapping.recid : null,
			vendors_recid: Number((mapping as any).vendors_recid || 0) || null,
			element_service_pattern: mapping.element_service_pattern || "",
			element_meter_pattern: String(mapping.element_meter_pattern || ""),
			accounts_guid: mapping.accounts_guid || "",
			element_priority: Number(mapping.element_priority || 0),
			element_description: String(mapping.element_description || ""),
			element_status: Number(mapping.element_status) === 1,
		});
		setMappingFormOpen(true);
	};

	const loadShared = useCallback(async (): Promise<void> => {
		const [periodRes, accountRes, vendorRes, ledgerRes] = await Promise.all([
			rpcCall<FinancePeriodsList1>("urn:finance:periods:list:1"),
			rpcCall<FinanceAccountsList1>("urn:finance:accounts:list:1"),
			rpcCall<{ vendors: VendorItem[] }>("urn:finance:vendors:list:1"),
			rpcCall<{ ledgers: FinanceLedger[] }>("urn:finance:ledgers:list:1"),
		]);
		setPeriods(periodRes.periods || []);
		setAccounts(accountRes.accounts || []);
		setVendors(vendorRes.vendors || []);
		setLedgers(ledgerRes.ledgers || []);
	}, []);

	const loadJournals = useCallback(async (): Promise<void> => {
		const payload = {
			journal_status: journalStatus === "" ? null : Number(journalStatus),
			fiscal_year: selectedYear || null,
			periods_guid: selectedPeriodGuid || null,
		};
		const res = await fetchJournalSummary(payload) as JournalSummaryList1;
		setJournals((res.journals || []) as JournalSummaryRow[]);
	}, [journalStatus, selectedPeriodGuid, selectedYear]);

	const loadLots = useCallback(async (): Promise<void> => {
		const res = await fetchCreditLotSummary({ users_guid: lotUserGuid || null }) as CreditLotSummaryList1;
		setLots((res.lots || []) as CreditLotSummaryRow[]);
	}, [lotUserGuid]);

	const loadPeriodStatus = useCallback(async (): Promise<void> => {
		const res = await fetchPeriodStatus({ fiscal_year: periodYearFilter || null }) as PeriodStatusList1;
		setPeriodStatusRows((res.periods || []) as PeriodStatusRow[]);
	}, [periodYearFilter]);

	const loadImports = useCallback(async (): Promise<void> => {
		const res = await rpcCall<StagingImportList1>("urn:finance:staging:list_imports:1", { status: 1 });
		setImports((res.imports || []) as StagingImportRow[]);
	}, []);

	const loadTaskEvents = useCallback(async (guid: string): Promise<void> => {
		const res = await rpcCall<{ events: AsyncTaskEvent[] }>("urn:system:async_tasks:list_task_events:1", { guid });
		setPromoteTaskEvents(res.events || []);
	}, []);

	const loadPurgeLogs = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ purge_logs: any[] }>("urn:finance:staging_purge_log:list:1", {});
		setPurgeLogs(res.purge_logs || []);
	}, []);

	const loadAccountMappings = useCallback(async (): Promise<void> => {
		const payload = mappingVendorFilter ? { vendors_recid: Number(mappingVendorFilter) } : {};
		const res = await rpcCall<FinanceStagingAccountMapList1>("urn:finance:staging_account_map:list:1", payload);
		setAccountMappings(res.mappings || []);
	}, [mappingVendorFilter]);

	const loadAll = useCallback(async (): Promise<void> => {
		try {
			await loadShared();
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadShared]);

	useEffect(() => {
		void loadAll();
	}, [loadAll]);

	useEffect(() => {
		if (tab === 0) {
			void loadJournals();
		}
		if (tab === 1) {
			void loadLots();
		}
		if (tab === 2) {
			void loadPeriodStatus();
		}
		if (tab === 3) {
			void loadImports();
			void loadPurgeLogs();
		}
		if (tab === 4) {
			void loadAccountMappings();
		}
	}, [tab, loadAccountMappings, loadImports, loadJournals, loadLots, loadPeriodStatus, loadPurgeLogs]);

	useEffect(() => {
		if (selectedImport === null) {
			setNormalizedLineItems([]);
			return;
		}

		void (async () => {
			const normalized = await rpcCall<{ line_items: StagingLineItem[] }>("urn:finance:staging:list_line_items:1", {
				imports_recid: selectedImport,
			});
			setNormalizedLineItems(normalized.line_items || []);
		})();
	}, [selectedImport]);

	useEffect(() => {
		setSelectedLedgerRecid(null);
		setPromotingImport(null);
		setPromoteTaskGuid(null);
		setPromoteTaskStatus(null);
		setPromoteTaskEvents([]);
		setPromoteConfirmOpen(false);
	}, [selectedImport]);

	useEffect(() => {
		if (!promoteTaskGuid || selectedImport === null || tab !== 3) {
			return;
		}

		let active = true;
		let intervalId = 0;

		const pollTask = async (): Promise<void> => {
			try {
				const task = await rpcCall<AsyncTask>("urn:system:async_tasks:get_task:1", { guid: promoteTaskGuid });
				if (!active) {
					return;
				}
				setPromoteTaskStatus(task);
				await loadTaskEvents(promoteTaskGuid);
				if (!active) {
					return;
				}
				if (task.status === 4) {
					window.clearInterval(intervalId);
					const journalRecid = task.result?.journal_recid ?? task.result?.journals_recid ?? task.result?.gl_journal_recid ?? task.result?.journal?.recid;
					showNotification(journalRecid ? `Promotion completed — journal #${journalRecid}` : "Promotion completed.");
					await loadImports();
					return;
				}
				if (task.status >= 5) {
					window.clearInterval(intervalId);
					showNotification(task.error || "Promotion failed.", "error");
				}
			} catch (e: any) {
				if (!active) {
					return;
				}
				const status = e?.response?.status ?? e?.status;
				if (status === 404) {
					return;
				}
				showNotification(e?.message || "Unable to monitor promotion task.", "error");
			}
		};

		void pollTask();
		intervalId = window.setInterval(() => void pollTask(), 4000);

		return () => {
			active = false;
			window.clearInterval(intervalId);
		};
	}, [loadImports, loadTaskEvents, promoteTaskGuid, selectedImport, tab]);

	if (forbidden) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h6">Access denied</Typography>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Accountant</PageTitle>
			<Divider sx={{ mb: 2 }} />
			<Tabs value={tab} onChange={(_, next) => setTab(next)}>
				<Tab label="Journals" />
				<Tab label="Credit Lots" />
				<Tab label="Periods" />
				<Tab label="Staging" />
				<Tab label="Account Mappings" />
			</Tabs>

			{tab === 0 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField
								select
								label="Fiscal Year"
								value={selectedYear}
								onChange={(e) => setSelectedYear(Number(e.target.value))}
								sx={{ minWidth: 120 }}
							>
								{fiscalYears.map((year) => (
									<MenuItem key={year} value={year}>{year}</MenuItem>
								))}
							</TextField>
							<TextField
								select
								label="Period"
								value={selectedPeriodGuid}
								onChange={(e) => setSelectedPeriodGuid(e.target.value)}
								sx={{ minWidth: 200 }}
							>
								<MenuItem value="">All</MenuItem>
								{periodsForSelectedYear.map((period) => (
									<MenuItem key={`${period.guid || period.period_number}`} value={period.guid || ""}>
										{getPeriodDisplayLabel(period)}
									</MenuItem>
								))}
							</TextField>
							<TextField
								select
								label="Status"
								value={journalStatus}
								onChange={(e) => setJournalStatus(e.target.value)}
								sx={{ minWidth: 140 }}
							>
								<MenuItem value="">All</MenuItem>
								<MenuItem value="0">Unposted</MenuItem>
								<MenuItem value="1">Posted</MenuItem>
								<MenuItem value="2">Reversed</MenuItem>
							</TextField>
							<Button variant="outlined" onClick={() => void loadJournals()}>Refresh</Button>
							<Button variant="contained" onClick={() => setCreateJournalOpen(true)}>Create Journal</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Posting Key</TableCell>
								<TableCell>Name</TableCell>
								<TableCell>Source Type</TableCell>
								<TableCell>Period</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Lines</TableCell>
								<TableCell>Total Debit</TableCell>
								<TableCell>Total Credit</TableCell>
								<TableCell>Posted By</TableCell>
								<TableCell>Created</TableCell>
								<TableCell />
							</TableRow>
						</TableHead>
						<TableBody>
							{journals.map((row) => (
								<TableRow
									hover
									key={row.recid}
									sx={{ cursor: "pointer" }}
									onClick={async () => {
										try {
											const linesRes = await fetchLines({ journals_recid: row.recid }) as JournalLineList1;
											setJournalLines(linesRes.lines || []);
										} catch {
											setJournalLines([]);
										}
										setSelectedJournal(row);
										setJournalDialogOpen(true);
									}}
								>
									<TableCell>{row.posting_key || "-"}</TableCell>
									<TableCell>{row.name}</TableCell>
									<TableCell>{row.source_type}</TableCell>
									<TableCell>{row.period_name || "-"}</TableCell>
									<TableCell>
										<Chip
											label={row.journal_status === 1 ? "Posted" : row.journal_status === 2 ? "Reversed" : "Unposted"}
											color={row.journal_status === 1 ? "success" : row.journal_status === 2 ? "error" : "warning"}
										/>
									</TableCell>
									<TableCell>{row.line_count}</TableCell>
									<TableCell>{Number(row.total_debit || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(row.total_credit || 0).toFixed(2)}</TableCell>
									<TableCell>{row.posted_by || "-"}</TableCell>
									<TableCell>{row.created_on}</TableCell>
									<TableCell onClick={(e) => e.stopPropagation()}>
										{row.journal_status === 0 && (
											<Button
												size="small"
												variant="contained"
												onClick={async () => {
													if (!window.confirm("Post this journal?")) {
														return;
													}
													await fetchPost({ recid: row.recid });
													await loadJournals();
												}}
											>
												Post
											</Button>
										)}
									{row.journal_status === 1 && row.source_type !== "reversal" && (
										<Button
												size="small"
												color="error"
												onClick={async () => {
													if (!window.confirm("Reverse this journal?")) {
														return;
													}
													await fetchReverse({ recid: row.recid });
													await loadJournals();
												}}
											>
												Reverse
											</Button>
										)}
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 1 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField label="User GUID (optional)" value={lotUserGuid} onChange={(e) => setLotUserGuid(e.target.value)} />
							<Button variant="outlined" onClick={() => void loadLots()}>Refresh</Button>
							<Button variant="contained" onClick={() => setGrantDialogOpen(true)}>Grant Credits</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Lot Number</TableCell>
								<TableCell>User</TableCell>
								<TableCell>Source Type</TableCell>
								<TableCell>Original</TableCell>
								<TableCell>Remaining</TableCell>
								<TableCell>Unit Price</TableCell>
								<TableCell>Total Paid</TableCell>
								<TableCell>Expired</TableCell>
								<TableCell>Events</TableCell>
								<TableCell>Total Consumed</TableCell>
								<TableCell>Created</TableCell>
								<TableCell />
							</TableRow>
						</TableHead>
						<TableBody>
							{lots.map((row) => (
								<TableRow
									hover
									key={row.recid}
									sx={{ cursor: "pointer" }}
									onClick={async () => {
										const eventsRes = await fetchListEvents({ lots_recid: row.recid }) as CreditLotEventList1;
										setLotEvents(eventsRes.events || []);
										setSelectedLotRecid(row.recid);
										setLotEventDialogOpen(true);
									}}
								>
									<TableCell>{row.lot_number}</TableCell>
									<TableCell>{row.users_guid}</TableCell>
									<TableCell>{row.source_type}</TableCell>
									<TableCell>{Number(row.credits_original || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(row.credits_remaining || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(row.unit_price || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(row.total_paid || 0).toFixed(2)}</TableCell>
									<TableCell>
										<Chip label={row.expired ? "Expired" : "Active"} color={row.expired ? "error" : "success"} />
									</TableCell>
									<TableCell>{row.event_count}</TableCell>
									<TableCell>{Number(row.total_consumed || 0).toFixed(2)}</TableCell>
									<TableCell>{row.created_on}</TableCell>
									<TableCell onClick={(e) => e.stopPropagation()}>
										{!row.expired && (
											<Button
												size="small"
												color="error"
												onClick={async () => {
													if (!window.confirm("Expire this credit lot?")) {
														return;
													}
													await fetchExpire({ recid: row.recid });
													await loadLots();
												}}
											>
												Expire
											</Button>
										)}
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 2 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField
								select
								label="Fiscal Year"
								value={periodYearFilter}
								onChange={(e) => setPeriodYearFilter(Number(e.target.value))}
								sx={{ minWidth: 120 }}
							>
								{fiscalYears.map((year) => (
									<MenuItem key={year} value={year}>{year}</MenuItem>
								))}
							</TextField>
							<Button variant="outlined" onClick={() => void loadPeriodStatus()}>Refresh</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Period Name</TableCell>
								<TableCell>Start</TableCell>
								<TableCell>End</TableCell>
								<TableCell>Close Type</TableCell>
								<TableCell>Total Journals</TableCell>
								<TableCell>Unposted</TableCell>
								<TableCell>Posted</TableCell>
								<TableCell>Reversed</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{periodStatusRows.map((row) => (
								<TableRow key={row.guid || row.period_name}>
									<TableCell>{row.period_name}</TableCell>
									<TableCell>{row.start_date}</TableCell>
									<TableCell>{row.end_date}</TableCell>
									<TableCell>
										<Chip label={row.close_type === 0 ? "Open" : "Closed"} color={row.close_type === 0 ? "success" : "error"} />
									</TableCell>
									<TableCell>{row.total_journals}</TableCell>
									<TableCell>{row.unposted_count}</TableCell>
									<TableCell>{row.posted_count}</TableCell>
									<TableCell>{row.reversed_count}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 3 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>RecId</TableCell>
								<TableCell>Source</TableCell>
								<TableCell>Metric</TableCell>
								<TableCell>Period Start</TableCell>
								<TableCell>Period End</TableCell>
								<TableCell>Rows</TableCell>
								<TableCell>Requested By</TableCell>
								<TableCell>Approved By</TableCell>
								<TableCell>Approved On</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Error</TableCell>
								<TableCell>Created On</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{imports.map((row) => (
								<TableRow
									hover
									key={row.recid}
									selected={selectedImport === row.recid}
									sx={{ cursor: "pointer" }}
									onClick={async () => {
										setSelectedImport(row.recid);
										const normalized = await rpcCall<{ line_items: StagingLineItem[] }>("urn:finance:staging:list_line_items:1", {
											imports_recid: row.recid,
										});
										setNormalizedLineItems(normalized.line_items || []);
									}}
								>
									<TableCell>{row.recid}</TableCell>
									<TableCell>{row.element_source}</TableCell>
									<TableCell>{row.element_metric}</TableCell>
									<TableCell>{row.element_period_start}</TableCell>
									<TableCell>{row.element_period_end}</TableCell>
									<TableCell>{row.element_row_count}</TableCell>
									<TableCell>{row.element_requested_by || "-"}</TableCell>
									<TableCell>{row.element_approved_by || "-"}</TableCell>
									<TableCell>{row.element_approved_on || "-"}</TableCell>
									<TableCell>
										<Chip
											label={IMPORT_STATUS_CONFIG[row.element_status]?.label || row.element_status}
											color={IMPORT_STATUS_CONFIG[row.element_status]?.color || "default"}
										/>
									</TableCell>
									<TableCell>{row.element_error ? `${String(row.element_error).slice(0, 80)}${String(row.element_error).length > 80 ? "..." : ""}` : ""}</TableCell>
									<TableCell>{String(row.element_created_on || "")}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>

					{selectedImport !== null && (() => {
						const selectedRow = imports.find((row) => row.recid === selectedImport);
						if (!selectedRow) {
							return null;
						}

						return (
							<Paper sx={{ p: 2 }}>
								<Stack spacing={2}>
									<Stack direction={{ xs: "column", md: "row" }} spacing={1} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
										<Box>
											<Typography variant="h6">
												Import #{selectedRow.recid} — {selectedRow.element_row_count} rows
											</Typography>
											<Typography variant="body2" color="text.secondary">
												{selectedRow.element_source} • {selectedRow.element_period_start} to {selectedRow.element_period_end}
											</Typography>
											<Typography variant="body2" color="text.secondary">
												Requested by {selectedRow.element_requested_by || "Unknown"} • Approved by {selectedRow.element_approved_by || "Unknown"}
											</Typography>
										</Box>
										{selectedRow.element_status === 1 && (
											<Button
												variant="contained"
												color="success"
												onClick={() => {
													setSelectedLedgerRecid(null);
													setPromoteConfirmOpen(true);
												}}
											>
												Promote Import
											</Button>
										)}
									</Stack>

									{promotingImport === selectedRow.recid && promoteTaskStatus && (
										<Paper variant="outlined" sx={{ p: 2 }}>
											<Stack spacing={1.5}>
												<Stack direction="row" spacing={1} alignItems="center">
													{promoteTaskStatus.status === 0 || promoteTaskStatus.status === 1 ? <CircularProgress size={18} /> : null}
													<Typography variant="subtitle2">
														Promotion Task {promoteTaskGuid ? `(${promoteTaskGuid})` : ""}
													</Typography>
												</Stack>
												<Typography variant="body2">
													Step {promoteTaskStatus.step_index || 0} of {PROMOTE_PIPELINE_STEPS.length}: {promoteTaskStatus.current_step || "Waiting to start"}
												</Typography>
												<LinearProgress
													variant="determinate"
													value={Math.min(100, ((promoteTaskStatus.step_index || 0) / PROMOTE_PIPELINE_STEPS.length) * 100)}
												/>
												{promoteTaskStatus.status === 4 && (
													<Alert severity="success">
														Promotion completed{(promoteTaskStatus.result?.journal_recid ?? promoteTaskStatus.result?.journals_recid) ? ` — journal #${promoteTaskStatus.result?.journal_recid ?? promoteTaskStatus.result?.journals_recid}` : ""}.
													</Alert>
												)}
												{promoteTaskStatus.status >= 5 && promoteTaskStatus.error && (
													<Alert severity="error">{promoteTaskStatus.error}</Alert>
												)}
												{promoteTaskEvents.length > 0 && (
													<Box>
														<Typography variant="subtitle2" sx={{ mb: 1 }}>Recent Task Events</Typography>
														<Stack spacing={0.5}>
															{promoteTaskEvents.slice(-4).reverse().map((event, index) => (
																<Typography key={`${promoteTaskGuid || "task"}-${index}`} variant="body2" color="text.secondary">
																	{event.event_name || event.step_name || event.message || JSON.stringify(event)}
																</Typography>
															))}
														</Stack>
													</Box>
												)}
											</Stack>
										</Paper>
									)}

									<Table size="small">
										<TableHead>
											<TableRow>
												<TableCell>Date</TableCell>
												<TableCell>Vendor</TableCell>
												<TableCell>Service</TableCell>
												<TableCell>Category</TableCell>
												<TableCell>Description</TableCell>
												<TableCell>Quantity</TableCell>
												<TableCell>Amount</TableCell>
												<TableCell>Currency</TableCell>
											</TableRow>
										</TableHead>
										<TableBody>
											{normalizedLineItems.map((line) => (
												<TableRow key={line.recid}>
													<TableCell>{line.element_date || ""}</TableCell>
													<TableCell>{line.vendor_name || line.vendors_recid}</TableCell>
													<TableCell>{line.element_service || ""}</TableCell>
													<TableCell>{line.element_category || ""}</TableCell>
													<TableCell>{line.element_description || ""}</TableCell>
													<TableCell>{line.element_quantity || ""}</TableCell>
													<TableCell>{line.element_amount || ""}</TableCell>
													<TableCell>{line.element_currency || ""}</TableCell>
												</TableRow>
											))}
										</TableBody>
									</Table>
								</Stack>
							</Paper>
						);
					})()}

					<Typography variant="h6" sx={{ mt: 3 }}>Purge Log</Typography>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Vendor</TableCell>
								<TableCell>Period</TableCell>
								<TableCell>Purged Count</TableCell>
								<TableCell>Last Purged</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{purgeLogs.map((log: any) => (
								<TableRow key={log.recid}>
									<TableCell>{vendors.find((vendor) => vendor.recid === log.vendors_recid)?.element_name || log.vendors_recid}</TableCell>
									<TableCell>{log.element_period_key}</TableCell>
									<TableCell>{log.element_purged_count}</TableCell>
									<TableCell>{String(log.element_purged_on || "")}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}


			{tab === 4 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1}>
							<TextField select label="Vendor Filter" value={mappingVendorFilter} onChange={(event) => setMappingVendorFilter(event.target.value)} sx={{ minWidth: 180 }}>
								<MenuItem value="">All Vendors</MenuItem>
								{vendors.map((vendor) => (<MenuItem key={vendor.recid} value={String(vendor.recid)}>{vendor.element_name}</MenuItem>))}
							</TextField>
							<Button variant="outlined" onClick={() => void loadAccountMappings()}>Refresh</Button>
							<Button variant="contained" onClick={() => openMappingForm()}>Create Mapping</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Vendor</TableCell><TableCell>Service Pattern</TableCell>
								<TableCell>Meter Pattern</TableCell>
								<TableCell>Account</TableCell>
								<TableCell>Priority</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Actions</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{accountMappings.map((mapping) => (
								<TableRow key={mapping.recid}>
									<TableCell>{(mapping as any).vendor_name || "Any"}</TableCell><TableCell>{mapping.element_service_pattern}</TableCell>
									<TableCell>{mapping.element_meter_pattern || "-"}</TableCell>
									<TableCell>{mapping.account_number} - {mapping.account_name}</TableCell>
									<TableCell>{mapping.element_priority}</TableCell>
									<TableCell>
										<Chip label={Number(mapping.element_status) === 1 ? "Active" : "Disabled"} color={Number(mapping.element_status) === 1 ? "success" : "default"} />
									</TableCell>
									<TableCell>
										<Stack direction="row" spacing={1}>
											<Button size="small" onClick={() => openMappingForm(mapping)}>Edit</Button>
											<Button
												size="small"
												color="error"
												onClick={async () => {
												if (!window.confirm("Delete this mapping?")) {
													return;
												}
												await rpcCall("urn:finance:staging_account_map:delete:1", { recid: mapping.recid });
												showNotification("Mapping deleted");
												await loadAccountMappings();
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

					<Collapse in={mappingFormOpen}>
						<Paper sx={{ p: 2 }}>
							<Stack spacing={2}>
								<Stack direction="row" spacing={1} flexWrap="wrap">
									<TextField
										select
										label="Vendor"
										value={mappingForm.vendors_recid || ""}
										onChange={(event) => setMappingForm((previous) => ({ ...previous, vendors_recid: event.target.value ? Number(event.target.value) : null }))}
										sx={{ minWidth: 180 }}
									>
										<MenuItem value="">Any Vendor</MenuItem>
										{vendors.map((vendor) => (
											<MenuItem key={vendor.recid} value={vendor.recid}>{vendor.element_name}</MenuItem>
										))}
									</TextField>
									<TextField
										label="Service Pattern"
										value={mappingForm.element_service_pattern}
										onChange={(event) => setMappingForm((previous) => ({ ...previous, element_service_pattern: event.target.value }))}
										required
									/>
									<TextField
										label="Meter Pattern"
										value={mappingForm.element_meter_pattern}
										onChange={(event) => setMappingForm((previous) => ({ ...previous, element_meter_pattern: event.target.value }))}
									/>
									<TextField
										select
										label="Account"
										value={mappingForm.accounts_guid}
										onChange={(event) => setMappingForm((previous) => ({ ...previous, accounts_guid: event.target.value }))}
									>
										<MenuItem value="">Select account</MenuItem>
										{postingAccounts.map((account) => (
											<MenuItem key={account.guid || account.number} value={String(account.guid || "")}>
												{account.number} - {account.name}
											</MenuItem>
										))}
									</TextField>
									<TextField
										type="number"
										label="Priority"
										value={mappingForm.element_priority}
										onChange={(event) => setMappingForm((previous) => ({ ...previous, element_priority: Number(event.target.value) }))}
									/>
								</Stack>
								<TextField
									label="Description"
									value={mappingForm.element_description}
									onChange={(event) => setMappingForm((previous) => ({ ...previous, element_description: event.target.value }))}
								/>
								<FormControlLabel
									control={
										<Checkbox
											checked={mappingForm.element_status}
											onChange={(event) => setMappingForm((previous) => ({ ...previous, element_status: event.target.checked }))}
										/>
									}
									label="Active"
								/>
								<Stack direction="row" spacing={1}>
									<Button
										variant="contained"
										onClick={async () => {
											if (!mappingForm.element_service_pattern || !mappingForm.accounts_guid) {
												showNotification("Service pattern and account are required", "error");
												return;
											}
											const payload = {
												recid: mappingForm.recid,
												vendors_recid: mappingForm.vendors_recid,
								element_service_pattern: mappingForm.element_service_pattern,
												element_meter_pattern: mappingForm.element_meter_pattern || null,
												accounts_guid: mappingForm.accounts_guid,
												element_priority: mappingForm.element_priority,
												element_description: mappingForm.element_description || null,
												element_status: mappingForm.element_status ? 1 : 0,
											};
											await rpcCall("urn:finance:staging_account_map:upsert:1", payload);
											showNotification(mappingForm.recid ? "Mapping updated" : "Mapping created");
											setMappingFormOpen(false);
											setMappingForm(EMPTY_MAPPING_FORM);
											await loadAccountMappings();
										}}
									>
										Save
									</Button>
									<Button
										onClick={() => {
											setMappingFormOpen(false);
											setMappingForm(EMPTY_MAPPING_FORM);
										}}
									>
										Cancel
									</Button>
								</Stack>
							</Stack>
						</Paper>
					</Collapse>
				</Stack>
			)}

			<Dialog open={promoteConfirmOpen} onClose={() => setPromoteConfirmOpen(false)}>
				<DialogTitle>Promote Import</DialogTitle>
				<DialogContent>
					<DialogContentText>
						Promote import #{selectedImport}? This will create a journal entry with the classified costs in the selected ledger.
					</DialogContentText>
					<TextField
						select
						label="Target Ledger"
						value={selectedLedgerRecid ?? ""}
						onChange={(e) => setSelectedLedgerRecid(e.target.value ? Number(e.target.value) : null)}
						fullWidth
						sx={{ mt: 2 }}
					>
						<MenuItem value="">Select ledger</MenuItem>
						{ledgers.map((ledger) => (
							<MenuItem key={ledger.recid} value={ledger.recid}>
								{ledger.element_name}
							</MenuItem>
						))}
					</TextField>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setPromoteConfirmOpen(false)}>Cancel</Button>
					<Button
						variant="contained"
						color="success"
						disabled={selectedLedgerRecid === null}
						onClick={async () => {
							if (selectedImport === null) {
								return;
							}
							try {
								const res = await rpcCall<StagingPromoteResult1>("urn:finance:staging:promote:1", {
									imports_recid: selectedImport,
									ledgers_recid: selectedLedgerRecid,
								});
								setPromotingImport(selectedImport);
								setPromoteTaskGuid(res.task_guid);
								setPromoteTaskStatus({
									guid: res.task_guid,
									status: 0,
									handler_name: null,
									current_step: null,
									step_index: 0,
									step_count: PROMOTE_PIPELINE_STEPS.length,
									result: null,
									error: null,
								});
								setPromoteTaskEvents([]);
								showNotification(`Promotion started for import #${selectedImport}.`);
							} catch (e: any) {
								showNotification(e?.message || "Promotion failed.", "error");
							} finally {
								setPromoteConfirmOpen(false);
							}
						}}
					>
						Promote
					</Button>
				</DialogActions>
			</Dialog>

			<Dialog open={journalDialogOpen} onClose={() => setJournalDialogOpen(false)} maxWidth="md" fullWidth>
				<DialogTitle>{selectedJournal?.name || "Journal Lines"}</DialogTitle>
				<DialogContent>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Line #</TableCell>
								<TableCell>Account GUID</TableCell>
								<TableCell>Debit</TableCell>
								<TableCell>Credit</TableCell>
								<TableCell>Description</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{journalLines.map((line) => (
								<TableRow key={line.recid || `${line.journals_recid}-${line.line_number}`}>
									<TableCell>{line.line_number}</TableCell>
									<TableCell>{line.accounts_guid}</TableCell>
									<TableCell>{Number(line.debit || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(line.credit || 0).toFixed(2)}</TableCell>
									<TableCell>{line.description || ""}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</DialogContent>
				<DialogActions><Button onClick={() => setJournalDialogOpen(false)}>Close</Button></DialogActions>
			</Dialog>

			<Dialog open={createJournalOpen} onClose={() => setCreateJournalOpen(false)} maxWidth="lg" fullWidth>
				<DialogTitle>Create Journal</DialogTitle>
				<DialogContent>
					<Stack spacing={2} sx={{ mt: 1 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField label="Name" value={journalForm.name} onChange={(e) => setJournalForm((prev) => ({ ...prev, name: e.target.value }))} />
							<TextField label="Description" value={String(journalForm.description || "")} onChange={(e) => setJournalForm((prev) => ({ ...prev, description: e.target.value }))} />
							<TextField
								select
								label="Period"
								value={String(journalForm.periods_guid || "")}
								onChange={(e) => setJournalForm((prev) => ({ ...prev, periods_guid: e.target.value || null }))}
							>
								<MenuItem value="">Select period</MenuItem>
								{periods.map((period) => (
									<MenuItem key={`${period.guid || period.period_number}`} value={period.guid || ""}>{getPeriodDisplayLabel(period)}</MenuItem>
								))}
							</TextField>
						</Stack>
						<Table size="small">
							<TableHead>
								<TableRow>
									<TableCell>Line #</TableCell>
									<TableCell>Account</TableCell>
									<TableCell>Debit</TableCell>
									<TableCell>Credit</TableCell>
									<TableCell>Description</TableCell>
									<TableCell />
								</TableRow>
							</TableHead>
							<TableBody>
								{journalForm.lines.map((line, index) => (
									<TableRow key={`line-${line.line_number}`}>
										<TableCell>{line.line_number}</TableCell>
										<TableCell>
											<TextField
												select
												size="small"
												value={line.accounts_guid}
												onChange={(e) => setJournalForm((prev) => ({
													...prev,
													lines: prev.lines.map((item, itemIndex) => itemIndex === index ? { ...item, accounts_guid: e.target.value } : item),
												}))}
											>
												<MenuItem value="">Select account</MenuItem>
												{postingAccounts.map((account) => (
													<MenuItem key={account.guid || account.number} value={String(account.guid || "")}>{account.number} - {account.name}</MenuItem>
												))}
											</TextField>
										</TableCell>
										<TableCell>
											<TextField
												size="small"
												value={line.debit}
												onChange={(e) => setJournalForm((prev) => ({
													...prev,
													lines: prev.lines.map((item, itemIndex) => itemIndex === index ? { ...item, debit: e.target.value } : item),
												}))}
											/>
										</TableCell>
										<TableCell>
											<TextField
												size="small"
												value={line.credit}
												onChange={(e) => setJournalForm((prev) => ({
													...prev,
													lines: prev.lines.map((item, itemIndex) => itemIndex === index ? { ...item, credit: e.target.value } : item),
												}))}
											/>
										</TableCell>
										<TableCell>
											<TextField
												size="small"
												value={String(line.description || "")}
												onChange={(e) => setJournalForm((prev) => ({
													...prev,
													lines: prev.lines.map((item, itemIndex) => itemIndex === index ? { ...item, description: e.target.value } : item),
												}))}
											/>
										</TableCell>
										<TableCell>
											<Button
												disabled={journalForm.lines.length <= 1}
												onClick={() => setJournalForm((prev) => ({
													...prev,
													lines: prev.lines.filter((_, itemIndex) => itemIndex !== index).map((item, itemIndex) => ({ ...item, line_number: itemIndex + 1 })),
												}))}
											>
												Remove
											</Button>
										</TableCell>
									</TableRow>
								))}
							</TableBody>
						</Table>
						<Button onClick={() => setJournalForm((prev) => ({ ...prev, lines: [...prev.lines, DEFAULT_JOURNAL_LINE(prev.lines.length + 1)] }))}>Add Line</Button>
					</Stack>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setCreateJournalOpen(false)}>Cancel</Button>
					<Button
						variant="contained"
						onClick={async () => {
							await fetchCreate(journalForm);
							setCreateJournalOpen(false);
							setJournalForm({
								name: "",
								description: "",
								posting_key: null,
								source_type: "manual",
								source_id: null,
								periods_guid: null,
								ledgers_recid: null,
								lines: [DEFAULT_JOURNAL_LINE(1)],
								post: false,
							});
							await loadJournals();
						}}
					>
						Create
					</Button>
				</DialogActions>
			</Dialog>

			<Dialog open={lotEventDialogOpen} onClose={() => setLotEventDialogOpen(false)} maxWidth="md" fullWidth>
				<DialogTitle>Lot Events {selectedLotRecid ? `#${selectedLotRecid}` : ""}</DialogTitle>
				<DialogContent>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Type</TableCell>
								<TableCell>Credits</TableCell>
								<TableCell>Unit Price</TableCell>
								<TableCell>Description</TableCell>
								<TableCell>Journal</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{lotEvents.map((event) => (
								<TableRow key={event.recid || `${event.lots_recid}-${event.event_type}-${event.credits}`}>
									<TableCell>{event.event_type}</TableCell>
									<TableCell>{Number(event.credits || 0).toFixed(2)}</TableCell>
									<TableCell>{Number(event.unit_price || 0).toFixed(2)}</TableCell>
									<TableCell>{event.description || ""}</TableCell>
									<TableCell>{event.journals_recid || "-"}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</DialogContent>
				<DialogActions><Button onClick={() => setLotEventDialogOpen(false)}>Close</Button></DialogActions>
			</Dialog>

			<Dialog open={grantDialogOpen} onClose={() => setGrantDialogOpen(false)} maxWidth="sm" fullWidth>
				<DialogTitle>Grant Credits</DialogTitle>
				<DialogContent>
					<Stack spacing={2} sx={{ mt: 1 }}>
						<TextField label="User GUID" value={grantForm.users_guid} onChange={(e) => setGrantForm((prev) => ({ ...prev, users_guid: e.target.value }))} />
						<TextField
							select
							label="Source Type"
							value={grantForm.source_type}
							onChange={(e) => setGrantForm((prev) => ({ ...prev, source_type: e.target.value }))}
						>
							<MenuItem value="grant_owner">grant_owner</MenuItem>
							<MenuItem value="grant_promo">grant_promo</MenuItem>
							<MenuItem value="grant_signup">grant_signup</MenuItem>
						</TextField>
						<TextField type="number" label="Credits" value={grantForm.credits} onChange={(e) => setGrantForm((prev) => ({ ...prev, credits: Number(e.target.value) }))} />
						<TextField label="Expires At (optional ISO datetime)" value={String(grantForm.expires_at || "")} onChange={(e) => setGrantForm((prev) => ({ ...prev, expires_at: e.target.value || null }))} />
					</Stack>
				</DialogContent>
				<DialogActions>
					<Button onClick={() => setGrantDialogOpen(false)}>Cancel</Button>
					<Button
						variant="contained"
						onClick={async () => {
							await fetchCreditCreate({ ...grantForm, total_paid: "0" });
							setGrantDialogOpen(false);
							setGrantForm({
								users_guid: "",
								source_type: "grant_owner",
								credits: 0,
								total_paid: "0",
								currency: "USD",
								expires_at: null,
								source_id: null,
							});
							await loadLots();
						}}
					>
						Grant
					</Button>
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

export default FinanceAccountantPage;
