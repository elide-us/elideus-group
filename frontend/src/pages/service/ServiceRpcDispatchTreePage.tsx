import type { SyntheticEvent } from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Box, Button, Chip, Paper, Stack, Typography } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
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
import { fetchListEdtMappings } from '../../rpc/service/reflection';

function describeFieldType(
    field: ServiceRpcdispatchModelFieldItem1,
    modelMap: Map<string, string>,
    edtMappings: Record<number, string>,
): string {
    const parts: string[] = [];

    if (field.element_ref_model_guid) {
        const refName = modelMap.get(field.element_ref_model_guid) ?? `Model#${field.element_ref_model_guid}`;
        if (field.element_is_list) {
            parts.push(`list[${refName}]`);
        } else {
            parts.push(refName);
        }
    } else if (field.element_is_dict) {
        parts.push(field.element_is_list ? 'list[dict]' : 'JSON');
    } else if (field.element_edt_recid) {
        const edtName = edtMappings[field.element_edt_recid] ?? `EDT#${field.element_edt_recid}`;
        if (field.element_is_list) {
            parts.push(`list[${edtName}]`);
        } else {
            parts.push(edtName);
        }
    } else {
        parts.push('any');
    }

    return parts.join('');
}

const statusChip = (status: number): JSX.Element =>
    status === 1 ? <Chip label="Active" color="success" size="small" /> : <Chip label="Disabled" size="small" />;

const treeItemSx = {
    '& > .MuiTreeItem-content': {
        borderLeft: '1px dashed',
        borderColor: 'divider',
        ml: 1,
        pl: 1,
        py: 0.25,
    },
};

