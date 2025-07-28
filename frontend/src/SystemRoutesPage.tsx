import { useEffect, useState } from 'react';
import { Box, Table, TableHead, TableRow, TableCell, TableBody, IconButton, Stack, List, ListItemButton, ListItemText } from '@mui/material';
import ColumnHeader from './shared/ColumnHeader';
import { PageTitle } from './shared/PageTitle';
import { Delete, Add, ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import type { SystemRouteItem, SystemRoutesList2, SystemUserRoles1 } from './shared/RpcModels';
import { fetchList2 as fetchRoutes, fetchSet2 as fetchSet, fetchDelete2 as fetchDelete } from './rpc/system/routes';
import EditBox from './shared/EditBox';
import Notification from './shared/Notification';
import { fetchListRoles2 as fetchListRoles } from './rpc/system/users';

const MAX_HEIGHT = 120;

const SystemRoutesPage = (): JSX.Element => {
    const [routes, setRoutes] = useState<SystemRouteItem[]>([]);
    const [roleNames, setRoleNames] = useState<string[]>([]);
    const [selectedLeft, setSelectedLeft] = useState<Record<number, string>>({});
    const [selectedRight, setSelectedRight] = useState<Record<number, string>>({});
    const [newRoute, setNewRoute] = useState<SystemRouteItem>({ path: '', name: '', icon: '', sequence: 0, requiredRoles: [] });
    const [newLeft, setNewLeft] = useState<string | null>(null);
    const [newRight, setNewRight] = useState<string | null>(null);
    const [notification, setNotification] = useState(false);
    const handleNotificationClose = (): void => { setNotification(false); };

    const load = async (): Promise<void> => {
        try {
            const res: SystemRoutesList2 = await fetchRoutes();
            setRoutes(res.routes.sort((a, b) => a.sequence - b.sequence));
        } catch {
            setRoutes([]);
        }
        try {
            const roles: SystemUserRoles1 = await fetchListRoles();
            setRoleNames(roles.roles);
        } catch {
            setRoleNames([]);
        }
    };

    useEffect(() => { void load(); }, []);

    const updateRoute = async (index: number, field: keyof SystemRouteItem, value: any): Promise<void> => {
        const updated = [...routes];
        (updated[index] as any)[field] = value;
        setRoutes(updated);
        await fetchSet(updated[index]);
        void load();
        setNotification(true);
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
        setNotification(true);
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
        setNotification(true);
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='System Routes' />
            <Table size='small' sx={{ '& td, & th': { py: 0.5 } }}>
                <TableHead>
                    <TableRow>
                        <ColumnHeader title='Path' />
                        <ColumnHeader title='Name' />
                        <ColumnHeader title='Icon' />
                        <ColumnHeader title='Sequence' />
                        <ColumnHeader title='Roles' />
                        <TableCell />
                    </TableRow>
                </TableHead>
                <TableBody>
                    {routes.map((r, idx) => {
                        const available = roleNames.filter(n => !r.requiredRoles.includes(n));
                        return (
                            <TableRow key={r.path}>
                                <TableCell>
                                    <EditBox value={r.path} onCommit={(val: string | number) => updateRoute(idx, 'path', String(val))} />
                                </TableCell>
                                <TableCell>
                                    <EditBox value={r.name} onCommit={(val: string | number) => updateRoute(idx, 'name', String(val))} />
                                </TableCell>
                                <TableCell>
                                    <EditBox value={r.icon} onCommit={(val: string | number) => updateRoute(idx, 'icon', String(val))} />
                                </TableCell>
                                <TableCell>
                                    <EditBox type='number' value={r.sequence} onCommit={(val: string | number) => updateRoute(idx, 'sequence', Number(val))} />
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
                            <EditBox value={newRoute.path} onCommit={(val: string | number) => setNewRoute({ ...newRoute, path: String(val) })} />
                        </TableCell>
                        <TableCell>
                            <EditBox value={newRoute.name} onCommit={(val: string | number) => setNewRoute({ ...newRoute, name: String(val) })} />
                        </TableCell>
                        <TableCell>
                            <EditBox value={newRoute.icon} onCommit={(val: string | number) => setNewRoute({ ...newRoute, icon: String(val) })} />
                        </TableCell>
                        <TableCell>
                            <EditBox type='number' value={newRoute.sequence} onCommit={(val: string | number) => setNewRoute({ ...newRoute, sequence: Number(val) })} />
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
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity='success'
                message='Saved'
            />
        </Box>
    );
};

export default SystemRoutesPage;
