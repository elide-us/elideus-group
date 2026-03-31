import { useCallback, useEffect, useMemo, useState } from 'react';
import {
    Box,
    Button,
    Chip,
    Paper,
    Stack,
    Tab,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Tabs,
    Typography,
} from '@mui/material';
import PageTitle from '../../components/PageTitle';
import {
    ServiceRpcdispatchDomainItem1,
    ServiceRpcdispatchDomainList1,
    ServiceRpcdispatchFunctionItem1,
    ServiceRpcdispatchFunctionList1,
    ServiceRpcdispatchModelFieldItem1,
    ServiceRpcdispatchModelFieldList1,
    ServiceRpcdispatchModelItem1,
    ServiceRpcdispatchModelList1,
    ServiceRpcdispatchSubdomainItem1,
    ServiceRpcdispatchSubdomainList1,
} from '../../shared/RpcModels';
import {
    fetchListDomains,
    fetchListFunctions,
    fetchListModelFields,
    fetchListModels,
    fetchListSubdomains,
} from '../../rpc/service/rpcdispatch/index';

const EDT_NAME_BY_RECID: Record<number, string> = {
    1: 'INT32',
    2: 'INT64',
    3: 'INT64_IDENTITY',
    4: 'UUID',
    5: 'BOOL',
    7: 'DATETIME_TZ',
    8: 'STRING',
    9: 'TEXT',
    11: 'INT8',
    12: 'DATE',
    13: 'DECIMAL_19_5',
};

const boolChip = (value: boolean): JSX.Element =>
    value ? <Chip label="Yes" color="success" size="small" /> : <Chip label="No" size="small" />;

const statusChip = (status: number): JSX.Element =>
    status === 1 ? <Chip label="Active" color="success" size="small" /> : <Chip label="Disabled" size="small" />;

const emptyValue = (value: string | number | null | undefined): string | number => {
    if (value === null || value === undefined || value === '') {
        return '—';
    }
    return value;
};