const ServiceRpcDispatchTreePage = (): JSX.Element => {
    const [forbidden, setForbidden] = useState(false);
    const [loading, setLoading] = useState(false);

    const [domains, setDomains] = useState<ServiceRpcdispatchDomainItem1[]>([]);
    const [subdomains, setSubdomains] = useState<ServiceRpcdispatchSubdomainItem1[]>([]);
    const [functions, setFunctions] = useState<ServiceRpcdispatchFunctionItem1[]>([]);
    const [models, setModels] = useState<ServiceRpcdispatchModelItem1[]>([]);
    const [fields, setFields] = useState<ServiceRpcdispatchModelFieldItem1[]>([]);
    const [edtMappings, setEdtMappings] = useState<Record<number, string>>({});

    const [expandedItems, setExpandedItems] = useState<string[]>([]);

    const handleRpcError = (error: any): never => {
        if (error?.response?.status === 403) {
            setForbidden(true);
        }
        throw error;
    };

    const loadAll = useCallback(async (): Promise<void> => {
        setLoading(true);
        try {
            const [domainRes, subdomainRes, functionRes, modelRes, fieldRes, edtRes] = await Promise.all([
                fetchListDomains() as Promise<ServiceRpcdispatchDomainList1 & { domains: ServiceRpcdispatchDomainItem1[] }>,
                fetchListSubdomains() as Promise<ServiceRpcdispatchSubdomainList1 & { subdomains: ServiceRpcdispatchSubdomainItem1[] }>,
                fetchListFunctions() as Promise<ServiceRpcdispatchFunctionList1 & { functions: ServiceRpcdispatchFunctionItem1[] }>,
                fetchListModels() as Promise<ServiceRpcdispatchModelList1 & { models: ServiceRpcdispatchModelItem1[] }>,
                fetchListModelFields() as Promise<ServiceRpcdispatchModelFieldList1 & { fields: ServiceRpcdispatchModelFieldItem1[] }>,
                fetchListEdtMappings() as Promise<{ mappings: { recid: number; element_name: string }[] }>,
            ]);

            const nextDomains = (domainRes.domains || []) as ServiceRpcdispatchDomainItem1[];
            const nextSubdomains = (subdomainRes.subdomains || []) as ServiceRpcdispatchSubdomainItem1[];
            const nextFunctions = (functionRes.functions || []) as ServiceRpcdispatchFunctionItem1[];
            const nextModels = (modelRes.models || []) as ServiceRpcdispatchModelItem1[];
            const nextFields = (fieldRes.fields || []) as ServiceRpcdispatchModelFieldItem1[];
            setDomains(nextDomains);
            setSubdomains(nextSubdomains);
            setFunctions(nextFunctions);
            setModels(nextModels);
            setFields(nextFields);
            const edtMap: Record<number, string> = {};
            for (const row of edtRes.mappings ?? []) {
                edtMap[row.recid] = row.element_name;
            }
            setEdtMappings(edtMap);
            setForbidden(false);
            setExpandedItems(nextDomains.map((domain) => `domain-${domain.recid}`));
        } catch (error: any) {
            handleRpcError(error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void loadAll();
    }, [loadAll]);

    const modelNameByGuid = useMemo(
        () => new Map(models.map((model) => [String((model as any).element_guid), model.element_name])),
        [models],
    );

    const fieldsByModel = useMemo(() => {
        const grouped = new Map<string, ServiceRpcdispatchModelFieldItem1[]>();
        fields.forEach((field) => {
            if (!grouped.has(field.models_guid)) {
                grouped.set(field.models_guid, []);
            }
            grouped.get(field.models_guid)?.push(field);
        });
        grouped.forEach((modelFields) => modelFields.sort((a, b) => a.element_sort_order - b.element_sort_order));
        return grouped;
    }, [fields]);

    const subdomainsByDomain = useMemo(() => {
        const grouped = new Map<string, ServiceRpcdispatchSubdomainItem1[]>();
        subdomains.forEach((subdomain) => {
            if (!grouped.has(subdomain.domains_guid)) {
                grouped.set(subdomain.domains_guid, []);
            }
            grouped.get(subdomain.domains_guid)?.push(subdomain);
        });
        grouped.forEach((items) => items.sort((a, b) => a.element_name.localeCompare(b.element_name)));
        return grouped;
    }, [subdomains]);

    const functionsBySubdomain = useMemo(() => {
        const grouped = new Map<string, ServiceRpcdispatchFunctionItem1[]>();
        functions.forEach((fn) => {
            if (!grouped.has(fn.subdomains_guid)) {
                grouped.set(fn.subdomains_guid, []);
            }
            grouped.get(fn.subdomains_guid)?.push(fn);
        });
        grouped.forEach((items) => items.sort((a, b) => a.element_name.localeCompare(b.element_name)));
        return grouped;
    }, [functions]);

    const sortedDomains = useMemo(() => [...domains].sort((a, b) => a.element_name.localeCompare(b.element_name)), [domains]);

    const allNodeIds = useMemo(() => {
        const ids: string[] = [];
        sortedDomains.forEach((domain) => {
            ids.push(`domain-${domain.recid}`);
            (subdomainsByDomain.get(String((domain as any).element_guid)) || []).forEach((subdomain) => {
                ids.push(`subdomain-${subdomain.recid}`);
                (functionsBySubdomain.get(String((subdomain as any).element_guid)) || []).forEach((fn) => {
                    ids.push(`function-${fn.recid}`);

                    if (!fn.element_request_model_guid && !fn.element_response_model_guid) {
                        ids.push(`function-${fn.recid}-no-models`);
                    }

                    if (fn.element_request_model_guid) {
                        const requestModelNodeId = `function-${fn.recid}-req-model-${fn.element_request_model_guid}`;
                        ids.push(requestModelNodeId);
                        (fieldsByModel.get(fn.element_request_model_guid) || []).forEach((field) => {
                            ids.push(`field-${field.recid}-under-${fn.element_request_model_guid}-fn-${fn.recid}`);
                        });
                    }

                    if (fn.element_response_model_guid) {
                        const responseModelNodeId = `function-${fn.recid}-resp-model-${fn.element_response_model_guid}`;
                        ids.push(responseModelNodeId);
                        (fieldsByModel.get(fn.element_response_model_guid) || []).forEach((field) => {
                            ids.push(`field-${field.recid}-under-${fn.element_response_model_guid}-fn-${fn.recid}`);
                        });
                    }
                });
            });
        });
        return ids;
    }, [fieldsByModel, functionsBySubdomain, sortedDomains, subdomainsByDomain]);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>RPC Dispatch Tree</PageTitle>

            <Paper sx={{ p: 2, mb: 2 }}>
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }}>
                    <Box>
                        <Typography variant="h6">RPC Dispatch Tree</Typography>
                        <Typography variant="body2" color="text.secondary">
                            {domains.length} domains · {subdomains.length} subdomains · {functions.length} functions · {models.length} models · {fields.length} fields
                        </Typography>
                    </Box>
                    <Stack direction="row" spacing={1}>
                        <Button variant="outlined" onClick={() => void loadAll()} disabled={loading}>
                            Refresh
                        </Button>
                        <Button variant="outlined" onClick={() => setExpandedItems(allNodeIds)} disabled={loading || allNodeIds.length === 0}>
                            Expand All
                        </Button>
                        <Button variant="outlined" onClick={() => setExpandedItems([])} disabled={loading || allNodeIds.length === 0}>
                            Collapse All
                        </Button>
                    </Stack>
                </Stack>
            </Paper>

            <Paper sx={{ p: 1 }}>
                <SimpleTreeView expandedItems={expandedItems} onExpandedItemsChange={(_: SyntheticEvent | null, itemIds: string[]) => setExpandedItems(itemIds)}>
                    {sortedDomains.map((domain) => {
                        const domainId = `domain-${domain.recid}`;
                        const childSubdomains = subdomainsByDomain.get(String((domain as any).element_guid)) || [];
                        return (
                            <TreeItem
                                key={domainId}
                                itemId={domainId}
                                sx={treeItemSx}
                                label={
                                    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                        <Typography variant="body2" fontWeight={600}>{domain.element_name}</Typography>
                                        <Chip size="small" variant="outlined" label={domain.element_required_role || 'No role'} />
                                        {domain.element_is_auth_exempt && <Chip size="small" color="info" label="Auth Exempt" />}
                                        {domain.element_is_public && <Chip size="small" color="warning" label="Public" />}
                                        {domain.element_is_discord && <Chip size="small" color="secondary" label="Discord" />}
                                    </Stack>
                                }
                            >
                                {childSubdomains.map((subdomain) => {
                                    const subdomainId = `subdomain-${subdomain.recid}`;
                                    const childFunctions = functionsBySubdomain.get(String((subdomain as any).element_guid)) || [];
                                    return (
                                        <TreeItem
                                            key={subdomainId}
                                            itemId={subdomainId}
                                            sx={treeItemSx}
                                            label={
                                                <Stack direction="row" spacing={1} alignItems="center">
                                                    <Typography variant="body2" fontWeight={500}>{subdomain.element_name}</Typography>
                                                    <Typography variant="caption" color="text.secondary">({childFunctions.length} functions)</Typography>
                                                </Stack>
                                            }
                                        >
                                            {childFunctions.map((fn) => {
                                                const functionId = `function-${fn.recid}`;
                                                const requestModel = fn.element_request_model_guid
                                                    ? modelNameByGuid.get(fn.element_request_model_guid) ?? `Model#${fn.element_request_model_guid}`
                                                    : null;
                                                const responseModel = fn.element_response_model_guid
                                                    ? modelNameByGuid.get(fn.element_response_model_guid) ?? `Model#${fn.element_response_model_guid}`
                                                    : null;

                                                return (
                                                    <TreeItem
                                                        key={functionId}
                                                        itemId={functionId}
                                                        sx={treeItemSx}
                                                        label={
                                                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                                                <Typography variant="body2">{fn.element_name}:{fn.element_version}</Typography>
                                                                <Typography variant="caption" color="text.secondary">→ {fn.element_module_attr}.{fn.element_method_name}</Typography>
                                                                {statusChip(fn.element_status)}
                                                            </Stack>
                                                        }
                                                    >
                                                        {!requestModel && !responseModel && (
                                                            <TreeItem
                                                                itemId={`function-${fn.recid}-no-models`}
                                                                sx={treeItemSx}
                                                                label={<Typography variant="body2" color="text.secondary">(no models)</Typography>}
                                                            />
                                                        )}

                                                        {requestModel && fn.element_request_model_guid && (
                                                            <TreeItem
                                                                itemId={`function-${fn.recid}-req-model-${fn.element_request_model_guid}`}
                                                                sx={treeItemSx}
                                                                label={<Typography variant="body2">📥 Request: {requestModel}</Typography>}
                                                            >
                                                                {(fieldsByModel.get(fn.element_request_model_guid) || []).map((field) => (
                                                                    <TreeItem
                                                                        key={`field-${field.recid}-under-${fn.element_request_model_guid}-fn-${fn.recid}`}
                                                                        itemId={`field-${field.recid}-under-${fn.element_request_model_guid}-fn-${fn.recid}`}
                                                                        sx={treeItemSx}
                                                                        label={
                                                                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                                                                <Typography variant="body2">{field.element_name}: {describeFieldType(field, modelNameByGuid, edtMappings)}</Typography>
                                                                                {field.element_is_nullable && <Chip size="small" label="?" />}
                                                                                {field.element_is_list && <Chip size="small" label="[]" />}
                                                                                {field.element_is_dict && <Chip size="small" label="{}" />}
                                                                                {field.element_default_value && (
                                                                                    <Typography variant="caption" color="text.secondary">= {field.element_default_value}</Typography>
                                                                                )}
                                                                            </Stack>
                                                                        }
                                                                    />
                                                                ))}
                                                            </TreeItem>
                                                        )}

                                                        {responseModel && fn.element_response_model_guid && (
                                                            <TreeItem
                                                                itemId={`function-${fn.recid}-resp-model-${fn.element_response_model_guid}`}
                                                                sx={treeItemSx}
                                                                label={<Typography variant="body2">📤 Response: {responseModel}</Typography>}
                                                            >
                                                                {(fieldsByModel.get(fn.element_response_model_guid) || []).map((field) => (
                                                                    <TreeItem
                                                                        key={`field-${field.recid}-under-${fn.element_response_model_guid}-fn-${fn.recid}`}
                                                                        itemId={`field-${field.recid}-under-${fn.element_response_model_guid}-fn-${fn.recid}`}
                                                                        sx={treeItemSx}
                                                                        label={
                                                                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                                                                                <Typography variant="body2">{field.element_name}: {describeFieldType(field, modelNameByGuid, edtMappings)}</Typography>
                                                                                {field.element_is_nullable && <Chip size="small" label="?" />}
                                                                                {field.element_is_list && <Chip size="small" label="[]" />}
                                                                                {field.element_is_dict && <Chip size="small" label="{}" />}
                                                                                {field.element_default_value && (
                                                                                    <Typography variant="caption" color="text.secondary">= {field.element_default_value}</Typography>
                                                                                )}
                                                                            </Stack>
                                                                        }
                                                                    />
                                                                ))}
                                                            </TreeItem>
                                                        )}
                                                    </TreeItem>
                                                );
                                            })}
                                        </TreeItem>
                                    );
                                })}
                            </TreeItem>
                        );
                    })}
                </SimpleTreeView>
            </Paper>
        </Box>
    );
};

export default ServiceRpcDispatchTreePage;
