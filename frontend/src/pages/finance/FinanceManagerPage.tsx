import { useCallback, useEffect, useMemo, useState } from "react";
import {
	Box,
	Button,
	Chip,
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

const ACCOUNT_TYPES: { value: number; label: string }[] = [
	{ value: 0, label: "Asset" },
	{ value: 1, label: "Liability" },
	{ value: 2, label: "Equity" },
	{ value: 3, label: "Revenue" },
	{ value: 4, label: "Expense" },
];

const getPeriodDisplayLabel = (row: { fiscal_year: number; period_name: string }): string => {
	return `FY${row.fiscal_year} - ${row.period_name}`;
};

const FinanceManagerPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [numbers, setNumbers] = useState<FinanceNumber[]>([]);
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
	const [importing, setImporting] = useState(false);
	const [imports, setImports] = useState<StagingImport[]>([]);
	const [selectedImport, setSelectedImport] = useState<number | null>(null);
	const [importDetails, setImportDetails] = useState<Record<string, any>[]>([]);

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

	const loadImports = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ imports: StagingImport[] }>("urn:finance:staging:list_imports:1");
		setImports(res.imports || []);
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
			await Promise.all([loadNumbers(), loadPeriodStatus(), loadAllPeriodStatus()]);
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadAllPeriodStatus, loadNumbers, loadPeriodStatus]);

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
							<TextField label="Account GUID" value={numberForm.accounts_guid} onChange={(e) => setNumberForm((prev) => ({ ...prev, accounts_guid: e.target.value }))} />
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
									<TableCell>{row.element_error ? `${row.element_error.slice(0, 80)}${row.element_error.length > 80 ? "..." : ""}` : ""}</TableCell>
									<TableCell>{row.element_created_on}</TableCell>
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
								<TableCell>Close Type</TableCell>
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
										<Chip label={row.close_type === 1 ? "Closed" : "Open"} color={row.close_type === 1 ? "error" : "success"} size="small" />
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
														const message = row.close_type === 1
													? `Reopen period ${row.period_name}? This will allow new journal postings.`
													: `Close period ${row.period_name}? This will prevent new journal postings.`;
												if (!window.confirm(message)) {
													return;
												}
												await rpcCall("urn:finance:periods:upsert:1", {
													guid: row.period_guid,
													year: row.fiscal_year,
													period_number: row.period_number,
													period_name: row.period_name,
													start_date: row.start_date,
													end_date: row.end_date,
													has_closing_week: row.has_closing_week,
													close_type: row.close_type === 1 ? 0 : 1,
												});
												await loadPeriodStatus();
										}}
										>
											{row.close_type === 1 ? "Reopen Period" : "Close Period"}
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
