import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Box,
	Button,
	Chip,
	Dialog,
	DialogActions,
	DialogContent,
	DialogTitle,
	Divider,
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
	StagingImportItem1,
	StagingImportList1,
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

	const [importStartDate, setImportStartDate] = useState("");
	const [importEndDate, setImportEndDate] = useState("");
	const [importing, setImporting] = useState(false);
	const [imports, setImports] = useState<StagingImportItem1[]>([]);
	const [selectedImport, setSelectedImport] = useState<number | null>(null);
	const [importDetails, setImportDetails] = useState<Record<string, any>[]>([]);

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

	const loadShared = useCallback(async (): Promise<void> => {
		const [periodRes, accountRes] = await Promise.all([
			rpcCall<FinancePeriodsList1>("urn:finance:periods:list:1"),
			rpcCall<FinanceAccountsList1>("urn:finance:accounts:list:1"),
		]);
		setPeriods(periodRes.periods || []);
		setAccounts(accountRes.accounts || []);
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
		const res = await rpcCall<StagingImportList1>("urn:finance:staging:list_imports:1");
		setImports(res.imports || []);
	}, []);

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
		}
	}, [tab, loadImports, loadJournals, loadLots, loadPeriodStatus]);

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
							>
								<MenuItem value="">All</MenuItem>
								{periodsForSelectedYear.map((period) => (
									<MenuItem key={`${period.guid || period.period_number}`} value={period.guid || ""}>
										{`FY${period.year} - ${period.period_name}`}
									</MenuItem>
								))}
							</TextField>
							<TextField
								select
								label="Status"
								value={journalStatus}
								onChange={(e) => setJournalStatus(e.target.value)}
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
										const linesRes = await fetchLines({ journals_recid: row.recid }) as JournalLineList1;
										setJournalLines(linesRes.lines || []);
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
											size="small"
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
										{row.journal_status === 1 && (
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
										<Chip label={row.expired ? "Expired" : "Active"} color={row.expired ? "error" : "success"} size="small" />
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
										<Chip label={row.close_type === 0 ? "Open" : "Closed"} color={row.close_type === 0 ? "success" : "error"} size="small" />
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
					<Paper sx={{ p: 2 }}>
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
									try {
										await rpcCall("urn:finance:staging:import:1", {
											period_start: importStartDate,
											period_end: importEndDate,
										});
										await loadImports();
									} finally {
										setImporting(false);
									}
								}}
							>
								{importing ? "Importing..." : "Import"}
							</Button>
						</Stack>
					</Paper>

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
							{imports.map((row) => (
								<TableRow
									hover
									key={row.recid}
									selected={selectedImport === row.recid}
									sx={{ cursor: "pointer" }}
									onClick={async () => {
										setSelectedImport(row.recid);
										const details = await rpcCall<Record<string, any>[]>("urn:finance:staging:list_details:1", {
											imports_recid: row.recid,
										});
										setImportDetails(details || []);
									}}
								>
									<TableCell>{row.recid}</TableCell>
									<TableCell>{row.element_source}</TableCell>
									<TableCell>{row.element_metric}</TableCell>
									<TableCell>{row.element_period_start}</TableCell>
									<TableCell>{row.element_period_end}</TableCell>
									<TableCell>{row.element_row_count}</TableCell>
									<TableCell>{row.element_status === 0 ? "Pending" : row.element_status === 1 ? "Completed" : row.element_status === 2 ? "Failed" : row.element_status}</TableCell>
									<TableCell>{row.element_error ? `${String(row.element_error).slice(0, 80)}${String(row.element_error).length > 80 ? "..." : ""}` : ""}</TableCell>
									<TableCell>{String(row.element_created_on || "")}</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>

					{selectedImport !== null && (
						<Stack spacing={1}>
							<Typography variant="h6">
								Import #{selectedImport} — {imports.find((row) => row.recid === selectedImport)?.element_row_count || 0} rows
							</Typography>
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
										<TableRow key={`${selectedImport}-${index}`}>
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
						</Stack>
					)}
				</Stack>
			)}

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
									<MenuItem key={`${period.guid || period.period_number}`} value={period.guid || ""}>{`FY${period.year} - ${period.period_name}`}</MenuItem>
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
		</Box>
	);
};

export default FinanceAccountantPage;
