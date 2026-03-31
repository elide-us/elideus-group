import { Fragment, useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
    Box,
    Chip,
    Divider,
    IconButton,
    Link,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    TextField,
    Typography,
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';

import ColumnHeader from '../../components/ColumnHeader';
import EditBox from '../../components/EditBox';
import PageTitle from '../../components/PageTitle';
import type {
    ServicePagesCreatePage1,
    ServicePagesListPages1,
    ServicePagesPageItem1,
    ServicePagesUpdatePage1,
} from '../../shared/RpcModels';
import { fetchCreate, fetchDelete, fetchList, fetchUpdate } from '../../rpc/service/pages';

const DEFAULT_CONTENT = '# New Page\n\nContent goes here.';

const ServicePagesPage = (): JSX.Element => {
    const [pages, setPages] = useState<ServicePagesPageItem1[]>([]);
    const [forbidden, setForbidden] = useState(false);
    const [newPage, setNewPage] = useState<ServicePagesCreatePage1>({
        slug: '',
        title: '',
        content: DEFAULT_CONTENT,
        page_type: 'article',
        category: null,
        roles: 0,
        is_pinned: false,
        sequence: 0,
        summary: null,
    });

    const load = async (): Promise<void> => {
        try {
            const res: ServicePagesListPages1 = await fetchList();
            setPages([...res.pages].sort((a, b) => a.sequence - b.sequence));
            setForbidden(false);
        } catch (e: any) {
            if (e?.response?.status === 403) {
                setForbidden(true);
            } else {
                setPages([]);
            }
        }
    };

    useEffect(() => {
        void load();
    }, []);

    if (forbidden) {
        return (
            <Box sx={{ p: 2 }}>
                <Typography variant="h6">Forbidden</Typography>
            </Box>
        );
    }

    const updatePage = async (
        recid: number,
        field: keyof Pick<ServicePagesPageItem1, 'title' | 'page_type' | 'category' | 'sequence'>,
        value: string | number,
    ): Promise<void> => {
        const payload: Record<string, unknown> = { recid, [field]: value };
        if (field === 'category' && value === '') {
            payload[field] = null;
        }
        await fetchUpdate(payload as ServicePagesUpdatePage1);
        void load();
    };

    const handleDelete = async (recid: number): Promise<void> => {
        await fetchDelete({ recid });
        void load();
    };

    const handleAdd = async (): Promise<void> => {
        if (!newPage.slug.trim() || !newPage.title.trim() || !newPage.content.trim()) {
            return;
        }
        await fetchCreate({
            ...newPage,
            slug: newPage.slug.trim(),
            title: newPage.title.trim(),
        });
        setNewPage({
            slug: '',
            title: '',
            content: DEFAULT_CONTENT,
            page_type: 'article',
            category: null,
            roles: 0,
            is_pinned: false,
            sequence: 0,
            summary: null,
        });
        void load();
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle>Content Pages</PageTitle>
            <Divider sx={{ mb: 2 }} />
            <Table size="small" sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <ColumnHeader sx={{ width: '16%' }}>Slug</ColumnHeader>
                        <ColumnHeader sx={{ width: '18%' }}>Title</ColumnHeader>
                        <ColumnHeader sx={{ width: '12%' }}>Type</ColumnHeader>
                        <ColumnHeader sx={{ width: '14%' }}>Category</ColumnHeader>
                        <ColumnHeader sx={{ width: '10%' }}>Sequence</ColumnHeader>
                        <ColumnHeader sx={{ width: '10%' }}>Active</ColumnHeader>
                        <ColumnHeader sx={{ width: '10%' }}>Pinned</ColumnHeader>
                        <ColumnHeader sx={{ width: '10%' }}>Actions</ColumnHeader>
                    </TableRow>
                </TableHead>
                <TableBody>
                    {pages.map((page) => (
                        <TableRow key={page.recid}>
                            <TableCell>
                                <Link component={RouterLink} to={`/pages/${page.slug}`} underline="hover">
                                    {page.slug}
                                </Link>
                            </TableCell>
                            <TableCell>
                                <EditBox
                                    value={page.title}
                                    onCommit={(value) => updatePage(page.recid, 'title', value)}
                                    width="95%"
                                />
                            </TableCell>
                            <TableCell>
                                <EditBox
                                    value={page.page_type}
                                    onCommit={(value) => updatePage(page.recid, 'page_type', value)}
                                    width="95%"
                                />
                            </TableCell>
                            <TableCell>
                                <EditBox
                                    value={page.category ?? ''}
                                    onCommit={(value) => updatePage(page.recid, 'category', value)}
                                    width="95%"
                                />
                            </TableCell>
                            <TableCell>
                                <EditBox
                                    value={page.sequence}
                                    onCommit={(value) => updatePage(page.recid, 'sequence', value)}
                                    width="95%"
                                />
                            </TableCell>
                            <TableCell>
                                <Chip size="small" label={page.is_active ? 'Yes' : 'No'} color={page.is_active ? 'success' : 'default'} />
                            </TableCell>
                            <TableCell>
                                <Chip size="small" label={page.is_pinned ? 'Yes' : 'No'} color={page.is_pinned ? 'primary' : 'default'} />
                            </TableCell>
                            <TableCell>
                                <IconButton onClick={() => void handleDelete(page.recid)}>
                                    <Delete />
                                </IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                    <Fragment>
                        <TableRow>
                            <TableCell>
                                <TextField
                                    sx={{ width: '95%' }}
                                    value={newPage.slug}
                                    onChange={(e) => setNewPage({ ...newPage, slug: e.target.value })}
                                />
                            </TableCell>
                            <TableCell>
                                <TextField
                                    sx={{ width: '95%' }}
                                    value={newPage.title}
                                    onChange={(e) => setNewPage({ ...newPage, title: e.target.value })}
                                />
                            </TableCell>
                            <TableCell>
                                <TextField
                                    sx={{ width: '95%' }}
                                    value={newPage.page_type}
                                    onChange={(e) => setNewPage({ ...newPage, page_type: e.target.value })}
                                />
                            </TableCell>
                            <TableCell>
                                <TextField
                                    sx={{ width: '95%' }}
                                    value={newPage.category ?? ''}
                                    onChange={(e) =>
                                        setNewPage({
                                            ...newPage,
                                            category: e.target.value || null,
                                        })
                                    }
                                />
                            </TableCell>
                            <TableCell>
                                <TextField
                                    sx={{ width: '95%' }}
                                    type="number"
                                    value={newPage.sequence}
                                    onChange={(e) =>
                                        setNewPage({
                                            ...newPage,
                                            sequence: Number(e.target.value),
                                        })
                                    }
                                />
                            </TableCell>
                            <TableCell>
                                <Typography variant="body2" color="text.secondary">New</Typography>
                            </TableCell>
                            <TableCell>
                                <Typography variant="body2" color="text.secondary">No</Typography>
                            </TableCell>
                            <TableCell>
                                <IconButton onClick={() => void handleAdd()}>
                                    <Add />
                                </IconButton>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell colSpan={8}>
                                <TextField
                                    fullWidth
                                    label="Initial content"
                                    multiline
                                    minRows={3}
                                    value={newPage.content}
                                    onChange={(e) => setNewPage({ ...newPage, content: e.target.value })}
                                />
                            </TableCell>
                        </TableRow>
                    </Fragment>
                </TableBody>
            </Table>
        </Box>
    );
};

export default ServicePagesPage;
