import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Box,
    Button,
    Checkbox,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    DialogContentText,
    DialogTitle,
    FormControlLabel,
    MenuItem,
    Paper,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from '@mui/material';
import Notification from '../../components/Notification';
import PageTitle from '../../components/PageTitle';
import {
    fetchList as fetchRenewalList,
    fetchUpsert as fetchRenewalUpsert,
    fetchDelete as fetchRenewalDelete,
} from '../../rpc/service/renewals';
import { fetchCreate as fetchPaymentCreate } from '../../rpc/service/payment_requests';
import type { ServiceRenewalsItem1, ServiceRenewalsUpsert1 } from '../../shared/RpcModels';

type RenewalItem = ServiceRenewalsItem1;

type RenewalForm = {
    recid: number | null;
    element_name: string;
    element_category: string;
    element_vendor: string;
    element_reference: string;
    element_expires_on: string;
    element_renew_by: string;
    element_renewal_cost: string;
    element_currency: string;
    element_auto_renew: boolean;
    element_owner: string;
    element_notes: string;
    element_status: number;
};

type PaymentFormState = {
    amount: string;
    description: string;
    period_start: string;
    period_end: string;
};

const EMPTY_FORM: RenewalForm = {
    recid: null,
    element_name: '',
    element_category: 'domain',
    element_vendor: '',
    element_reference: '',
    element_expires_on: '',
    element_renew_by: '',
    element_renewal_cost: '',
    element_currency: 'USD',
    element_auto_renew: false,
    element_owner: '',
    element_notes: '',
    element_status: 1,
};

const CATEGORIES = ['domain', 'certificate', 'secret', 'api_key', 'subscription'] as const;

const STATUS_CONFIG: Record<number, { label: string; color: 'success' | 'error' | 'default' | 'warning' | 'info' }> = {
    1: { label: 'Active', color: 'success' },
    2: { label: 'Expired', color: 'error' },
    3: { label: 'Renewed', color: 'info' },
    0: { label: 'Disabled', color: 'default' },
};

const getExpiryChip = (dateStr: string | null): { label: string; color: 'success' | 'warning' | 'error' | 'default' } => {
    if (!dateStr) {
        return { label: 'No date', color: 'default' };
    }

    const now = new Date();
    const expiry = new Date(dateStr);

    if (Number.isNaN(expiry.getTime())) {
        return { label: 'Invalid date', color: 'default' };
    }

    const daysUntil = Math.ceil((expiry.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (daysUntil < 0) {
        return { label: `Expired ${Math.abs(daysUntil)}d ago`, color: 'error' };
    }
    if (daysUntil <= 30) {
        return { label: `${daysUntil}d`, color: 'error' };
    }
    if (daysUntil <= 60) {
        return { label: `${daysUntil}d`, color: 'warning' };
    }
    return { label: `${daysUntil}d`, color: 'success' };
};

const mapItemToForm = (item: RenewalItem): RenewalForm => ({
    recid: item.recid,
    element_name: item.element_name,
    element_category: item.element_category,
    element_vendor: item.element_vendor ?? '',
    element_reference: item.element_reference ?? '',
    element_expires_on: item.element_expires_on ?? '',
    element_renew_by: item.element_renew_by ?? '',
    element_renewal_cost: item.element_renewal_cost ?? '',
    element_currency: item.element_currency ?? 'USD',
    element_auto_renew: item.element_auto_renew,
    element_owner: item.element_owner ?? '',
    element_notes: item.element_notes ?? '',
    element_status: item.element_status,
});

const formatDate = (value: string | null): string => value || '—';

const formatCost = (item: RenewalItem): string => {
    if (!item.element_renewal_cost) {
        return '—';
    }
    return `${item.element_renewal_cost} ${item.element_currency || ''}`.trim();
};

const EMPTY_PAYMENT_FORM: PaymentFormState = {
    amount: '',
    description: '',
    period_start: '',
    period_end: '',
};

const formatDateInput = (value: Date): string => value.toISOString().slice(0, 10);

const getCurrentMonthBounds = (): Pick<PaymentFormState, 'period_start' | 'period_end'> => {
    const now = new Date();
    const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
    const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 0));

    return {
        period_start: formatDateInput(start),
        period_end: formatDateInput(end),
    };
};

