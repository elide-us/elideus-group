import { useEffect, useState } from 'react';
import { Box, Divider, Table, TableHead, TableRow, TableCell, TableBody, IconButton, Typography, TextField } from '@mui/material';
import { Delete, Add } from '@mui/icons-material';
import type { ConfigItem, SystemConfigList1 } from './shared/RpcModels';
import { fetchList, fetchSet, fetchDelete } from './rpc/system/config';
import EditBox from './shared/EditBox';
import Notification from './shared/Notification';

const SystemConfigPage = (): JSX.Element => {
    const [items, setItems] = useState<ConfigItem[]>([]);
    const [newItem, setNewItem] = useState<ConfigItem>({ key: '', value: '' });
    const [notification, setNotification] = useState(false);
    const handleNotificationClose = (): void => { setNotification(false); };

    const load = async (): Promise<void> => {
        try {
            const res: SystemConfigList1 = await fetchList();
            setItems(res.items);
        } catch {
            setItems([]);
        }
    };

    useEffect(() => { void load(); }, []);

    const updateItem = async (index: number, field: keyof ConfigItem, value: string): Promise<void> => {
        const updated = [...items];
        (updated[index] as any)[field] = value;
        setItems(updated);
        await fetchSet(updated[index]);
        setNotification(true);
    };

    const handleDelete = async (key: string): Promise<void> => {
        await fetchDelete({ key });
        void load();
        setNotification(true);
    };

    const handleAdd = async (): Promise<void> => {
        if (!newItem.key) return;
        await fetchSet(newItem);
        setNewItem({ key: '', value: '' });
        void load();
        setNotification(true);
    };

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant='h5'>System Configuration</Typography>
            <Divider sx={{ mb: 2 }} />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <TableCell>Key</TableCell>
                        <TableCell>Value</TableCell>
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {items.map((i, idx) => (
                        <TableRow key={i.key}>
                            <TableCell>
                                <EditBox value={i.key} onCommit={(val: string | number) => updateItem(idx, 'key', String(val))} />
                            </TableCell>
                            <TableCell>
                                <EditBox value={i.value} onCommit={(val: string | number) => updateItem(idx, 'value', String(val))} />
                            </TableCell>
                            <TableCell>
                                <IconButton onClick={() => handleDelete(i.key)}><Delete /></IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                    <TableRow>
                        <TableCell>
                            <TextField value={newItem.key} onChange={e => setNewItem({ ...newItem, key: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField value={newItem.value} onChange={e => setNewItem({ ...newItem, value: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <IconButton onClick={handleAdd}><Add /></IconButton>
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity='success'
                message='Saved'
            />
        </Box>
    );
};

export default SystemConfigPage;
