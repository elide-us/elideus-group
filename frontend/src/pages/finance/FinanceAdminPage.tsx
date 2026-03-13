import { useCallback, useEffect, useState } from "react";
import {
	Box,
	Button,
	Checkbox,
	Divider,
	FormControlLabel,
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

type FinancePeriod = {
	guid?: string | null;
	year: number;
	period_number: number;
	period_name: string;
	start_date: string;
	end_date: string;
	days_in_period: number;
	quarter_number: number;
	has_closing_week: boolean;
	status: number;
	is_leap_adjustment: boolean;
};

type FinanceAccount = {
	guid?: string | null;
	number: string;
	name: string;
	account_type: number;
	parent?: string | null;
	is_posting: boolean;
	status: number;
};

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

type FinanceDimension = {
	recid?: number | null;
	name: string;
	value: string;
	description?: string | null;
	status: number;
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

const ACCOUNT_TYPES: { value: number; label: string }[] = [
	{ value: 0, label: "Asset" },
	{ value: 1, label: "Liability" },
	{ value: 2, label: "Equity" },
	{ value: 3, label: "Revenue" },
	{ value: 4, label: "Expense" },
];

const FinanceAdminPage = (): JSX.Element => {
	const [tab, setTab] = useState(0);
	const [forbidden, setForbidden] = useState(false);

	const [periods, setPeriods] = useState<FinancePeriod[]>([]);
	const [fiscalYear, setFiscalYear] = useState<number>(new Date().getFullYear());
	const [fiscalStartDate, setFiscalStartDate] = useState<string>("");

	const [accounts, setAccounts] = useState<FinanceAccount[]>([]);
	const [newAccount, setNewAccount] = useState<FinanceAccount>({
		number: "",
		name: "",
		account_type: 0,
		parent: null,
		is_posting: true,
		status: 1,
	});

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

	const [dimensions, setDimensions] = useState<FinanceDimension[]>([]);
	const [dimensionForm, setDimensionForm] = useState<FinanceDimension>({
		recid: null,
		name: "",
		value: "",
		description: "",
		status: 1,
	});
	const [importStartDate, setImportStartDate] = useState("");
	const [importEndDate, setImportEndDate] = useState("");
	const [importing, setImporting] = useState(false);
	const [imports, setImports] = useState<StagingImport[]>([]);
	const [selectedImport, setSelectedImport] = useState<number | null>(null);
	const [importDetails, setImportDetails] = useState<Record<string, any>[]>([]);

	const loadPeriods = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ periods: FinancePeriod[] }>("urn:finance:periods:list:1");
		setPeriods(res.periods || []);
	}, []);

	const loadAccounts = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ accounts: FinanceAccount[] }>("urn:finance:accounts:list:1");
		setAccounts(res.accounts || []);
	}, []);

	const loadNumbers = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ numbers: FinanceNumber[] }>("urn:finance:numbers:list:1");
		setNumbers(res.numbers || []);
	}, []);

	const loadDimensions = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ dimensions: FinanceDimension[] }>("urn:finance:dimensions:list:1");
		setDimensions(res.dimensions || []);
	}, []);

	const loadImports = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ imports: StagingImport[] }>("urn:finance:staging:list_imports:1");
		setImports(res.imports || []);
	}, []);

	const loadAll = useCallback(async (): Promise<void> => {
		try {
			await Promise.all([loadPeriods(), loadAccounts(), loadNumbers(), loadDimensions()]);
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadPeriods, loadAccounts, loadNumbers, loadDimensions]);

	useEffect(() => {
		void loadAll();
	}, [loadAll]);

	useEffect(() => {
		if (tab !== 4) {
			return;
		}
		void loadImports();
	}, [tab, loadImports]);

	if (forbidden) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h6">Forbidden</Typography>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Finance Admin</PageTitle>
			<Divider sx={{ mb: 2 }} />
			<Tabs value={tab} onChange={(_, next) => setTab(next)}>
				<Tab label="Fiscal Periods" />
				<Tab label="Chart of Accounts" />
				<Tab label="Number Sequences" />
				<Tab label="Financial Dimensions" />
				<Tab label="Billing Import" />
			</Tabs>

			{tab === 0 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} alignItems="center">
							<TextField
								type="number"
								label="Fiscal Year"
								value={fiscalYear}
								onChange={(e) => setFiscalYear(Number(e.target.value))}
							/>
							<TextField
								label="Start Date (YYYY-MM-DD)"
								value={fiscalStartDate}
								onChange={(e) => setFiscalStartDate(e.target.value)}
							/>
							<Button
								variant="contained"
								onClick={async () => {
									await rpcCall("urn:finance:periods:generate_calendar:1", {
										fiscal_year: fiscalYear,
										start_date: fiscalStartDate,
									});
									await loadPeriods();
								}}
							>
								Generate
							</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead>
							<TableRow>
								<TableCell>Period Name</TableCell>
								<TableCell>Quarter</TableCell>
								<TableCell>Start</TableCell>
								<TableCell>End</TableCell>
								<TableCell>Days</TableCell>
								<TableCell>Close</TableCell>
								<TableCell>Status</TableCell>
								<TableCell>Leap</TableCell>
							</TableRow>
						</TableHead>
						<TableBody>
							{periods.map((item) => (
								<TableRow key={item.guid || `${item.year}-${item.period_number}`}>
									<TableCell>{item.period_name}</TableCell>
									<TableCell>{item.quarter_number}</TableCell>
									<TableCell>{item.start_date}</TableCell>
									<TableCell>{item.end_date}</TableCell>
									<TableCell>{item.days_in_period}</TableCell>
									<TableCell>{item.has_closing_week ? "Yes" : "No"}</TableCell>
									<TableCell>{item.status}</TableCell>
									<TableCell>{item.is_leap_adjustment ? "Yes" : "No"}</TableCell>
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
								label="Number"
								value={newAccount.number}
								onChange={(e) => setNewAccount((prev) => ({ ...prev, number: e.target.value }))}
							/>
							<TextField
								label="Name"
								value={newAccount.name}
								onChange={(e) => setNewAccount((prev) => ({ ...prev, name: e.target.value }))}
							/>
							<TextField
								select
								label="Type"
								value={newAccount.account_type}
								onChange={(e) => setNewAccount((prev) => ({ ...prev, account_type: Number(e.target.value) }))}
							>
								{ACCOUNT_TYPES.map((option) => (
									<MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
								))}
							</TextField>
							<TextField
								select
								label="Parent"
								value={newAccount.parent || ""}
								onChange={(e) => setNewAccount((prev) => ({ ...prev, parent: e.target.value || null }))}
							>
								<MenuItem value="">None</MenuItem>
								{accounts.map((account) => (
									<MenuItem key={account.guid} value={account.guid || ""}>{account.number} - {account.name}</MenuItem>
								))}
							</TextField>
							<FormControlLabel
								label="Posting"
								control={
									<Checkbox
										checked={newAccount.is_posting}
										onChange={(e) => setNewAccount((prev) => ({ ...prev, is_posting: e.target.checked }))}
									/>
								}
							/>
							<Button
								variant="contained"
								onClick={async () => {
									await rpcCall("urn:finance:accounts:upsert:1", newAccount);
									setNewAccount({ number: "", name: "", account_type: 0, parent: null, is_posting: true, status: 1 });
									await loadAccounts();
								}}
							>
								Add
							</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead><TableRow><TableCell>Number</TableCell><TableCell>Name</TableCell><TableCell>Type</TableCell><TableCell>Parent</TableCell><TableCell>Posting</TableCell><TableCell>Status</TableCell><TableCell /></TableRow></TableHead>
						<TableBody>
							{accounts.map((item) => (
								<TableRow key={item.guid || item.number}>
									<TableCell>{item.number}</TableCell>
									<TableCell>{item.name}</TableCell>
									<TableCell>{ACCOUNT_TYPES.find((a) => a.value === item.account_type)?.label || item.account_type}</TableCell>
									<TableCell>{item.parent || "-"}</TableCell>
									<TableCell>{item.is_posting ? "Yes" : "No"}</TableCell>
									<TableCell>{item.status}</TableCell>
									<TableCell>
										<Button color="error" onClick={async () => {
											if (!item.guid) return;
											await rpcCall("urn:finance:accounts:delete:1", { guid: item.guid });
											await loadAccounts();
										}}>Delete</Button>
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

			{tab === 3 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField label="Name" value={dimensionForm.name} onChange={(e) => setDimensionForm((prev) => ({ ...prev, name: e.target.value }))} />
							<TextField label="Value" value={dimensionForm.value} onChange={(e) => setDimensionForm((prev) => ({ ...prev, value: e.target.value }))} />
							<TextField label="Description" value={dimensionForm.description || ""} onChange={(e) => setDimensionForm((prev) => ({ ...prev, description: e.target.value }))} />
							<TextField type="number" label="Status" value={dimensionForm.status} onChange={(e) => setDimensionForm((prev) => ({ ...prev, status: Number(e.target.value) }))} />
							<Button variant="contained" onClick={async () => {
								await rpcCall("urn:finance:dimensions:upsert:1", dimensionForm);
								setDimensionForm({ recid: null, name: "", value: "", description: "", status: 1 });
								await loadDimensions();
							}}>Save</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead><TableRow><TableCell>Name</TableCell><TableCell>Value</TableCell><TableCell>Description</TableCell><TableCell>Status</TableCell><TableCell /></TableRow></TableHead>
						<TableBody>
							{dimensions.map((item) => (
								<TableRow key={item.recid || `${item.name}:${item.value}`}>
									<TableCell>{item.name}</TableCell>
									<TableCell>{item.value}</TableCell>
									<TableCell>{item.description || ""}</TableCell>
									<TableCell>{item.status}</TableCell>
									<TableCell>
										<Button onClick={() => setDimensionForm(item)}>Edit</Button>
										<Button color="error" onClick={async () => { if (!item.recid) return; await rpcCall("urn:finance:dimensions:delete:1", { recid: item.recid }); await loadDimensions(); }}>Delete</Button>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

			{tab === 4 && (
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
		</Box>
	);
};

export default FinanceAdminPage;
