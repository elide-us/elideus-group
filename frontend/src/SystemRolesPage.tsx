import { useEffect, useState } from 'react';
import { Box, Table, TableHead, TableRow, TableCell, TableBody, IconButton, TextField } from '@mui/material';
import ColumnHeader from './shared/ColumnHeader';
import { PageTitle } from './shared/PageTitle';
import { Delete, Add } from '@mui/icons-material';
import type { RoleItem, SystemRolesList2 } from './shared/RpcModels';
import { fetchList2 as fetchList, fetchSet2 as fetchSet, fetchDelete2 as fetchDelete } from './rpc/system/roles';
import EditBox from './shared/EditBox';
import Notification from './shared/Notification';

const SystemRolesPage = (): JSX.Element => {
    const [roles, setRoles] = useState<RoleItem[]>([]);
    const [newRole, setNewRole] = useState<RoleItem>({ name: '', display: '', bit: 0 });
    const [notification, setNotification] = useState(false);
    const handleNotificationClose = (): void => { setNotification(false); };

    const load = async (): Promise<void> => {
        try {
            const res: SystemRolesList2 = await fetchList();
            setRoles(res.roles.sort((a, b) => a.bit - b.bit));
        } catch {
            setRoles([]);
        }
    };

    useEffect(() => {
        void load();
    }, []);

    const updateRole = async (index: number, field: keyof RoleItem, value: string | number): Promise<void> => {
        const updated = [...roles];
        (updated[index] as any)[field] = field === 'bit' ? Number(value) : value;
        setRoles(updated);
        await fetchSet(updated[index]);
        void load();
        setNotification(true);
    };

    const handleDelete = async (name: string): Promise<void> => {
        await fetchDelete({ name });
        void load();
        setNotification(true);
    };

    const handleAdd = async (): Promise<void> => {
        if (!newRole.name) return;
        await fetchSet(newRole);
        setNewRole({ name: '', display: '', bit: 0 });
        void load();
        setNotification(true);
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='System Roles' />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <ColumnHeader title='Role' />
                        <ColumnHeader title='Display' />
                        <ColumnHeader title='Bit' />
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {roles.map((r, idx) => (
                        <TableRow key={r.name}>
                            <TableCell>
                                <EditBox value={r.name} onCommit={(val: string | number) => updateRole(idx, 'name', String(val))} />
                            </TableCell>
                            <TableCell>
                                <EditBox value={r.display} onCommit={(val: string | number) => updateRole(idx, 'display', String(val))} />
                            </TableCell>
                            <TableCell>
                                <EditBox type='number' inputProps={{ min: 0, max: 62 }} value={r.bit} onCommit={(val: string | number) => updateRole(idx, 'bit', Number(val))} />
                            </TableCell>
                            <TableCell>
                                <IconButton onClick={() => handleDelete(r.name)}><Delete /></IconButton>
                            </TableCell>
                        </TableRow>
                    ))}
                    <TableRow>
                        <TableCell>
                            <TextField value={newRole.name} onChange={e => setNewRole({ ...newRole, name: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField value={newRole.display} onChange={e => setNewRole({ ...newRole, display: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField type='number' inputProps={{ min: 0, max: 62 }} value={newRole.bit} onChange={e => setNewRole({ ...newRole, bit: Number(e.target.value) })} />
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

export default SystemRolesPage;