const ServiceRpcDispatchPage = (): JSX.Element => {
    const [tabIndex, setTabIndex] = useState(0);
    const [forbidden, setForbidden] = useState(false);

    const [domains, setDomains] = useState<ServiceRpcdispatchDomainItem1[]>([]);
    const [subdomains, setSubdomains] = useState<ServiceRpcdispatchSubdomainItem1[]>([]);
    const [functions, setFunctions] = useState<ServiceRpcdispatchFunctionItem1[]>([]);
    const [models, setModels] = useState<ServiceRpcdispatchModelItem1[]>([]);
    const [fields, setFields] = useState<ServiceRpcdispatchModelFieldItem1[]>([]);

    const [loading, setLoading] = useState(false);

    const domainGuidMap = useMemo(() => new Map(domains.map((d) => [String((d as any).element_guid), d.element_name])), [domains]);
    const subdomainGuidMap = useMemo(() => new Map(subdomains.map((s) => [String((s as any).element_guid), s.element_name])), [subdomains]);
    const modelMap = useMemo(() => new Map(models.map((m) => [m.recid, m.element_name])), [models]);
    const modelGuidMap = useMemo(() => new Map(models.map((m) => [String((m as any).element_guid), m.element_name])), [models]);

    const handleRpcError = (error: any): never => {
        if (error?.response?.status === 403) {
            setForbidden(true);
        }
        throw error;
    };

    const loadDomains = useCallback(async (): Promise<void> => {
        try {
            const response = await fetchListDomains() as ServiceRpcdispatchDomainList1 & { domains: ServiceRpcdispatchDomainItem1[] };
            setDomains(response.domains || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadSubdomains = useCallback(async (): Promise<void> => {
        try {
            const response = await fetchListSubdomains() as ServiceRpcdispatchSubdomainList1 & { subdomains: ServiceRpcdispatchSubdomainItem1[] };
            setSubdomains(response.subdomains || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadFunctions = useCallback(async (): Promise<void> => {
        try {
            const response = await fetchListFunctions() as ServiceRpcdispatchFunctionList1 & { functions: ServiceRpcdispatchFunctionItem1[] };
            setFunctions(response.functions || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadModels = useCallback(async (): Promise<void> => {
        try {
            const response = await fetchListModels() as ServiceRpcdispatchModelList1 & { models: ServiceRpcdispatchModelItem1[] };
            setModels(response.models || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadModelFields = useCallback(async (): Promise<void> => {
        try {
            const response = await fetchListModelFields() as ServiceRpcdispatchModelFieldList1 & { fields: ServiceRpcdispatchModelFieldItem1[] };
            setFields(response.fields || []);
            setForbidden(false);
        } catch (error: any) {
            handleRpcError(error);
        }
    }, []);

    const loadAll = useCallback(async (): Promise<void> => {
        setLoading(true);
        try {
            await Promise.all([loadDomains(), loadSubdomains(), loadFunctions(), loadModels(), loadModelFields()]);
        } finally {
            setLoading(false);
        }
    }, [loadDomains, loadFunctions, loadModelFields, loadModels, loadSubdomains]);

    const refreshActiveTab = useCallback(async (): Promise<void> => {
        setLoading(true);
        try {
            if (tabIndex === 0) {
                await loadDomains();
            } else if (tabIndex === 1) {
                await loadSubdomains();
            } else if (tabIndex === 2) {
                await loadFunctions();
            } else if (tabIndex === 3) {
                await loadModels();
            } else {
                await loadModelFields();
            }
        } finally {
            setLoading(false);
        }
    }, [loadDomains, loadFunctions, loadModelFields, loadModels, loadSubdomains, tabIndex]);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    useEffect(() => {
        void refreshActiveTab();
    }, [tabIndex, refreshActiveTab]);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>RPC Dispatch</PageTitle>

            <Paper sx={{ p: 2, mb: 2 }}>
                <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" color="text.secondary">
                        Read-only service view of reflection_rpc_* metadata tables.
                    </Typography>
                    <Button variant="outlined" onClick={() => void refreshActiveTab()} disabled={loading}>
                        Refresh
                    </Button>
                </Stack>
            </Paper>

            <Paper>
                <Tabs value={tabIndex} onChange={(_, value: number) => setTabIndex(value)} variant="scrollable">
                    <Tab label={`Domains (${domains.length})`} />
                    <Tab label={`Subdomains (${subdomains.length})`} />
                    <Tab label={`Functions (${functions.length})`} />
                    <Tab label={`Models (${models.length})`} />
                    <Tab label={`Model Fields (${fields.length})`} />
                </Tabs>

                <Box sx={{ p: 2 }}>
                    {tabIndex === 0 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Required Role</TableCell>
                                    <TableCell>Auth Exempt</TableCell>
                                    <TableCell>Public</TableCell>
                                    <TableCell>Discord</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                    <TableCell>Iteration</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {domains.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{emptyValue(row.element_required_role)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_auth_exempt)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_public)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_discord)}</TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                        <TableCell>{row.element_iteration}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 1 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Domain</TableCell>
                                    <TableCell>Entitlement Mask</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                    <TableCell>Iteration</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {subdomains.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{domainGuidMap.get(row.domains_guid) ?? `#${row.domains_guid}`}</TableCell>
                                        <TableCell>{row.element_entitlement_mask}</TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                        <TableCell>{row.element_iteration}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 2 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Version</TableCell>
                                    <TableCell>Subdomain</TableCell>
                                    <TableCell>Module Attr</TableCell>
                                    <TableCell>Method Name</TableCell>
                                    <TableCell>Request Model</TableCell>
                                    <TableCell>Response Model</TableCell>
                                    <TableCell>Status</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {functions.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{row.element_version}</TableCell>
                                        <TableCell>{subdomainGuidMap.get(row.subdomains_guid) ?? `#${row.subdomains_guid}`}</TableCell>
                                        <TableCell>{row.element_module_attr}</TableCell>
                                        <TableCell>{row.element_method_name}</TableCell>
                                        <TableCell>
                                            {row.element_request_model_guid
                                                ? modelGuidMap.get(row.element_request_model_guid) ??
                                                  `#${row.element_request_model_guid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>
                                            {row.element_response_model_guid
                                                ? modelGuidMap.get(row.element_response_model_guid) ??
                                                  `#${row.element_response_model_guid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 3 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Name</TableCell>
                                    <TableCell>Domain</TableCell>
                                    <TableCell>Subdomain</TableCell>
                                    <TableCell>Version</TableCell>
                                    <TableCell>Parent</TableCell>
                                    <TableCell>Status</TableCell>
                                    <TableCell>App Version</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {models.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{row.element_domain}</TableCell>
                                        <TableCell>{row.element_subdomain}</TableCell>
                                        <TableCell>{row.element_version}</TableCell>
                                        <TableCell>
                                            {row.element_parent_recid
                                                ? modelMap.get(row.element_parent_recid) ?? `#${row.element_parent_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{statusChip(row.element_status)}</TableCell>
                                        <TableCell>{emptyValue(row.element_app_version)}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}

                    {tabIndex === 4 && (
                        <Table size="small">
                            <TableHead>
                                <TableRow>
                                    <TableCell>Field Name</TableCell>
                                    <TableCell>Model</TableCell>
                                    <TableCell>EDT</TableCell>
                                    <TableCell>Nullable</TableCell>
                                    <TableCell>List</TableCell>
                                    <TableCell>Dict</TableCell>
                                    <TableCell>Ref Model</TableCell>
                                    <TableCell>Default Value</TableCell>
                                    <TableCell>Sort Order</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {fields.map((row) => (
                                    <TableRow key={row.recid}>
                                        <TableCell>{row.element_name}</TableCell>
                                        <TableCell>{modelGuidMap.get(row.models_guid) ?? `#${row.models_guid}`}</TableCell>
                                        <TableCell>
                                            {row.element_edt_recid
                                                ? EDT_NAME_BY_RECID[row.element_edt_recid] ?? `#${row.element_edt_recid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{boolChip(row.element_is_nullable)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_list)}</TableCell>
                                        <TableCell>{boolChip(row.element_is_dict)}</TableCell>
                                        <TableCell>
                                            {row.element_ref_model_guid
                                                ? modelGuidMap.get(row.element_ref_model_guid) ??
                                                  `#${row.element_ref_model_guid}`
                                                : '—'}
                                        </TableCell>
                                        <TableCell>{emptyValue(row.element_default_value)}</TableCell>
                                        <TableCell>{row.element_sort_order}</TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </Box>
            </Paper>
        </Box>
    );
};

export default ServiceRpcDispatchPage;
