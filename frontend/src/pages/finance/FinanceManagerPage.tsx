import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Alert,
	Box,
	Button,
	Chip,
	CircularProgress,
	Dialog,
	DialogActions,
	DialogContent,
	DialogContentText,
	DialogTitle,
	Divider,
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
import PageTitle from "../../components/PageTitle";
import { rpcCall } from "../../shared/RpcModels";

type FinanceNumber = {
	recid?: number | null;
	accounts_guid: string;
	prefix?: string | null;
	account_number: string;
	last_number: number;
	allocation_size: number;
	reset_policy: string;
	account_name?: string | null;
};

type FinanceAccount = {
	guid: string;
	name: string;
};

type StagingImport = {
	recid: number;
	element_source: string;
	element_scope: string | null;
	element_metric: string;
	element_period_start: string;
	element_period_end: string;
	element_row_count: number;
	element_status: number;
	element_error: string | null;
	element_created_on: string;
	element_modified_on: string;
};

type StagingLineItem = {
	recid: number;
	imports_recid: number;
	vendors_recid: number;
	vendor_name: string | null;
	element_date: string | null;
	element_service: string | null;
	element_category: string | null;
	element_description: string | null;
	element_quantity: string | null;
	element_unit_price: string | null;
	element_amount: string;
	element_currency: string | null;
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

type FinanceLedger = {
	recid: number;
	element_name: string;
};

type AsyncTaskEvent = Record<string, any>;

type PeriodStatus = {
	period_guid: string;
	fiscal_year: number;
	period_number: number;
	period_name: string;
	start_date: string;
	end_date: string;
	close_type: number;
	period_status: number;
	has_closing_week: boolean;
	total_journals: number;
	unposted_journals: number;
	posted_journals: number;
	reversed_journals: number;
};

type TrialBalanceRow = {
	period_guid: string;
	fiscal_year: number;
	period_number: number;
	period_name: string;
	account_guid: string;
	account_number: string;
	account_name: string;
	account_type: number;
	total_debit: number;
	total_credit: number;
	net_balance: number;
};

type JournalSummaryRow = {
	recid: number;
	journal_name: string;
	journal_description: string | null;
	posting_key: string | null;
	source_type: string | null;
	source_id: string | null;
	journal_status: number;
	periods_guid: string | null;
	fiscal_year: number | null;
	period_name: string | null;
	posted_by: string | null;
	posted_on: string | null;
	reversed_by: number | null;
	reversal_of: number | null;
	created_on: string;
	line_count: number;
	total_debit: number;
	total_credit: number;
};

const IMPORT_STATUS_CONFIG: Record<number, { label: string; color: "default" | "success" | "error" | "info" | "warning" }> = {
	0: { label: "Pending", color: "warning" },
	1: { label: "Completed", color: "success" },
	2: { label: "Failed", color: "error" },
	3: { label: "Promoted", color: "info" },
};

const PROMOTE_PIPELINE_STEPS = ["validate_import", "classify_costs", "create_journal", "mark_promoted"] as const;

const ACCOUNT_TYPES: { value: number; label: string }[] = [
	{ value: 0, label: "Asset" },
	{ value: 1, label: "Liability" },
	{ value: 2, label: "Equity" },
	{ value: 3, label: "Revenue" },
	{ value: 4, label: "Expense" },
];

const PERIOD_TYPE_CONFIG: Record<number, { label: string; color: "default" | "info" | "warning" }> = {
	0: { label: "Standard", color: "default" },
	1: { label: "Quarter Close", color: "warning" },
	2: { label: "Year Close", color: "info" },
};

const PERIOD_STATUS_CONFIG: Record<number, { label: string; color: "default" | "success" | "error" }> = {
	1: { label: "Open", color: "success" },
	2: { label: "Closed", color: "error" },
	3: { label: "Locked", color: "default" },
};

const getPeriodDisplayLabel = (row: { fiscal_year: number; period_name: string }): string => {
	return `FY${row.fiscal_year} - ${row.period_name}`;
};

const FinanceManagerPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [numbers, setNumbers] = useState<FinanceNumber[]>([]);
	const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
	const [numberForm, setNumberForm] = useState<FinanceNumber>({
		recid: null,
		accounts_guid: "",
		prefix: "",
		account_number: "",
		last_number: 1000,
		allocation_size: 10,
		reset_policy: "Never",
	});

	const [importStartDate, setImportStartDate] = useState("");
	const [importEndDate, setImportEndDate] = useState("");
	const [invoiceMonth, setInvoiceMonth] = useState("");
	const [importing, setImporting] = useState(false);
	const [importingInvoices, setImportingInvoices] = useState(false);
	const [imports, setImports] = useState<StagingImport[]>([]);
	const [selectedImport, setSelectedImport] = useState<number | null>(null);
	const [importDetails, setImportDetails] = useState<Record<string, any>[]>([]);
	const [detailView, setDetailView] = useState<"raw" | "line_items">("raw");
	const [lineItems, setLineItems] = useState<StagingLineItem[]>([]);
	const [ledgers, setLedgers] = useState<FinanceLedger[]>([]);
	const [selectedLedgerRecid, setSelectedLedgerRecid] = useState<number | null>(null);
	const [promotingImport, setPromotingImport] = useState<number | null>(null);
	const [promoteTaskGuid, setPromoteTaskGuid] = useState<string | null>(null);
	const [promoteTaskStatus, setPromoteTaskStatus] = useState<AsyncTask | null>(null);
	const [promoteTaskEvents, setPromoteTaskEvents] = useState<AsyncTaskEvent[]>([]);
	const [billingMessage, setBillingMessage] = useState<{ severity: "success" | "error" | "info"; text: string } | null>(null);
	const [confirmAction, setConfirmAction] = useState<{ type: "promote" | "delete"; recid: number } | null>(null);

	const [periodYear, setPeriodYear] = useState<number>(new Date().getFullYear());
	const [allPeriodStatusRows, setAllPeriodStatusRows] = useState<PeriodStatus[]>([]);
	const [periodStatusRows, setPeriodStatusRows] = useState<PeriodStatus[]>([]);

	const [trialYear, setTrialYear] = useState<number>(new Date().getFullYear());
	const [trialPeriodGuid, setTrialPeriodGuid] = useState<string>("");
	const [trialRows, setTrialRows] = useState<TrialBalanceRow[]>([]);

	const [journalYear, setJournalYear] = useState<number>(new Date().getFullYear());
	const [journalPeriodGuid, setJournalPeriodGuid] = useState<string>("");
	const [journalStatus, setJournalStatus] = useState<string>("");
	const [journalRows, setJournalRows] = useState<JournalSummaryRow[]>([]);

	const yearOptions = useMemo(() => {
		const years = new Set<number>();
		allPeriodStatusRows.forEach((row) => years.add(row.fiscal_year));
		if (!years.size) {
			years.add(new Date().getFullYear());
		}
		return Array.from(years).sort((a, b) => b - a);
	}, [allPeriodStatusRows]);

	const periodsForTrialYear = useMemo(
		() => allPeriodStatusRows.filter((row) => row.fiscal_year === trialYear),
		[allPeriodStatusRows, trialYear],
	);

	const periodsForJournalYear = useMemo(
		() => allPeriodStatusRows.filter((row) => row.fiscal_year === journalYear),
		[allPeriodStatusRows, journalYear],
	);

	const loadNumbers = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ numbers: FinanceNumber[] }>("urn:finance:numbers:list:1");
		setNumbers(res.numbers || []);
	}, []);

	const loadAccounts = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ accounts: FinanceAccount[] }>("urn:finance:accounts:list:1");
		setAccounts((res.accounts || []).filter((account) => Boolean(account.guid)));
	}, []);

	const loadLedgers = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ ledgers: FinanceLedger[] }>("urn:finance:ledgers:list:1");
		setLedgers(res.ledgers || []);
	}, []);

	const loadImports = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ imports: StagingImport[] }>("urn:finance:staging:list_imports:1");
		setImports(res.imports || []);
	}, []);

	const loadImportDetails = useCallback(async (importsRecid: number): Promise<void> => {
		const details = await rpcCall<Record<string, any>[]>("urn:finance:staging:list_details:1", {
			imports_recid: importsRecid,
		});
		setImportDetails(details || []);
	}, []);

	const loadLineItems = useCallback(async (importsRecid: number): Promise<void> => {
		const res = await rpcCall<{ line_items: StagingLineItem[] }>("urn:finance:staging:list_line_items:1", {
			imports_recid: importsRecid,
		});
		setLineItems(res.line_items || []);
	}, []);

	const loadTaskEvents = useCallback(async (guid: string): Promise<void> => {
		const res = await rpcCall<{ events: AsyncTaskEvent[] }>("urn:system:async_tasks:list_task_events:1", { guid });
		setPromoteTaskEvents(res.events || []);
	}, []);

	const loadPeriodStatus = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ periods: PeriodStatus[] }>("urn:finance:reporting:period_status:1", {
			fiscal_year: periodYear || null,
		});
		setPeriodStatusRows(res.periods || []);
	}, [periodYear]);

	const loadAllPeriodStatus = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ periods: PeriodStatus[] }>("urn:finance:reporting:period_status:1", {});
		setAllPeriodStatusRows(res.periods || []);
	}, []);

	const loadTrialBalance = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ rows: TrialBalanceRow[] }>("urn:finance:reporting:trial_balance:1", {
			fiscal_year: trialYear || null,
			period_guid: trialPeriodGuid || null,
		});
		setTrialRows(res.rows || []);
	}, [trialPeriodGuid, trialYear]);

	const loadJournalSummary = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ journals: JournalSummaryRow[] }>("urn:finance:reporting:journal_summary:1", {
			journal_status: journalStatus === "" ? null : Number(journalStatus),
			fiscal_year: journalYear || null,
			periods_guid: journalPeriodGuid || null,
		});
		setJournalRows(res.journals || []);
	}, [journalPeriodGuid, journalStatus, journalYear]);

	const loadAll = useCallback(async (): Promise<void> => {
		try {
			await Promise.all([loadNumbers(), loadAccounts(), loadLedgers(), loadPeriodStatus(), loadAllPeriodStatus()]);
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadAccounts, loadAllPeriodStatus, loadLedgers, loadNumbers, loadPeriodStatus]);

	useEffect(() => {
		void loadAll();
	}, [loadAll]);

	useEffect(() => {
		if (tab === 1) {
			void loadImports();
		}
		if (tab === 2) {
			void loadPeriodStatus();
		}
		if (tab === 3) {
			void loadTrialBalance();
		}
		if (tab === 4) {
			void loadJournalSummary();
		}
	}, [tab, loadImports, loadJournalSummary, loadPeriodStatus, loadTrialBalance]);

	const selectedImportRow = useMemo(
		() => imports.find((row) => row.recid === selectedImport) ?? null,
		[imports, selectedImport],
	);

	const currentTaskStepName = promoteTaskStatus?.current_step || null;

	const promoteJournalRecid = useMemo(() => {
		const result = promoteTaskStatus?.result;
		if (!result) {
			return null;
		}
		return result.journal_recid ?? result.journals_recid ?? result.gl_journal_recid ?? result.journal?.recid ?? null;
	}, [promoteTaskStatus]);


	useEffect(() => {
		if (selectedImport === null) {
			setImportDetails([]);
			setLineItems([]);
			return;
		}

		if (detailView === "raw") {
			void loadImportDetails(selectedImport);
			return;
		}

		void loadLineItems(selectedImport);
	}, [detailView, loadImportDetails, loadLineItems, selectedImport]);

	useEffect(() => {
		setDetailView("raw");
		setSelectedLedgerRecid(null);
		setPromotingImport(null);
		setPromoteTaskGuid(null);
		setPromoteTaskStatus(null);
		setPromoteTaskEvents([]);
		setBillingMessage(null);
	}, [selectedImport]);

	useEffect(() => {
		if (tab !== 1) {
			setPromotingImport(null);
			setPromoteTaskGuid(null);
			setPromoteTaskStatus(null);
			setPromoteTaskEvents([]);
			setBillingMessage(null);
		}
	}, [tab]);

	useEffect(() => {
		if (!promoteTaskGuid || selectedImport === null || tab !== 1) {
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
					setBillingMessage({
						severity: "success",
						text: task.result
							? `Promotion completed${(task.result.journal_recid ?? task.result.journals_recid ?? task.result.gl_journal_recid ?? task.result.journal?.recid) ? ` — journal #${task.result.journal_recid ?? task.result.journals_recid ?? task.result.gl_journal_recid ?? task.result.journal?.recid}` : ""}.`
							: "Promotion completed.",
					});
					await loadImports();
					return;
				}
				if (task.status >= 5) {
					window.clearInterval(intervalId);
					setBillingMessage({
						severity: "error",
						text: task.error || "Promotion failed.",
					});
				}
			} catch (e: any) {
				if (!active) {
					return;
				}
				setBillingMessage({
					severity: "error",
					text: e?.message || "Unable to monitor promotion task.",
				});
			}
		};

		void pollTask();
		intervalId = window.setInterval(() => {
			void pollTask();
		}, 4000);

		return () => {
			active = false;
			window.clearInterval(intervalId);
		};
	}, [loadImports, loadTaskEvents, promoteTaskGuid, selectedImport, tab]);

	const trialTotals = useMemo(() => {
		return trialRows.reduce(
			(acc, row) => ({
				debit: acc.debit + Number(row.total_debit || 0),
				credit: acc.credit + Number(row.total_credit || 0),
				net: acc.net + Number(row.net_balance || 0),
			}),
			{ debit: 0, credit: 0, net: 0 },
		);
	}, [trialRows]);

	if (forbidden) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h6">Access denied</Typography>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Accounting Manager</PageTitle>
			<Divider sx={{ mb: 2 }} />
			<Tabs value={tab} onChange={(_, next) => setTab(next)}>
				<Tab label="Number Sequences" />
				<Tab label="Billing Import" />
				<Tab label="Period Management" />
				<Tab label="Trial Balance" />
				<Tab label="Journal Overview" />
			</Tabs>

			{tab === 0 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField label="Prefix" value={numberForm.prefix || ""} onChange={(e) => setNumberForm((prev) => ({ ...prev, prefix: e.target.value }))} />
							<TextField
								select
								label="Account"
								value={numberForm.accounts_guid}
								onChange={(e) => setNumberForm((prev) => ({ ...prev, accounts_guid: e.target.value }))}
								sx={{ minWidth: 300 }}
							>
								<MenuItem value="">Select account</MenuItem>
								{accounts.map((account) => (
									<MenuItem key={account.guid} value={account.guid}>
										{account.guid} | {account.name}
									</MenuItem>
								))}
							</TextField>
							<TextField label="Account Number" value={numberForm.account_number} onChange={(e) => setNumberForm((prev) => ({ ...prev, account_number: e.target.value }))} />
							<TextField type="number" label="Last Number" value={numberForm.last_number} onChange={(e) => setNumberForm((prev) => ({ ...prev, last_number: Number(e.target.value) }))} />
							<TextField type="number" label="Allocation Size" value={numberForm.allocation_size} onChange={(e) => setNumberForm((prev) => ({ ...prev, allocation_size: Number(e.target.value) }))} />
							<TextField label="Reset Policy" value={numberForm.reset_policy} onChange={(e) => setNumberForm((prev) => ({ ...prev, reset_policy: e.target.value }))} />
							<Button variant="contained" onClick={async () => {
								await rpcCall("urn:finance:numbers:upsert:1", numberForm);
								setNumberForm({ recid: null, accounts_guid: "", prefix: "", account_number: "", last_number: 1000, allocation_size: 10, reset_policy: "Never" });
								await loadNumbers();
							}}>Save</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead><TableRow><TableCell>Prefix</TableCell><TableCell>Account Number</TableCell><TableCell>Last Number</TableCell><TableCell>Allocation Size</TableCell><TableCell>Reset Policy</TableCell><TableCell /></TableRow></TableHead>
						<TableBody>
							{numbers.map((item) => (
								<TableRow key={item.recid || `${item.accounts_guid}-${item.account_number}`}>
									<TableCell>{item.prefix || ""}</TableCell>
									<TableCell>{item.account_number}</TableCell>
									<TableCell>{item.last_number}</TableCell>
									<TableCell>{item.allocation_size}</TableCell>
									<TableCell>{item.reset_policy}</TableCell>
									<TableCell>
										<Button onClick={() => setNumberForm(item)}>Edit</Button>
										<Button onClick={async () => { if (!item.recid) return; await rpcCall("urn:finance:numbers:next_number:1", { recid: item.recid }); await loadNumbers(); }}>Get Next</Button>
										<Button color="error" onClick={async () => { if (!item.recid) return; await rpcCall("urn:finance:numbers:delete:1", { recid: item.recid }); await loadNumbers(); }}>Delete</Button>
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
						<Stack spacing={2}>
							<Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
								<TextField
									label="Start Date (YYYY-MM-DD)"
									value={importStartDate}
									onChange={(e) => setImportStartDate(e.target.value)}
								/>
								<TextField
									label="End Date (YYYY-MM-DD)"
									value={importEndDate}
									onChange={(e) => setImportEndDate(e.target.value)}
								/>
								<Button
									variant="contained"
									disabled={importing}
									onClick={async () => {
										setImporting(true);
										setBillingMessage(null);
										try {
											await rpcCall("urn:finance:staging:import:1", {
												period_start: importStartDate,
												period_end: importEndDate,
											});
											setBillingMessage({ severity: "success", text: "Cost detail import started successfully." });
											await loadImports();
										} catch (e: any) {
											setBillingMessage({ severity: "error", text: e?.message || "Cost detail import failed." });
										} finally {
											setImporting(false);
										}
									}}
								>
									{importing ? "Importing..." : "Import"}
								</Button>
							</Stack>
							<Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
								<TextField
									label="Invoice Month (YYYY-MM)"
									value={invoiceMonth}
									onChange={(e) => setInvoiceMonth(e.target.value)}
								/>
								<Button
									variant="contained"
									disabled={importingInvoices}
									onClick={async () => {
										setImportingInvoices(true);
										setBillingMessage(null);
										try {
											const res = await rpcCall<{ message?: string }>("urn:finance:staging:import_invoices:1", {
												period_month: invoiceMonth,
											});
											setBillingMessage({
												severity: "success",
												text: res.message || "Invoice import completed successfully.",
											});
											await loadImports();
										} catch (e: any) {
											setBillingMessage({ severity: "error", text: e?.message || "Invoice import failed." });
										} finally {
											setImportingInvoices(false);
										}
									}}
								>
									{importingInvoices ? "Importing..." : "Import Invoices"}
								</Button>
							</Stack>
						</Stack>
					</Paper>



					{billingMessage && <Alert severity={billingMessage.severity}>{billingMessage.text}</Alert>}

					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>RecId</TableCell>
								<TableCell>Source</TableCell>
								<TableCell>Metric</TableCell>
								<TableCell>Period Start</TableCell>
								<TableCell>Period End</TableCell>
								<TableCell>Rows</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Error</TableCell>
								<TableCell>Created On</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{imports.map((row) => {
								const statusConfig = IMPORT_STATUS_CONFIG[row.element_status];
								return (
									<TableRow
										hover
										key={row.recid}
										selected={selectedImport === row.recid}
										sx={{ cursor: "pointer" }}
										onClick={() => {
											setSelectedImport(row.recid);
										}}
									>
										<TableCell>{row.recid}</TableCell>
										<TableCell>{row.element_source}</TableCell>
										<TableCell>{row.element_metric}</TableCell>
										<TableCell>{row.element_period_start}</TableCell>
										<TableCell>{row.element_period_end}</TableCell>
										<TableCell>{row.element_row_count}</TableCell>
										<TableCell>
											<Chip
												label={statusConfig?.label || row.element_status}
												color={statusConfig?.color || "default"}
												size="small"
											/>
										</TableCell>
										<TableCell>{row.element_error ? `${row.element_error.slice(0, 80)}${row.element_error.length > 80 ? "..." : ""}` : ""}</TableCell>
										<TableCell>{row.element_created_on}</TableCell>
									</TableRow>
								);
							})}
						</TableBody>
					</Table>

					{selectedImportRow && (
						<Paper sx={{ p: 2 }}>
							<Stack spacing={2}>
								<Stack direction={{ xs: "column", md: "row" }} spacing={1} justifyContent="space-between" alignItems={{ xs: "flex-start", md: "center" }}>
									<Box>
										<Typography variant="h6">
											Import #{selectedImportRow.recid} — {selectedImportRow.element_row_count} rows
										</Typography>
										<Typography variant="body2" color="text.secondary">
											{selectedImportRow.element_source} • {selectedImportRow.element_period_start} to {selectedImportRow.element_period_end}
										</Typography>
									</Box>
									<Stack direction="row" spacing={1} flexWrap="wrap">
										{selectedImportRow.element_status === 1 && (
											<Button
												variant="contained"
												color="success"
												onClick={() => {
													setSelectedLedgerRecid(null);
													setConfirmAction({ type: "promote", recid: selectedImportRow.recid });
												}}
											>
												Promote Import
											</Button>
										)}
										{selectedImportRow.element_status !== 3 && (
											<Button variant="outlined" color="error" onClick={() => setConfirmAction({ type: "delete", recid: selectedImportRow.recid })}>
												Delete Import
											</Button>
										)}
									</Stack>
								</Stack>

									{promotingImport === selectedImportRow.recid && promoteTaskStatus && (
										<Paper variant="outlined" sx={{ p: 2 }}>
											<Stack spacing={1.5}>
												<Stack direction="row" spacing={1} alignItems="center">
													{promoteTaskStatus.status === 0 || promoteTaskStatus.status === 1 ? <CircularProgress size={18} /> : null}
													<Typography variant="subtitle2">
														Promotion Task {promoteTaskGuid ? `(${promoteTaskGuid})` : ""}
													</Typography>
												</Stack>
												<Typography variant="body2">
													Step {promoteTaskStatus.step_index || 0} of {PROMOTE_PIPELINE_STEPS.length}: {currentTaskStepName || "Waiting to start"}
												</Typography>
												<LinearProgress
													variant="determinate"
													value={Math.min(100, ((promoteTaskStatus.step_index || 0) / PROMOTE_PIPELINE_STEPS.length) * 100)}
												/>
												{promoteTaskStatus.status === 4 && (
													<Alert severity="success">
														Promotion completed{promoteJournalRecid ? ` — journal #${promoteJournalRecid}` : ""}.
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

								<Tabs value={detailView} onChange={(_, next) => setDetailView(next)} sx={{ borderBottom: 1, borderColor: "divider" }}>
									<Tab value="raw" label="Raw Details" />
									<Tab value="line_items" label="Line Items" />
								</Tabs>

								{detailView === "raw" ? (
									<Table size="small">
										<TableHead>
											<TableRow>
												<TableCell>Date</TableCell>
												<TableCell>Subscription</TableCell>
												<TableCell>Resource Group</TableCell>
												<TableCell>Meter Category</TableCell>
												<TableCell>Quantity</TableCell>
												<TableCell>Cost</TableCell>
												<TableCell>Currency</TableCell>
											</TableRow>
										</TableHead>
										<TableBody>
											{importDetails.slice(0, 50).map((detail, index) => (
												<TableRow key={`${selectedImportRow.recid}-${index}`}>
													<TableCell>{detail.element_Date}</TableCell>
													<TableCell>{detail.element_SubscriptionName}</TableCell>
													<TableCell>{detail.element_ResourceGroup}</TableCell>
													<TableCell>{detail.element_MeterCategory}</TableCell>
													<TableCell>{detail.element_Quantity}</TableCell>
													<TableCell>{detail.element_CostInBillingCurrency}</TableCell>
													<TableCell>{detail.element_BillingCurrency}</TableCell>
												</TableRow>
											))}
										</TableBody>
									</Table>
								) : (
									<Table size="small">
										<TableHead>
											<TableRow>
												<TableCell>Date</TableCell>
												<TableCell>Vendor</TableCell>
												<TableCell>Service</TableCell>
												<TableCell>Category</TableCell>
												<TableCell>Description</TableCell>
												<TableCell>Quantity</TableCell>
												<TableCell>Unit Price</TableCell>
												<TableCell>Amount</TableCell>
												<TableCell>Currency</TableCell>
											</TableRow>
										</TableHead>
										<TableBody>
											{lineItems.map((item) => (
												<TableRow key={item.recid}>
													<TableCell>{item.element_date || "-"}</TableCell>
													<TableCell>{item.vendor_name || "-"}</TableCell>
													<TableCell>{item.element_service || "-"}</TableCell>
													<TableCell>{item.element_category || "-"}</TableCell>
													<TableCell>{item.element_description || "-"}</TableCell>
													<TableCell>{item.element_quantity || "-"}</TableCell>
													<TableCell>{item.element_unit_price || "-"}</TableCell>
													<TableCell>{item.element_amount}</TableCell>
													<TableCell>{item.element_currency || "-"}</TableCell>
												</TableRow>
											))}
										</TableBody>
									</Table>
								)}
							</Stack>
						</Paper>
					)}

					<Dialog open={confirmAction !== null} onClose={() => setConfirmAction(null)}>
						<DialogTitle>{confirmAction?.type === "promote" ? "Promote Import" : "Delete Import"}</DialogTitle>
						<DialogContent>
							<DialogContentText>
								{confirmAction?.type === "promote"
									? `Promote import #${confirmAction?.recid}? This will create a journal entry with the classified costs in the selected ledger.`
									: `Delete import #${confirmAction?.recid}? This will remove all staging data for this import.`}
							</DialogContentText>
							{confirmAction?.type === "promote" && (
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
							)}
						</DialogContent>
						<DialogActions>
							<Button onClick={() => setConfirmAction(null)}>Cancel</Button>
							<Button
								onClick={async () => {
									if (!confirmAction) {
										return;
									}
									setBillingMessage(null);
									try {
										if (confirmAction.type === "promote") {
											const res = await rpcCall<{ task_guid: string }>("urn:finance:staging:promote:1", {
												imports_recid: confirmAction.recid,
												ledgers_recid: selectedLedgerRecid,
											});
											setPromotingImport(confirmAction.recid);
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
											setBillingMessage({ severity: "info", text: `Promotion started for import #${confirmAction.recid}.` });
										} else {
											await rpcCall("urn:finance:staging:delete_import:1", {
												imports_recid: confirmAction.recid,
											});
											setSelectedImport(null);
											setPromotingImport(null);
											setPromoteTaskGuid(null);
											setPromoteTaskStatus(null);
											setPromoteTaskEvents([]);
											setImportDetails([]);
											setLineItems([]);
											setBillingMessage({ severity: "success", text: `Import #${confirmAction.recid} deleted.` });
											await loadImports();
										}
									} catch (e: any) {
										setBillingMessage({
											severity: "error",
											text: e?.message || `Unable to ${confirmAction.type === "promote" ? "promote" : "delete"} import.`,
										});
									} finally {
										setConfirmAction(null);
									}
								}}
								color={confirmAction?.type === "delete" ? "error" : "success"}
								variant="contained"
								disabled={confirmAction?.type === "promote" && selectedLedgerRecid === null}
							>
								{confirmAction?.type === "promote" ? "Promote" : "Delete"}
							</Button>
						</DialogActions>
					</Dialog>
				</Stack>
			)}

			{tab === 2 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField select label="Fiscal Year" value={periodYear} onChange={(e) => setPeriodYear(Number(e.target.value))} sx={{ minWidth: 120 }}>
								{yearOptions.map((year) => (
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
								<TableCell>Period Number</TableCell>
								<TableCell>Start</TableCell>
								<TableCell>End</TableCell>
								<TableCell>Period Type</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Has Closing Week</TableCell>
								<TableCell>Total Journals</TableCell>
								<TableCell>Unposted</TableCell>
								<TableCell>Posted</TableCell>
								<TableCell>Reversed</TableCell>
								<TableCell />
							</TableRow>
						</TableHead>
						<TableBody>
							{periodStatusRows.map((row) => (
								<TableRow key={row.period_guid}>
									<TableCell>{getPeriodDisplayLabel(row)}</TableCell>
									<TableCell>{row.period_number}</TableCell>
									<TableCell>{row.start_date}</TableCell>
									<TableCell>{row.end_date}</TableCell>
									<TableCell>
										<Chip
											label={PERIOD_TYPE_CONFIG[row.close_type]?.label || "Unknown"}
											color={PERIOD_TYPE_CONFIG[row.close_type]?.color || "default"}
											size="small"
										/>
									</TableCell>
									<TableCell>
										<Chip
											label={PERIOD_STATUS_CONFIG[row.period_status]?.label || "Unknown"}
											color={PERIOD_STATUS_CONFIG[row.period_status]?.color || "default"}
											size="small"
										/>
									</TableCell>
									<TableCell>{row.has_closing_week ? "Yes" : "No"}</TableCell>
									<TableCell>{row.total_journals}</TableCell>
									<TableCell>
										<Chip
											label={row.unposted_journals}
											color={row.unposted_journals > 0 ? "warning" : "default"}
											size="small"
										/>
									</TableCell>
									<TableCell>{row.posted_journals}</TableCell>
									<TableCell>{row.reversed_journals}</TableCell>
									<TableCell>
										<Button
											size="small"
											onClick={async () => {
												const nextStatus = row.period_status === 1 ? 2 : 1;
												const message = nextStatus === 1
													? `Reopen period ${row.period_name}? This will allow new journal postings.`
													: `Close period ${row.period_name}? This will prevent new journal postings.`;
												if (!window.confirm(message)) {
													return;
												}
												const existingPeriod = await rpcCall<{
													guid: string | null;
													year: number;
													period_number: number;
													period_name: string;
													start_date: string;
													end_date: string;
													days_in_period: number | null;
													quarter_number: number | null;
													has_closing_week: boolean;
													is_leap_adjustment: boolean;
													anchor_event: string | null;
													close_type: number;
													status: number;
													numbers_recid: number | null;
													element_display_format: string | null;
												}>("urn:finance:periods:get:1", {
													guid: row.period_guid,
												});
												await rpcCall("urn:finance:periods:upsert:1", {
													...existingPeriod,
													status: nextStatus,
												});
												await loadPeriodStatus();
										}}
										>
											{row.period_status === 1 ? "Close Period" : "Reopen Period"}
										</Button>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 3 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField select label="Fiscal Year" value={trialYear} onChange={(e) => setTrialYear(Number(e.target.value))} sx={{ minWidth: 120 }}>
								{yearOptions.map((year) => (
									<MenuItem key={year} value={year}>{year}</MenuItem>
								))}
							</TextField>
							<TextField select label="Period" value={trialPeriodGuid} onChange={(e) => setTrialPeriodGuid(e.target.value)} sx={{ minWidth: 200 }}>
								<MenuItem value="">All</MenuItem>
								{periodsForTrialYear.map((period) => (
									<MenuItem key={period.period_guid} value={period.period_guid}>{getPeriodDisplayLabel(period)}</MenuItem>
								))}
							</TextField>
							<Button variant="outlined" onClick={() => void loadTrialBalance()}>Refresh</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Account Number</TableCell>
								<TableCell>Account Name</TableCell>
								<TableCell>Account Type</TableCell>
								<TableCell>Total Debit</TableCell>
								<TableCell>Total Credit</TableCell>
								<TableCell>Net Balance</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{trialRows.map((row) => (
								<TableRow key={`${row.period_guid}-${row.account_guid}`}>
									<TableCell>{row.account_number}</TableCell>
									<TableCell>{row.account_name}</TableCell>
									<TableCell>{ACCOUNT_TYPES.find((a) => a.value === row.account_type)?.label || row.account_type}</TableCell>
									<TableCell>{Number(row.total_debit).toFixed(2)}</TableCell>
									<TableCell>{Number(row.total_credit).toFixed(2)}</TableCell>
									<TableCell sx={{ color: Number(row.net_balance) < 0 ? "error.main" : undefined }}>{Number(row.net_balance).toFixed(2)}</TableCell>
								</TableRow>
							))}
							<TableRow>
								<TableCell colSpan={3}><strong>Totals</strong></TableCell>
								<TableCell><strong>{trialTotals.debit.toFixed(2)}</strong></TableCell>
								<TableCell><strong>{trialTotals.credit.toFixed(2)}</strong></TableCell>
								<TableCell sx={{ color: trialTotals.net < 0 ? "error.main" : undefined }}><strong>{trialTotals.net.toFixed(2)}</strong></TableCell>
							</TableRow>
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 4 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField select label="Fiscal Year" value={journalYear} onChange={(e) => setJournalYear(Number(e.target.value))} sx={{ minWidth: 120 }}>
								{yearOptions.map((year) => (
									<MenuItem key={year} value={year}>{year}</MenuItem>
								))}
							</TextField>
							<TextField select label="Period" value={journalPeriodGuid} onChange={(e) => setJournalPeriodGuid(e.target.value)} sx={{ minWidth: 200 }}>
								<MenuItem value="">All</MenuItem>
								{periodsForJournalYear.map((period) => (
									<MenuItem key={period.period_guid} value={period.period_guid}>{getPeriodDisplayLabel(period)}</MenuItem>
								))}
							</TextField>
							<TextField select label="Status" value={journalStatus} onChange={(e) => setJournalStatus(e.target.value)} sx={{ minWidth: 140 }}>
								<MenuItem value="">All</MenuItem>
								<MenuItem value="0">Unposted</MenuItem>
								<MenuItem value="1">Posted</MenuItem>
								<MenuItem value="2">Reversed</MenuItem>
							</TextField>
							<Button variant="outlined" onClick={() => void loadJournalSummary()}>Refresh</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Posting Key</TableCell>
								<TableCell>Name</TableCell>
								<TableCell>Description</TableCell>
								<TableCell>Source Type</TableCell>
								<TableCell>Period</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Lines</TableCell>
								<TableCell>Total Debit</TableCell>
								<TableCell>Total Credit</TableCell>
								<TableCell>Posted By</TableCell>
								<TableCell>Posted On</TableCell>
								<TableCell>Created</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{journalRows.map((row) => (
								<TableRow key={row.recid}>
									<TableCell>{row.posting_key || "-"}</TableCell>
									<TableCell>{row.journal_name}</TableCell>
									<TableCell>{row.journal_description || "-"}</TableCell>
									<TableCell>{row.source_type || "-"}</TableCell>
									<TableCell>{row.period_name || "-"}</TableCell>
									<TableCell>
										<Chip
											label={row.journal_status === 1 ? "Posted" : row.journal_status === 2 ? "Reversed" : "Unposted"}
											color={row.journal_status === 1 ? "success" : row.journal_status === 2 ? "error" : "warning"}
											size="small"
										/>
									</TableCell>
									<TableCell>{row.line_count}</TableCell>
									<TableCell>{Number(row.total_debit).toFixed(2)}</TableCell>
									<TableCell>{Number(row.total_credit).toFixed(2)}</TableCell>
									<TableCell>{row.posted_by || "-"}</TableCell>
									<TableCell>{row.posted_on || "-"}</TableCell>
									<TableCell>{row.created_on}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}
		</Box>
	);
};

export default FinanceManagerPage;
