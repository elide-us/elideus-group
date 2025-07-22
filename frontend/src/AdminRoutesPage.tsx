import { useEffect, useState } from 'react';
import { Table, TableHead, TableRow, TableCell, TableBody, TextField, IconButton, Stack, List, ListItemButton, ListItemText, Typography } from '@mui/material';
import { Delete, Add, ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import type { AdminRouteItem, AdminRoutesList1, AdminUserRoles1 } from './shared/RpcModels';
import { fetchList as fetchRoutes, fetchSet, fetchDelete } from './rpc/admin/routes';
import { fetchListRoles } from './rpc/admin/users';

const MAX_HEIGHT = 120;

const AdminRoutesPage = (): JSX.Element => {
    const [routes, setRoutes] = useState<AdminRouteItem[]>([]);
    const [roleNames, setRoleNames] = useState<string[]>([]);
    const [selectedLeft, setSelectedLeft] = useState<Record<number, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<number, string>>({});
    const [newRoute, setNewRoute] = useState<AdminRouteItem>({ path: '', name: '', icon: '', sequence: 0, requiredRoles: [] });
    const [newLeft, setNewLeft] = useState<string | null>(null);
    const [newRight, setNewRight] = useState<string | null>(null);

    const load = async (): Promise<void> => {
        try {
            const res: AdminRoutesList1 = await fetchRoutes();
            setRoutes(res.routes.sort((a, b) => a.sequence - b.sequence));
        } catch {
            setRoutes([]);
        }
        try {
            const roles: AdminUserRoles1 = await fetchListRoles();
            setRoleNames(roles.roles);
        } catch {
            setRoleNames([]);
        }
    };

    useEffect(() => { void load(); }, []);

    const updateRoute = async (index: number, field: keyof AdminRouteItem, value: any): Promise<void> => {
        const updated = [...routes];
        (updated[index] as any)[field] = value;
        setRoutes(updated);
        await fetchSet(updated[index]);
        void load();
    };

    const moveRight = async (idx: number): Promise<void> => {
        const role = selectedLeft[idx];
        if (!role) return;
        const updatedRoles = [...routes[idx].requiredRoles, role];
        setSelectedLeft({ ...selectedLeft, [idx]: '' });
        await updateRoute(idx, 'requiredRoles', updatedRoles);
    };

    const moveLeft = async (idx: number): Promise<void> => {
        const role = selectedRight[idx];
        if (!role) return;
        const updatedRoles = routes[idx].requiredRoles.filter(r => r !== role);
        setSelectedRight({ ...selectedRight, [idx]: '' });
        await updateRoute(idx, 'requiredRoles', updatedRoles);
    };

    const handleDelete = async (path: string): Promise<void> => {
        await fetchDelete({ path });
        void load();
    };

    const addMoveRight = (role: string | null): void => {
        if (!role) return;
        setNewRoute({ ...newRoute, requiredRoles: [...newRoute.requiredRoles, role] });
        setNewLeft(null);
    };

    const addMoveLeft = (role: string | null): void => {
        if (!role) return;
        setNewRoute({ ...newRoute, requiredRoles: newRoute.requiredRoles.filter(r => r !== role) });
        setNewRight(null);
    };

    const handleAdd = async (): Promise<void> => {
        if (!newRoute.path) return;
        await fetchSet(newRoute);
        setNewRoute({ path: '', name: '', icon: '', sequence: 0, requiredRoles: [] });
        setNewLeft(null);
        setNewRight(null);
        void load();
    };

    return (
        <>
            <Typography variant='h5' sx={{ mb: 2 }}>Route Management</Typography>
            <Table>
                <TableHead>
                    <TableRow>
                        <TableCell>Path</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Icon</TableCell>
                        <TableCell>Sequence</TableCell>
                        <TableCell>Roles</TableCell>
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {routes.map((r, idx) => {
                        const available = roleNames.filter(n => !r.requiredRoles.includes(n));
                        return (
                            <TableRow key={r.path}>
                                <TableCell>
                                    <TextField value={r.path} onChange={e => updateRoute(idx, 'path', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <TextField value={r.name} onChange={e => updateRoute(idx, 'name', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <TextField value={r.icon} onChange={e => updateRoute(idx, 'icon', e.target.value)} />
                                </TableCell>
                                <TableCell>
                                    <TextField type='number' value={r.sequence} onChange={e => updateRoute(idx, 'sequence', Number(e.target.value))} />
                                </TableCell>
                                <TableCell>
                                    <Stack direction='row' spacing={1}>
                                        <List sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: 'auto', border: 1 }}>
                                            {available.map(role => (
                                                <ListItemButton key={role} selected={selectedLeft[idx] === role} onClick={() => setSelectedLeft({ ...selectedLeft, [idx]: role })}>
                                                    <ListItemText primary={role} />
                                                </ListItemButton>
                                            ))}
                                        </List>
                                        <Stack spacing={1} justifyContent='center'>
                                            <IconButton onClick={() => void moveRight(idx)}><ArrowForwardIos /></IconButton>
                                            <IconButton onClick={() => void moveLeft(idx)}><ArrowBackIos /></IconButton>
                                        </Stack>
                                        <List sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: 'auto', border: 1 }}>
                                            {r.requiredRoles.map(role => (
                                                <ListItemButton key={role} selected={selectedRight[idx] === role} onClick={() => setSelectedRight({ ...selectedRight, [idx]: role })}>
                                                    <ListItemText primary={role} />
                                                </ListItemButton>
                                            ))}
                                        </List>
                                    </Stack>
                                </TableCell>
                                <TableCell>
                                    <IconButton onClick={() => handleDelete(r.path)}><Delete /></IconButton>
                                </TableCell>
                            </TableRow>
                        );
                    })}
                    <TableRow>
                        <TableCell>
                            <TextField value={newRoute.path} onChange={e => setNewRoute({ ...newRoute, path: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField value={newRoute.name} onChange={e => setNewRoute({ ...newRoute, name: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField value={newRoute.icon} onChange={e => setNewRoute({ ...newRoute, icon: e.target.value })} />
                        </TableCell>
                        <TableCell>
                            <TextField type='number' value={newRoute.sequence} onChange={e => setNewRoute({ ...newRoute, sequence: Number(e.target.value) })} />
                        </TableCell>
                        <TableCell>
                            <Stack direction='row' spacing={1}>
                                <List sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: 'auto', border: 1 }}>
                                    {roleNames.filter(r => !newRoute.requiredRoles.includes(r)).map(role => (
                                        <ListItemButton key={role} selected={newLeft === role} onClick={() => setNewLeft(role)}>
                                            <ListItemText primary={role} />
                                        </ListItemButton>
                                    ))}
                                </List>
                                <Stack spacing={1} justifyContent='center'>
                                    <IconButton onClick={() => addMoveRight(newLeft)}><ArrowForwardIos /></IconButton>
                                    <IconButton onClick={() => addMoveLeft(newRight)}><ArrowBackIos /></IconButton>
                                </Stack>
                                <List sx={{ width: 120, maxHeight: MAX_HEIGHT, overflow: 'auto', border: 1 }}>
                                    {newRoute.requiredRoles.map(role => (
                                        <ListItemButton key={role} selected={newRight === role} onClick={() => setNewRight(role)}>
                                            <ListItemText primary={role} />
                                        </ListItemButton>
                                    ))}
                                </List>
                            </Stack>
                        </TableCell>
                        <TableCell>
                            <IconButton onClick={handleAdd}><Add /></IconButton>
                        </TableCell>
                    </TableRow>
                </TableBody>
            </Table>
        </>
    );
};

export default AdminRoutesPage;