const ServiceRenewalsPage = (): JSX.Element => {
    const [renewals, setRenewals] = useState<RenewalItem[]>([]);
    const [categoryFilter, setCategoryFilter] = useState<string>('');
    const [selectedRecid, setSelectedRecid] = useState<number | null>(null);
    const [creating, setCreating] = useState(false);
    const [form, setForm] = useState<RenewalForm>(EMPTY_FORM);
    const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
    const [forbidden, setForbidden] = useState(false);
    const [notificationOpen, setNotificationOpen] = useState(false);
    const [notificationMessage, setNotificationMessage] = useState('Saved');
    const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
    const [paymentForm, setPaymentForm] = useState<PaymentFormState>(EMPTY_PAYMENT_FORM);
    const [paymentStandalone, setPaymentStandalone] = useState(false);
    const [paymentVendor, setPaymentVendor] = useState('');
    const [paymentService, setPaymentService] = useState('');

    const loadRenewals = useCallback(async (): Promise<void> => {
        try {
            const res = await fetchRenewalList({ category: categoryFilter || null, status: null });
            setRenewals(res.renewals || []);
            setForbidden(false);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
                return;
            }
            throw e;
        }
    }, [categoryFilter]);

    useEffect(() => {
        void loadRenewals();
    }, [loadRenewals]);

    const sortedRenewals = useMemo(() => {
        return [...renewals].sort((a, b) => {
            const aTime = a.element_expires_on ? new Date(a.element_expires_on).getTime() : Number.POSITIVE_INFINITY;
            const bTime = b.element_expires_on ? new Date(b.element_expires_on).getTime() : Number.POSITIVE_INFINITY;
            return aTime - bTime;
        });
    }, [renewals]);

    const selectedLabel = useMemo(() => {
        if (creating) {
            return 'Create Renewal';
        }
        const current = renewals.find((item) => item.recid === selectedRecid);
        return current ? `Edit ${current.element_name}` : 'Edit Renewal';
    }, [creating, renewals, selectedRecid]);

    const resetSelection = (): void => {
        setSelectedRecid(null);
        setCreating(false);
        setForm(EMPTY_FORM);
        setConfirmDelete(null);
    };

    const showNotification = (message: string): void => {
        setNotificationMessage(message);
        setNotificationOpen(true);
    };

    const handleRowClick = (item: RenewalItem): void => {
        setSelectedRecid(item.recid);
        setCreating(false);
        setForm(mapItemToForm(item));
    };

    const handleCreate = (): void => {
        setSelectedRecid(null);
        setCreating(true);
        setForm(EMPTY_FORM);
    };

    const openPaymentDialog = (standalone: boolean): void => {
        const monthBounds = getCurrentMonthBounds();
        setPaymentStandalone(standalone);

        if (standalone) {
            setPaymentVendor('');
            setPaymentService('');
            setPaymentForm({
                ...EMPTY_PAYMENT_FORM,
                ...monthBounds,
            });
        } else {
            setPaymentVendor(form.element_vendor);
            setPaymentService(form.element_name);
            setPaymentForm({
                amount: form.element_renewal_cost,
                description: form.element_name ? `${form.element_name} renewal` : '',
                ...monthBounds,
            });
        }

        setPaymentDialogOpen(true);
    };

    const closePaymentDialog = (): void => {
        setPaymentDialogOpen(false);
        setPaymentStandalone(false);
        setPaymentVendor('');
        setPaymentService('');
        setPaymentForm(EMPTY_PAYMENT_FORM);
    };

    const handleSave = async (): Promise<void> => {
        await fetchRenewalUpsert({
            ...form,
            recid: form.recid,
            element_vendor: form.element_vendor || null,
            element_reference: form.element_reference || null,
            element_expires_on: form.element_expires_on || null,
            element_renew_by: form.element_renew_by || null,
            element_renewal_cost: form.element_renewal_cost || null,
            element_currency: form.element_currency || null,
            element_owner: form.element_owner || null,
            element_notes: form.element_notes || null,
        } as ServiceRenewalsUpsert1);
        await loadRenewals();
        showNotification(form.recid ? 'Renewal updated' : 'Renewal created');
        resetSelection();
    };

    const handleDeleteConfirm = async (): Promise<void> => {
        if (confirmDelete === null) {
            return;
        }
        await fetchRenewalDelete({ recid: confirmDelete });
        await loadRenewals();
        showNotification('Renewal deleted');
        resetSelection();
    };

    const handlePaymentSubmit = async (): Promise<void> => {
        await fetchPaymentCreate({
            vendor_name: paymentStandalone ? paymentVendor || '' : form.element_vendor || '',
            amount: paymentForm.amount,
            currency: form.element_currency || 'USD',
            description: paymentForm.description,
            service: paymentStandalone ? paymentService || null : form.element_name || null,
            category: paymentStandalone ? null : form.element_category || null,
            period_start: paymentForm.period_start,
            period_end: paymentForm.period_end,
            renewal_recid: paymentStandalone ? null : form.recid,
        });
        showNotification('Payment request created');
        closePaymentDialog();
    };

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <PageTitle>Renewals</PageTitle>
                <Typography variant="h6">Access denied</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <Stack spacing={2}>
                <PageTitle>Renewals</PageTitle>

                <Paper sx={{ p: 2 }}>
                    <Stack
                        direction={{ xs: 'column', md: 'row' }}
                        spacing={2}
                        alignItems={{ xs: 'stretch', md: 'center' }}
                        justifyContent="space-between"
                    >
                        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2} sx={{ flex: 1 }}>
                            <TextField
                                select
                                label="Category"
                                value={categoryFilter}
                                onChange={(event) => setCategoryFilter(event.target.value)}
                                sx={{ minWidth: { xs: '100%', sm: 220 } }}
                            >
                                <MenuItem value="">All</MenuItem>
                                {CATEGORIES.map((category) => (
                                    <MenuItem key={category} value={category}>
                                        {category}
                                    </MenuItem>
                                ))}
                            </TextField>
                        </Stack>
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                            <Button variant="outlined" onClick={() => void loadRenewals()}>
                                Refresh
                            </Button>
                            <Button variant="outlined" onClick={() => openPaymentDialog(true)}>
                                Request Payment
                            </Button>
                            <Button variant="contained" onClick={handleCreate}>
                                Create
                            </Button>
                        </Stack>
                    </Stack>
                </Paper>

                <Paper sx={{ p: 2, overflowX: 'auto' }}>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Category</TableCell>
                                <TableCell>Vendor</TableCell>
                                <TableCell>Expires</TableCell>
                                <TableCell>Renew By</TableCell>
                                <TableCell>Cost</TableCell>
                                <TableCell>Auto-Renew</TableCell>
                                <TableCell>Status</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {sortedRenewals.map((item) => {
                                const expiryChip = getExpiryChip(item.element_expires_on);
                                const statusConfig = STATUS_CONFIG[item.element_status] || {
                                    label: `Status ${item.element_status}`,
                                    color: 'default' as const,
                                };
                                const isSelected = !creating && selectedRecid === item.recid;

                                return (
                                    <TableRow
                                        key={item.recid}
                                        hover
                                        selected={isSelected}
                                        onClick={() => handleRowClick(item)}
                                        sx={{ cursor: 'pointer' }}
                                    >
                                        <TableCell>{item.element_name}</TableCell>
                                        <TableCell>
                                            <Chip label={item.element_category} />
                                        </TableCell>
                                        <TableCell>{item.element_vendor || '—'}</TableCell>
                                        <TableCell>
                                            <Stack direction="row" spacing={1} alignItems="center">
                                                <Typography variant="body2">{formatDate(item.element_expires_on)}</Typography>
                                                <Chip label={expiryChip.label} color={expiryChip.color} />
                                            </Stack>
                                        </TableCell>
                                        <TableCell>{formatDate(item.element_renew_by)}</TableCell>
                                        <TableCell>{formatCost(item)}</TableCell>
                                        <TableCell>
                                            <Chip
                                                label={item.element_auto_renew ? 'Yes' : 'No'}
                                                color={item.element_auto_renew ? 'success' : 'default'}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Chip label={statusConfig.label} color={statusConfig.color} />
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                            {!sortedRenewals.length && (
                                <TableRow>
                                    <TableCell colSpan={8}>
                                        <Typography variant="body2" color="text.secondary">
                                            No renewals found.
                                        </Typography>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </Paper>

                {(creating || selectedRecid !== null) && (
                    <Paper sx={{ p: 2 }}>
                        <Stack spacing={2}>
                            <Typography variant="h6">{selectedLabel}</Typography>

                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                                <TextField
                                    label="Name"
                                    value={form.element_name}
                                    onChange={(event) => setForm({ ...form, element_name: event.target.value })}
                                    fullWidth
                                />
                                <TextField
                                    select
                                    label="Category"
                                    value={form.element_category}
                                    onChange={(event) => setForm({ ...form, element_category: event.target.value })}
                                    fullWidth
                                >
                                    {CATEGORIES.map((category) => (
                                        <MenuItem key={category} value={category}>
                                            {category}
                                        </MenuItem>
                                    ))}
                                </TextField>
                                <TextField
                                    label="Vendor"
                                    value={form.element_vendor}
                                    onChange={(event) => setForm({ ...form, element_vendor: event.target.value })}
                                    fullWidth
                                />
                            </Stack>

                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                                <TextField
                                    label="Reference"
                                    value={form.element_reference}
                                    onChange={(event) => setForm({ ...form, element_reference: event.target.value })}
                                    fullWidth
                                />
                                <TextField
                                    label="Owner"
                                    value={form.element_owner}
                                    onChange={(event) => setForm({ ...form, element_owner: event.target.value })}
                                    fullWidth
                                />
                            </Stack>

                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
                                <TextField
                                    label="Expires On"
                                    type="date"
                                    value={form.element_expires_on}
                                    onChange={(event) => setForm({ ...form, element_expires_on: event.target.value })}
                                    InputLabelProps={{ shrink: true }}
                                    fullWidth
                                />
                                <TextField
                                    label="Renew By"
                                    type="date"
                                    value={form.element_renew_by}
                                    onChange={(event) => setForm({ ...form, element_renew_by: event.target.value })}
                                    InputLabelProps={{ shrink: true }}
                                    fullWidth
                                />
                                <TextField
                                    label="Renewal Cost"
                                    value={form.element_renewal_cost}
                                    onChange={(event) => setForm({ ...form, element_renewal_cost: event.target.value })}
                                    fullWidth
                                />
                                <TextField
                                    label="Currency"
                                    value={form.element_currency}
                                    onChange={(event) => setForm({ ...form, element_currency: event.target.value })}
                                    fullWidth
                                />
                            </Stack>

                            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} alignItems={{ xs: 'flex-start', md: 'center' }}>
                                <FormControlLabel
                                    control={
                                        <Checkbox
                                            checked={form.element_auto_renew}
                                            onChange={(event) => setForm({ ...form, element_auto_renew: event.target.checked })}
                                        />
                                    }
                                    label="Auto-Renew"
                                />
                                <TextField
                                    select
                                    label="Status"
                                    value={String(form.element_status)}
                                    onChange={(event) => setForm({ ...form, element_status: Number(event.target.value) })}
                                    sx={{ minWidth: { xs: '100%', md: 220 } }}
                                >
                                    <MenuItem value="1">Active</MenuItem>
                                    <MenuItem value="0">Disabled</MenuItem>
                                    <MenuItem value="2">Expired</MenuItem>
                                    <MenuItem value="3">Renewed</MenuItem>
                                </TextField>
                            </Stack>

                            <TextField
                                label="Notes"
                                value={form.element_notes}
                                onChange={(event) => setForm({ ...form, element_notes: event.target.value })}
                                multiline
                                minRows={4}
                                fullWidth
                            />

                            <Stack direction="row" spacing={1} justifyContent="flex-end">
                                {!creating && form.recid !== null && (
                                    <Button variant="outlined" color="warning" onClick={() => openPaymentDialog(false)}>
                                        Request Payment
                                    </Button>
                                )}
                                <Button
                                    variant="contained"
                                    onClick={() => void handleSave()}
                                    disabled={!form.element_name.trim() || !form.element_category.trim()}
                                >
                                    Save
                                </Button>
                                {!creating && form.recid !== null && (
                                    <Button color="error" variant="outlined" onClick={() => setConfirmDelete(form.recid)}>
                                        Delete
                                    </Button>
                                )}
                                <Button variant="text" onClick={resetSelection}>
                                    Cancel
                                </Button>
                            </Stack>
                        </Stack>
                    </Paper>
                )}
            </Stack>

            <Dialog open={confirmDelete !== null} onClose={() => setConfirmDelete(null)}>
                <DialogTitle>Delete renewal</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Are you sure you want to delete this renewal record? This action cannot be undone.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
                    <Button color="error" variant="contained" onClick={() => void handleDeleteConfirm()}>
                        Delete
                    </Button>
                </DialogActions>
            </Dialog>

            <Dialog open={paymentDialogOpen} onClose={closePaymentDialog} maxWidth="sm" fullWidth>
                <DialogTitle>{paymentStandalone ? 'Request Payment' : 'Request Renewal Payment'}</DialogTitle>
                <DialogContent>
                    <Stack spacing={2} sx={{ mt: 1 }}>
                        <TextField
                            label="Vendor Name"
                            value={paymentVendor}
                            onChange={(event) => setPaymentVendor(event.target.value)}
                            required
                            fullWidth
                            InputProps={{ readOnly: !paymentStandalone }}
                        />
                        <TextField
                            label="Service Name"
                            value={paymentService}
                            onChange={(event) => setPaymentService(event.target.value)}
                            fullWidth
                            InputProps={{ readOnly: !paymentStandalone }}
                        />
                        <TextField
                            label="Amount"
                            value={paymentForm.amount}
                            onChange={(event) => setPaymentForm((previous) => ({ ...previous, amount: event.target.value }))}
                            required
                            fullWidth
                        />
                        <TextField
                            label="Description"
                            value={paymentForm.description}
                            onChange={(event) => setPaymentForm((previous) => ({ ...previous, description: event.target.value }))}
                            required
                            fullWidth
                        />
                        <TextField
                            label="Period Start"
                            value={paymentForm.period_start}
                            onChange={(event) => setPaymentForm((previous) => ({ ...previous, period_start: event.target.value }))}
                            placeholder="YYYY-MM-DD"
                            fullWidth
                        />
                        <TextField
                            label="Period End"
                            value={paymentForm.period_end}
                            onChange={(event) => setPaymentForm((previous) => ({ ...previous, period_end: event.target.value }))}
                            placeholder="YYYY-MM-DD"
                            fullWidth
                        />
                    </Stack>
                </DialogContent>
                <DialogActions>
                    <Button onClick={closePaymentDialog}>Cancel</Button>
                    <Button
                        variant="contained"
                        onClick={() => void handlePaymentSubmit()}
                        disabled={
                            !paymentVendor.trim() ||
                            !paymentForm.amount.trim() ||
                            !paymentForm.description.trim() ||
                            !paymentForm.period_start.trim() ||
                            !paymentForm.period_end.trim()
                        }
                    >
                        Submit Request
                    </Button>
                </DialogActions>
            </Dialog>

            <Notification
                open={notificationOpen}
                handleClose={() => setNotificationOpen(false)}
                severity="success"
                message={notificationMessage}
            />
        </Box>
    );
};

export default ServiceRenewalsPage;
