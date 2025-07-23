import { useEffect, useState } from 'react';
import { Box, Divider, Table, TableHead, TableRow, TableCell, TableBody, TextField, IconButton, Typography } from '@mui/material';
import { Delete, Add } from '@mui/icons-material';
import type { RoleItem, SystemRolesList1 } from './shared/RpcModels';
import { fetchList, fetchSet, fetchDelete } from './rpc/system/roles';

const SystemRolesPage = (): JSX.Element => {
    const [roles, setRoles] = useState<RoleItem[]>([]);
    const [newRole, setNewRole] = useState<RoleItem>({ name: '', display: '', bit: 0 });

    const load = async (): Promise<void> => {
        try {
            const res: SystemRolesList1 = await fetchList();
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
    };

    const handleDelete = async (name: string): Promise<void> => {
        await fetchDelete({ name });
        void load();
    };

    const handleAdd = async (): Promise<void> => {
        if (!newRole.name) return;
        await fetchSet(newRole);
        setNewRole({ name: '', display: '', bit: 0 });
        void load();
    };

    return (
        <Box sx={{ p: 2 }}>
            <Typography variant='h5'>System Roles</Typography>
            <Divider sx={{ mb: 2 }} />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <TableCell>Role</TableCell>
                        <TableCell>Display</TableCell>
                        <TableCell>Bit</TableCell>
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {roles.map((r, idx) => (
                        <TableRow key={r.name}>
                            <TableCell>
                                <TextField value={r.name} onChange={e => updateRole(idx, 'name', e.target.value)} />
                            </TableCell>
                            <TableCell>
                                <TextField value={r.display} onChange={e => updateRole(idx, 'display', e.target.value)} />
                            </TableCell>
                            <TableCell>
                                <TextField type='number' inputProps={{ min: 0, max: 62 }} value={r.bit} onChange={e => updateRole(idx, 'bit', e.target.value)} />
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
        </Box>
    );
};

export default SystemRolesPage;
