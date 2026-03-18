import { useCallback, useEffect, useMemo, useState } from "react";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import AddIcon from "@mui/icons-material/Add";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Alert,
    Box,
    Button,
    Chip,
    Collapse,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    FormControl,
    FormControlLabel,
    IconButton,
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
    Typography,
    Checkbox,
} from "@mui/material";
import PageTitle from "../../components/PageTitle";
import {
    fetchDelete as fetchDeleteAccount,
    fetchList as fetchAccounts,
    fetchUpsert as fetchUpsertAccount,
} from "../../rpc/finance/accounts/index";
import {
    fetchDelete as fetchDeleteDimension,
    fetchList as fetchDimensions,
    fetchUpsert as fetchUpsertDimension,
} from "../../rpc/finance/dimensions/index";
import {
    fetchCreate as fetchCreateLedger,
    fetchDelete as fetchDeleteLedger,
    fetchList as fetchLedgers,
    fetchUpdate as fetchUpdateLedger,
} from "../../rpc/finance/ledgers/index";
import {
    fetchGenerateCalendar,
    fetchList as fetchPeriods,
    fetchUpsert as fetchUpsertPeriod,
} from "../../rpc/finance/periods/index";
import { fetchPeriodStatus } from "../../rpc/finance/reporting/index";
import {
    fetchDelete as fetchDeleteVendor,
    fetchList as fetchVendors,
    fetchUpsert as fetchUpsertVendor,
} from "../../rpc/finance/vendors/index";

type FinanceLedger = {
    recid: number;
    element_name: string;
    element_description: string | null;
    element_chart_of_accounts_guid: string | null;
    element_status: number;
    element_created_on: string | null;
    element_modified_on: string | null;
};

type LedgerFormState = {
    recid: number | null;
    element_name: string;
    element_description: string;
    element_chart_of_accounts_guid: string;
    element_status: number;
};

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
    is_leap_adjustment: boolean;
    anchor_event: string | null;
    close_type: number;
    status: number;
    numbers_recid: number | null;
    element_display_format: string | null;
};

type PeriodStatusRow = {
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
    recid: number | null;
    element_name: string;
    element_display: string | null;
    element_description: string | null;
    element_status: number;
};

type PeriodSummary = {
    open: number;
    closed: number;
    locked: number;
};

const ACCOUNT_TYPES: { value: number; label: string }[] = [
    { value: 0, label: "Asset" },
    { value: 1, label: "Liability" },
    { value: 2, label: "Equity" },
    { value: 3, label: "Revenue" },
    { value: 4, label: "Expense" },
];

const PERIOD_STATUS_OPTIONS = [
    { value: 1, label: "Open" },
    { value: 2, label: "Closed" },
    { value: 3, label: "Locked" },
] as const;

const LEDGER_STATUS_OPTIONS = [
    { value: 1, label: "Active" },
    { value: 0, label: "Inactive" },
] as const;

const emptyLedgerForm: LedgerFormState = {
    recid: null,
    element_name: "",
    element_description: "",
    element_chart_of_accounts_guid: "",
    element_status: 1,
};

const getErrorMessage = (error: unknown): string => {
    if (typeof error === "object" && error !== null) {
        const response = Reflect.get(error, "response");
        if (typeof response === "object" && response !== null) {
            const data = Reflect.get(response, "data");
            if (typeof data === "object" && data !== null) {
                const detail = Reflect.get(data, "detail");
                if (typeof detail === "string" && detail.trim()) {
                    return detail;
                }
            }
        }
        const message = Reflect.get(error, "message");
        if (typeof message === "string" && message.trim()) {
            return message;
        }
    }
    return "Something went wrong.";
};

const formatDate = (value: string | null | undefined): string => {
    if (!value) {
        return "—";
    }
    return value.slice(0, 10);
};

const formatDateTime = (value: string | null | undefined): string => {
    if (!value) {
        return "—";
    }
    return new Date(value).toLocaleString();
};

const getPeriodStatusLabel = (status: number): string => {
    return PERIOD_STATUS_OPTIONS.find((option) => option.value === status)?.label || `Status ${status}`;
};

const getLedgerStatusLabel = (status: number): string => {
    return LEDGER_STATUS_OPTIONS.find((option) => option.value === status)?.label || `Status ${status}`;
};

