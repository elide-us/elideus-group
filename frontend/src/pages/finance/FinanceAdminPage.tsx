import { useCallback, useEffect, useState } from "react";
import {
	Box,
	Button,
	Checkbox,
	Chip,
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
	numbers_recid: number | null;
	element_display_format: string | null;
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

type FinanceDimension = {
	recid?: number | null;
	name: string;
	value: string;
	description?: string | null;
	status: number;
};

type FinanceVendor = {
	recid?: number | null;
	element_name: string;
	element_display?: string | null;
	element_description?: string | null;
	element_status: number;
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

	const [dimensions, setDimensions] = useState<FinanceDimension[]>([]);
	const [dimensionForm, setDimensionForm] = useState<FinanceDimension>({
		recid: null,
		name: "",
		value: "",
		description: "",
		status: 1,
	});

	const [vendors, setVendors] = useState<FinanceVendor[]>([]);
	const [vendorForm, setVendorForm] = useState<FinanceVendor>({
		recid: null,
		element_name: "",
		element_display: "",
		element_description: "",
		element_status: 1,
	});

	const loadPeriods = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ periods: FinancePeriod[] }>("urn:finance:periods:list:1");
		setPeriods(res.periods || []);
	}, []);

	const loadAccounts = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ accounts: FinanceAccount[] }>("urn:finance:accounts:list:1");
		setAccounts(res.accounts || []);
	}, []);

	const loadDimensions = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ dimensions: FinanceDimension[] }>("urn:finance:dimensions:list:1");
		setDimensions(res.dimensions || []);
	}, []);

	const loadVendors = useCallback(async (): Promise<void> => {
		const res = await rpcCall<{ vendors: FinanceVendor[] }>("urn:finance:vendors:list:1");
		setVendors(res.vendors || []);
	}, []);

	const loadAll = useCallback(async (): Promise<void> => {
		try {
			await Promise.all([loadPeriods(), loadAccounts(), loadDimensions(), loadVendors()]);
			setForbidden(false);
		} catch (e: any) {
			if (e?.response?.status === 403) {
				setForbidden(true);
				return;
			}
			throw e;
		}
	}, [loadPeriods, loadAccounts, loadDimensions, loadVendors]);

	useEffect(() => {
		void loadAll();
	}, [loadAll]);

	if (forbidden) {
		return (
			<Box sx={{ p: 2 }}>
				<Typography variant="h6">Access denied</Typography>
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
				<Tab label="Financial Dimensions" />
				<Tab label="Vendors" />
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
							</TableRow>
						</TableHead>
						<TableBody>
							{periods.map((item) => (
								<TableRow key={item.guid || `${item.year}-${item.period_number}`}>
									<TableCell>
										{item.element_display_format
											? `${item.element_display_format}-${item.period_name}`
											: item.period_name}
									</TableCell>
									<TableCell>{item.quarter_number}</TableCell>
									<TableCell>{item.start_date}</TableCell>
									<TableCell>{item.end_date}</TableCell>
									<TableCell>{item.days_in_period}</TableCell>
									<TableCell>{item.has_closing_week ? "Yes" : "No"}</TableCell>
									<TableCell>{item.status}</TableCell>
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

			{tab === 3 && (
				<Stack spacing={2} sx={{ mt: 2 }}>
					<Paper sx={{ p: 2 }}>
						<Stack direction="row" spacing={1} flexWrap="wrap">
							<TextField label="Name" value={vendorForm.element_name} onChange={(e) => setVendorForm((prev) => ({ ...prev, element_name: e.target.value }))} />
							<TextField label="Display" value={vendorForm.element_display || ""} onChange={(e) => setVendorForm((prev) => ({ ...prev, element_display: e.target.value }))} />
							<TextField label="Description" value={vendorForm.element_description || ""} onChange={(e) => setVendorForm((prev) => ({ ...prev, element_description: e.target.value }))} />
							<FormControlLabel label="Active" control={<Checkbox checked={vendorForm.element_status === 1} onChange={(e) => setVendorForm((prev) => ({ ...prev, element_status: e.target.checked ? 1 : 0 }))} />} />
							<Button variant="contained" onClick={async () => {
								await rpcCall("urn:finance:vendors:upsert:1", vendorForm);
								setVendorForm({ recid: null, element_name: "", element_display: "", element_description: "", element_status: 1 });
								await loadVendors();
							}}>{vendorForm.recid ? "Update" : "Create"}</Button>
						</Stack>
					</Paper>
					<Table size="small">
						<TableHead><TableRow><TableCell>Name</TableCell><TableCell>Display</TableCell><TableCell>Description</TableCell><TableCell>Status</TableCell><TableCell /></TableRow></TableHead>
						<TableBody>
							{vendors.map((item) => (
								<TableRow key={item.recid || item.element_name}>
									<TableCell>{item.element_name}</TableCell>
									<TableCell>{item.element_display || ""}</TableCell>
									<TableCell>{item.element_description || ""}</TableCell>
									<TableCell><Chip size="small" color={item.element_status === 1 ? "success" : "default"} label={item.element_status === 1 ? "Active" : "Disabled"} /></TableCell>
									<TableCell>
										<Button onClick={() => setVendorForm(item)}>Edit</Button>
										<Button color="error" onClick={async () => {
											if (!item.recid || !window.confirm(`Delete vendor ${item.element_name}?`)) return;
											await rpcCall("urn:finance:vendors:delete:1", { recid: item.recid });
											await loadVendors();
										}}>Delete</Button>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				</Stack>
			)}

		</Box>
	);
};

export default FinanceAdminPage;