const getStatusChipColor = (status: number): "success" | "warning" | "error" | "default" => {
    if (status === 1) {
        return "success";
    }
    if (status === 2) {
        return "warning";
    }
    if (status === 3) {
        return "error";
    }
    return "default";
};

const FinanceAdminPage = (): JSX.Element => {
    const [tab, setTab] = useState(0);
    const [forbidden, setForbidden] = useState(false);
    const [pageError, setPageError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [isBusy, setIsBusy] = useState(false);

    const [ledgers, setLedgers] = useState<FinanceLedger[]>([]);
    const [ledgerDialogOpen, setLedgerDialogOpen] = useState(false);
    const [ledgerForm, setLedgerForm] = useState<LedgerFormState>(emptyLedgerForm);

    const [periods, setPeriods] = useState<FinancePeriod[]>([]);
    const [periodStatuses, setPeriodStatuses] = useState<PeriodStatusRow[]>([]);
    const [fiscalYear, setFiscalYear] = useState<number>(new Date().getFullYear());

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

    const [vendorList, setVendorList] = useState<FinanceVendor[]>([]);
    const [vendorFormOpen, setVendorFormOpen] = useState(false);
    const [vendorForm, setVendorForm] = useState({
        recid: null as number | null,
        element_name: "",
        element_display: "",
        element_description: "",
        element_status: true,
    });

    const loadLedgers = useCallback(async (): Promise<void> => {
        const response = await fetchLedgers();
        setLedgers((response.ledgers || []) as FinanceLedger[]);
    }, []);

    const loadPeriods = useCallback(async (): Promise<void> => {
        const response = await fetchPeriods();
        setPeriods((response.periods || []) as FinancePeriod[]);
    }, []);

    const loadPeriodStatuses = useCallback(async (): Promise<void> => {
        const response = await fetchPeriodStatus();
        setPeriodStatuses((response.periods || []) as PeriodStatusRow[]);
    }, []);

    const loadAccounts = useCallback(async (): Promise<void> => {
        const response = await fetchAccounts();
        setAccounts((response.accounts || []) as FinanceAccount[]);
    }, []);

    const loadDimensions = useCallback(async (): Promise<void> => {
        const response = await fetchDimensions();
        setDimensions((response.dimensions || []) as FinanceDimension[]);
    }, []);

    const loadVendors = useCallback(async (): Promise<void> => {
        const response = await fetchVendors();
        setVendorList((response.vendors || []) as FinanceVendor[]);
    }, []);

    const loadAll = useCallback(async (): Promise<void> => {
        try {
            setPageError(null);
            await Promise.all([
                loadLedgers(),
                loadPeriods(),
                loadPeriodStatuses(),
                loadAccounts(),
                loadDimensions(),
            ]);
            setForbidden(false);
        } catch (error: unknown) {
            const response = typeof error === "object" && error !== null ? Reflect.get(error, "response") : null;
            const status = typeof response === "object" && response !== null ? Reflect.get(response, "status") : null;
            if (status === 403) {
                setForbidden(true);
                return;
            }
            setPageError(getErrorMessage(error));
        }
    }, [loadAccounts, loadDimensions, loadLedgers, loadPeriods, loadPeriodStatuses]);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    useEffect(() => {
        if (tab === 4) {
            void loadVendors();
        }
    }, [loadVendors, tab]);

    const periodYears = useMemo(() => {
        const years = new Set<number>();
        periods.forEach((period) => years.add(period.year));
        periodStatuses.forEach((row) => years.add(row.fiscal_year));
        years.add(fiscalYear);
        return Array.from(years).sort((left, right) => right - left);
    }, [fiscalYear, periods, periodStatuses]);

    const groupedPeriods = useMemo(() => {
        return periodYears.map((year) => ({
            year,
            periods: periods
                .filter((period) => period.year === year)
                .sort((left, right) => left.period_number - right.period_number),
        }));
    }, [periodYears, periods]);

    const periodSummaryByYear = useMemo(() => {
        return periodStatuses.reduce<Record<number, PeriodSummary>>((summary, row) => {
            if (!summary[row.fiscal_year]) {
                summary[row.fiscal_year] = { open: 0, closed: 0, locked: 0 };
            }
            if (row.period_status === 1) {
                summary[row.fiscal_year].open += 1;
            } else if (row.period_status === 2) {
                summary[row.fiscal_year].closed += 1;
            } else if (row.period_status === 3) {
                summary[row.fiscal_year].locked += 1;
            }
            return summary;
        }, {});
    }, [periodStatuses]);

    const hasPeriodsForSelectedYear = useMemo(() => {
        return periods.some((period) => period.year === fiscalYear);
    }, [fiscalYear, periods]);

    const closeLedgerDialog = (): void => {
        setLedgerDialogOpen(false);
        setLedgerForm(emptyLedgerForm);
    };

    const openCreateLedgerDialog = (): void => {
        setPageError(null);
        setSuccessMessage(null);
        setLedgerForm(emptyLedgerForm);
        setLedgerDialogOpen(true);
    };

    const openEditLedgerDialog = (ledger: FinanceLedger): void => {
        setPageError(null);
        setSuccessMessage(null);
        setLedgerForm({
            recid: ledger.recid,
            element_name: ledger.element_name,
            element_description: ledger.element_description || "",
            element_chart_of_accounts_guid: ledger.element_chart_of_accounts_guid || "",
            element_status: ledger.element_status,
        });
        setLedgerDialogOpen(true);
    };

    const refreshFinanceAdminData = useCallback(async (): Promise<void> => {
        await Promise.all([loadLedgers(), loadPeriods(), loadPeriodStatuses()]);
    }, [loadLedgers, loadPeriodStatuses, loadPeriods]);

    const submitLedger = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);

            const payload = {
                element_name: ledgerForm.element_name.trim(),
                element_description: ledgerForm.element_description.trim() || null,
                element_chart_of_accounts_guid: ledgerForm.element_chart_of_accounts_guid || null,
            };

            if (ledgerForm.recid === null) {
                await fetchCreateLedger(payload);
                setSuccessMessage(`Created ledger ${payload.element_name}.`);
            } else {
                await fetchUpdateLedger({
                    recid: ledgerForm.recid,
                    ...payload,
                    element_status: ledgerForm.element_status,
                });
                setSuccessMessage(`Updated ledger ${payload.element_name}.`);
            }

            closeLedgerDialog();
            await loadLedgers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handleDeleteLedger = async (ledger: FinanceLedger): Promise<void> => {
        if (!window.confirm(`Delete ledger ${ledger.element_name}? This will mark it inactive.`)) {
            return;
        }
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchDeleteLedger({ recid: ledger.recid });
            setSuccessMessage(`Deleted ledger ${ledger.element_name}.`);
            await loadLedgers();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handleGenerateCalendar = async (): Promise<void> => {
        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            const response = await fetchGenerateCalendar({ fiscal_year: fiscalYear });
            const createdCount = Array.isArray(response.periods) ? response.periods.length : 0;
            setSuccessMessage(`Generated ${createdCount} fiscal periods for ${fiscalYear}.`);
            await refreshFinanceAdminData();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const handlePeriodStatusChange = async (period: FinancePeriod, nextStatus: number): Promise<void> => {
        if (nextStatus === period.status) {
            return;
        }
        const confirmationMessage =
            nextStatus === 2
                ? `Closing period ${period.period_name} will prevent new journal postings. Continue?`
                : nextStatus === 3
                    ? `Locking period ${period.period_name} is intended to be permanent. Continue?`
                    : `Reopen period ${period.period_name}?`;

        if (!window.confirm(confirmationMessage)) {
            return;
        }

        try {
            setIsBusy(true);
            setPageError(null);
            setSuccessMessage(null);
            await fetchUpsertPeriod({
                ...period,
                guid: period.guid || null,
                status: nextStatus,
            });
            setSuccessMessage(`Updated ${period.period_name} to ${getPeriodStatusLabel(nextStatus)}.`);
            await refreshFinanceAdminData();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        } finally {
            setIsBusy(false);
        }
    };

    const saveAccount = async (): Promise<void> => {
        try {
            setPageError(null);
            await fetchUpsertAccount(newAccount);
            setNewAccount({
                number: "",
                name: "",
                account_type: 0,
                parent: null,
                is_posting: true,
                status: 1,
            });
            await loadAccounts();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const saveDimension = async (): Promise<void> => {
        try {
            setPageError(null);
            await fetchUpsertDimension(dimensionForm);
            setDimensionForm({ recid: null, name: "", value: "", description: "", status: 1 });
            await loadDimensions();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

    const saveVendor = async (): Promise<void> => {
        if (!vendorForm.element_name.trim()) {
            return;
        }
        try {
            setPageError(null);
            await fetchUpsertVendor({
                recid: vendorForm.recid,
                element_name: vendorForm.element_name,
                element_display: vendorForm.element_display || null,
                element_description: vendorForm.element_description || null,
                element_status: vendorForm.element_status ? 1 : 0,
            });
            setVendorFormOpen(false);
            setVendorForm({
                recid: null,
                element_name: "",
                element_display: "",
                element_description: "",
                element_status: true,
            });
            await loadVendors();
        } catch (error: unknown) {
            setPageError(getErrorMessage(error));
        }
    };

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

            {pageError && <Alert severity="error" sx={{ mb: 2 }}>{pageError}</Alert>}
            {successMessage && <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert>}

            <Tabs value={tab} onChange={(_, next) => setTab(next)}>
                <Tab label="Ledgers" />
                <Tab label="Fiscal Calendar" />
                <Tab label="Chart of Accounts" />
                <Tab label="Financial Dimensions" />
                <Tab label="Vendors" />
            </Tabs>

            {tab === 0 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction={{ xs: "column", md: "row" }} spacing={2} justifyContent="space-between">
                            <Box>
                                <Typography variant="h6">Ledger management</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Create and manage the General Ledger and any future reporting ledgers.
                                </Typography>
                            </Box>
                            <Button startIcon={<AddIcon />} variant="contained" onClick={openCreateLedgerDialog}>
                                Create ledger
                            </Button>
                        </Stack>
                    </Paper>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Created</TableCell>
                                <TableCell align="right">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {ledgers.map((ledger) => (
                                <TableRow key={ledger.recid}>
                                    <TableCell>{ledger.element_name}</TableCell>
                                    <TableCell>{ledger.element_description || "—"}</TableCell>
                                    <TableCell>
                                        <Chip
                                            size="small"
                                            color={ledger.element_status === 1 ? "success" : "default"}
                                            label={getLedgerStatusLabel(ledger.element_status)}
                                        />
                                    </TableCell>
                                    <TableCell>{formatDateTime(ledger.element_created_on)}</TableCell>
                                    <TableCell align="right">
                                        <IconButton aria-label={`Edit ${ledger.element_name}`} onClick={() => openEditLedgerDialog(ledger)}>
                                            <EditIcon fontSize="small" />
                                        </IconButton>
                                        <IconButton
                                            aria-label={`Delete ${ledger.element_name}`}
                                            color="error"
                                            onClick={() => void handleDeleteLedger(ledger)}
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                            {ledgers.length === 0 && (
                                <TableRow>
                                    <TableCell colSpan={6}>
                                        <Typography variant="body2" color="text.secondary">
                                            No ledgers have been created yet.
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Stack>
            )}

            {tab === 1 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ xs: "stretch", md: "center" }}>
                                <TextField
                                    type="number"
                                    label="Fiscal Year"
                                    value={fiscalYear}
                                    onChange={(event) => setFiscalYear(Number(event.target.value))}
                                    sx={{ maxWidth: 220 }}
                                />
                                <Button
                                    variant="contained"
                                    disabled={isBusy || !Number.isFinite(fiscalYear) || hasPeriodsForSelectedYear}
                                    onClick={() => void handleGenerateCalendar()}
                                >
                                    Generate fiscal year
                                </Button>
                                {hasPeriodsForSelectedYear && (
                                    <Alert severity="warning" sx={{ py: 0 }}>
                                        Fiscal year {fiscalYear} already has generated periods.
                                    </Alert>
                                )}
                            </Stack>
                            <Typography variant="body2" color="text.secondary">
                                The calendar generator creates 12 standard 28-day periods and 4 closing weeks using the
                                4-4-5 fiscal pattern.
                            </Typography>
                        </Stack>
                    </Paper>

                    <Stack direction={{ xs: "column", md: "row" }} spacing={2} flexWrap="wrap">
                        {periodYears.map((year) => {
                            const summary = periodSummaryByYear[year] || { open: 0, closed: 0, locked: 0 };
                            return (
                                <Paper key={year} sx={{ p: 2, minWidth: 220 }}>
                                    <Typography variant="subtitle1">FY {year}</Typography>
                                    <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
                                        <Chip size="small" color="success" label={`${summary.open} Open`} />
                                        <Chip size="small" color="warning" label={`${summary.closed} Closed`} />
                                        <Chip size="small" color="error" label={`${summary.locked} Locked`} />
                                    </Stack>
                                </Paper>
                            );
                        })}
                    </Stack>

                    {groupedPeriods.map(({ year, periods: periodsForYear }) => (
                        <Accordion key={year} defaultExpanded={year === fiscalYear}>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                <Stack direction={{ xs: "column", md: "row" }} spacing={2} alignItems={{ md: "center" }}>
                                    <Typography variant="h6">Fiscal Year {year}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {periodsForYear.length} periods
                                    </Typography>
                                </Stack>
                            </AccordionSummary>
                            <AccordionDetails>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>#</TableCell>
                                            <TableCell>Name</TableCell>
                                            <TableCell>Start</TableCell>
                                            <TableCell>End</TableCell>
                                            <TableCell>Days</TableCell>
                                            <TableCell>Quarter</TableCell>
                                            <TableCell>Closing Week</TableCell>
                                            <TableCell>Status</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {periodsForYear.map((period) => {
                                            const statusChoices = PERIOD_STATUS_OPTIONS.filter((option) => option.value >= period.status);
                                            return (
                                                <TableRow key={period.guid || `${period.year}-${period.period_number}`}>
                                                    <TableCell>{period.period_number}</TableCell>
                                                    <TableCell>
                                                        <Stack direction="row" spacing={1} alignItems="center">
                                                            <Typography variant="body2">{period.period_name}</Typography>
                                                            {period.is_leap_adjustment && (
                                                                <Chip size="small" color="info" label="53-week adj." />
                                                            )}
                                                        </Stack>
                                                    </TableCell>
                                                    <TableCell>{formatDate(period.start_date)}</TableCell>
                                                    <TableCell>{formatDate(period.end_date)}</TableCell>
                                                    <TableCell>{period.days_in_period}</TableCell>
                                                    <TableCell>{period.quarter_number}</TableCell>
                                                    <TableCell>{period.has_closing_week ? "Yes" : "No"}</TableCell>
                                                    <TableCell>
                                                        <Stack direction={{ xs: "column", md: "row" }} spacing={1} alignItems={{ md: "center" }}>
                                                            <Chip
                                                                size="small"
                                                                color={getStatusChipColor(period.status)}
                                                                label={getPeriodStatusLabel(period.status)}
                                                            />
                                                            <FormControl size="small" sx={{ minWidth: 140 }}>
                                                                <InputLabel id={`period-status-${period.guid}`}>Change</InputLabel>
                                                                <Select
                                                                    labelId={`period-status-${period.guid}`}
                                                                    label="Change"
                                                                    value={period.status}
                                                                    onChange={(event) =>
                                                                        void handlePeriodStatusChange(period, Number(event.target.value))
                                                                    }
                                                                >
                                                                    {statusChoices.map((option) => (
                                                                        <MenuItem key={option.value} value={option.value}>
                                                                            {option.label}
                                                                        </MenuItem>
                                                                    ))}
                                                                </Select>
                                                            </FormControl>
                                                        </Stack>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                        {periodsForYear.length === 0 && (
                                            <TableRow>
                                                <TableCell colSpan={8}>
                                                    <Typography variant="body2" color="text.secondary">
                                                        No periods generated for this fiscal year.
                                                    </Typography>
                                                </TableCell>
                                            </TableRow>
                                        )}
                                    </TableBody>
                                </Table>
                            </AccordionDetails>
                        </Accordion>
                    ))}
                </Stack>
            )}

            {tab === 2 && (
                <Stack spacing={2} sx={{ mt: 2 }}>
                    <Paper sx={{ p: 2 }}>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                            <TextField
                                label="Account Number"
                                value={newAccount.number}
                                onChange={(event) => setNewAccount({ ...newAccount, number: event.target.value })}
                            />
                            <TextField
                                label="Name"
                                value={newAccount.name}
                                onChange={(event) => setNewAccount({ ...newAccount, name: event.target.value })}
                            />
                            <TextField
                                select
                                label="Type"
                                value={newAccount.account_type}
                                onChange={(event) =>
                                    setNewAccount({ ...newAccount, account_type: Number(event.target.value) })
                                }
                            >
                                {ACCOUNT_TYPES.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </TextField>
                            <Button variant="contained" onClick={() => void saveAccount()}>
                                Save
                            </Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Number</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell />
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {accounts.map((item) => (
                                <TableRow key={item.guid || item.number}>
                                    <TableCell>{item.number}</TableCell>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell>
                                        {ACCOUNT_TYPES.find((option) => option.value === item.account_type)?.label || item.account_type}
                                    </TableCell>
                                    <TableCell>{item.status}</TableCell>
                                    <TableCell>
                                        <Button onClick={() => setNewAccount(item)}>Edit</Button>
                                        <Button
                                            color="error"
                                            onClick={async () => {
                                                if (!item.guid) {
                                                    return;
                                                }
                                                await fetchDeleteAccount({ guid: item.guid });
                                                await loadAccounts();
                                            }}
                                        >
                                            Delete
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
                            <TextField
                                label="Dimension Name"
                                value={dimensionForm.name}
                                onChange={(event) => setDimensionForm({ ...dimensionForm, name: event.target.value })}
                            />
                            <TextField
                                label="Value"
                                value={dimensionForm.value}
                                onChange={(event) => setDimensionForm({ ...dimensionForm, value: event.target.value })}
                            />
                            <TextField
                                label="Description"
                                value={dimensionForm.description}
                                onChange={(event) =>
                                    setDimensionForm({ ...dimensionForm, description: event.target.value })
                                }
                            />
                            <Button variant="contained" onClick={() => void saveDimension()}>
                                Save
                            </Button>
                        </Stack>
                    </Paper>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Value</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell />
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {dimensions.map((item) => (
                                <TableRow key={item.recid || `${item.name}:${item.value}`}>
                                    <TableCell>{item.name}</TableCell>
                                    <TableCell>{item.value}</TableCell>
                                    <TableCell>{item.description || ""}</TableCell>
                                    <TableCell>{item.status}</TableCell>
                                    <TableCell>
                                        <Button onClick={() => setDimensionForm(item)}>Edit</Button>
                                        <Button
                                            color="error"
                                            onClick={async () => {
                                                if (!item.recid) {
                                                    return;
                                                }
                                                await fetchDeleteDimension({ recid: item.recid });
                                                await loadDimensions();
                                            }}
                                        >
                                            Delete
                                        </Button>
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
                        <Stack direction="row" spacing={1} justifyContent="space-between" alignItems="center" flexWrap="wrap">
                            <Typography variant="subtitle1">Vendors</Typography>
                            <Button
                                variant="contained"
                                onClick={() => {
                                    setVendorForm({
                                        recid: null,
                                        element_name: "",
                                        element_display: "",
                                        element_description: "",
                                        element_status: true,
                                    });
                                    setVendorFormOpen(true);
                                }}
                            >
                                Create Vendor
                            </Button>
                        </Stack>
                    </Paper>

                    <Collapse in={vendorFormOpen}>
                        <Paper sx={{ p: 2 }}>
                            <Stack spacing={2}>
                                <Stack direction="row" spacing={1} flexWrap="wrap">
                                    <TextField
                                        label="Name"
                                        required
                                        value={vendorForm.element_name}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_name: event.target.value }))
                                        }
                                    />
                                    <TextField
                                        label="Display Name"
                                        value={vendorForm.element_display}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_display: event.target.value }))
                                        }
                                    />
                                    <TextField
                                        label="Description"
                                        value={vendorForm.element_description}
                                        onChange={(event) =>
                                            setVendorForm((previous) => ({ ...previous, element_description: event.target.value }))
                                        }
                                    />
                                    <FormControlLabel
                                        label="Active"
                                        control={
                                            <Checkbox
                                                checked={vendorForm.element_status}
                                                onChange={(event) =>
                                                    setVendorForm((previous) => ({
                                                        ...previous,
                                                        element_status: event.target.checked,
                                                    }))
                                                }
                                            />
                                        }
                                    />
                                </Stack>
                                <Stack direction="row" spacing={1}>
                                    <Button variant="contained" onClick={() => void saveVendor()}>
                                        Save
                                    </Button>
                                    <Button
                                        onClick={() => {
                                            setVendorFormOpen(false);
                                            setVendorForm({
                                                recid: null,
                                                element_name: "",
                                                element_display: "",
                                                element_description: "",
                                                element_status: true,
                                            });
                                        }}
                                    >
                                        Cancel
                                    </Button>
                                </Stack>
                            </Stack>
                        </Paper>
                    </Collapse>

                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Display Name</TableCell>
                                <TableCell>Description</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {vendorList.map((item) => (
                                <TableRow key={item.recid || item.element_name}>
                                    <TableCell>{item.element_name}</TableCell>
                                    <TableCell>{item.element_display || ""}</TableCell>
                                    <TableCell>{item.element_description || ""}</TableCell>
                                    <TableCell>
                                        <Chip
                                            size="small"
                                            color={item.element_status === 1 ? "success" : "default"}
                                            label={item.element_status === 1 ? "Active" : "Disabled"}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Stack direction="row" spacing={1}>
                                            <Button
                                                size="small"
                                                onClick={() => {
                                                    setVendorForm({
                                                        recid: item.recid || null,
                                                        element_name: item.element_name || "",
                                                        element_display: item.element_display || "",
                                                        element_description: item.element_description || "",
                                                        element_status: Number(item.element_status) === 1,
                                                    });
                                                    setVendorFormOpen(true);
                                                }}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                size="small"
                                                color="error"
                                                onClick={async () => {
                                                    if (!item.recid || !window.confirm(`Delete vendor ${item.element_name}?`)) {
                                                        return;
                                                    }
                                                    await fetchDeleteVendor({ recid: item.recid });
                                                    await loadVendors();
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
                </Stack>
            )}

            <Dialog fullWidth maxWidth="sm" open={ledgerDialogOpen} onClose={closeLedgerDialog}>
                <DialogTitle>{ledgerForm.recid === null ? "Create ledger" : "Edit ledger"}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            autoFocus
                            required
                            label="Ledger name"
                            value={ledgerForm.element_name}
                            onChange={(event) =>
                                setLedgerForm((previous) => ({ ...previous, element_name: event.target.value }))
                            }
                        />
                        <TextField
                            label="Description"
                            value={ledgerForm.element_description}
                            onChange={(event) =>
                                setLedgerForm((previous) => ({ ...previous, element_description: event.target.value }))
                            }
                            multiline
                            minRows={2}
                        />
                        <FormControl fullWidth>
                            <InputLabel id="ledger-coa-label">Chart of accounts root</InputLabel>
                            <Select
                                labelId="ledger-coa-label"
                                label="Chart of accounts root"
                                value={ledgerForm.element_chart_of_accounts_guid}
                                onChange={(event) =>
                                    setLedgerForm((previous) => ({
                                        ...previous,
                                        element_chart_of_accounts_guid: String(event.target.value),
                                    }))
                                }
                            >
                                <MenuItem value="">
                                    <em>None</em>
                                </MenuItem>
                                {accounts.map((account) => (
                                    <MenuItem key={account.guid || account.number} value={account.guid || ""}>
                                        {account.number} — {account.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        {ledgerForm.recid !== null && (
                            <FormControl fullWidth>
                                <InputLabel id="ledger-status-label">Status</InputLabel>
                                <Select
                                    labelId="ledger-status-label"
                                    label="Status"
                                    value={ledgerForm.element_status}
                                    onChange={(event) =>
                                        setLedgerForm((previous) => ({
                                            ...previous,
                                            element_status: Number(event.target.value),
                                        }))
                                    }
                                >
                                    {LEDGER_STATUS_OPTIONS.map((option) => (
                                        <MenuItem key={option.value} value={option.value}>
                                            {option.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        )}
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closeLedgerDialog}>Cancel</Button>
                    <Button variant="contained" disabled={isBusy || !ledgerForm.element_name.trim()} onClick={() => void submitLedger()}>
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default FinanceAdminPage;
