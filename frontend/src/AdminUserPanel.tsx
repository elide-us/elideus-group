import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton } from '@mui/material';
import { ArrowForwardIos, ArrowBackIos } from '@mui/icons-material';
import type { AdminUserRoles1 } from './shared/RpcModels';
import { fetchRoles, fetchSetRoles, fetchListRoles } from './rpc/admin/users';

const AdminUserPanel = (): JSX.Element => {
    const { guid } = useParams();
    const [assigned, setAssigned] = useState<string[]>([]);
    const [available, setAvailable] = useState<string[]>([]);
    const [selectedLeft, setSelectedLeft] = useState<string | null>(null);
    const [selectedRight, setSelectedRight] = useState<string | null>(null);

    useEffect(() => {
        void (async () => {
            if (!guid) return;
            try {
                const roles: AdminUserRoles1 = await fetchRoles({ userGuid: guid });
                const all: AdminUserRoles1 = await fetchListRoles();
                setAssigned(roles.roles);
                setAvailable(all.roles.filter(r => !roles.roles.includes(r)));
            } catch {
                setAssigned([]);
                setAvailable([]);
            }
        })();
    }, [guid]);

    const moveRight = (): void => {
        if (!selectedLeft) return;
        setAssigned([...assigned, selectedLeft]);
        setAvailable(available.filter(r => r !== selectedLeft));
        setSelectedLeft(null);
    };

    const moveLeft = (): void => {
        if (!selectedRight) return;
        setAvailable([...available, selectedRight]);
        setAssigned(assigned.filter(r => r !== selectedRight));
        setSelectedRight(null);
    };

    const handleSave = async (): Promise<void> => {
        if (!guid) return;
        await fetchSetRoles({ userGuid: guid, roles: assigned });
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <Stack direction='row' spacing={2}>
                <List sx={{ width: 200, border: 1 }}>
                    {available.map((r) => (
                        <ListItemButton key={r} selected={selectedLeft === r} onClick={() => setSelectedLeft(r)}>
                            <ListItemText primary={r} />
                        </ListItemButton>
                    ))}
                </List>
                <Stack spacing={1} justifyContent='center'>
                    <IconButton onClick={moveRight}><ArrowForwardIos /></IconButton>
                    <IconButton onClick={moveLeft}><ArrowBackIos /></IconButton>
                </Stack>
                <List sx={{ width: 200, border: 1 }}>
                    {assigned.map((r) => (
                        <ListItemButton key={r} selected={selectedRight === r} onClick={() => setSelectedRight(r)}>
                            <ListItemText primary={r} />
                        </ListItemButton>
                    ))}
                </List>
            </Stack>
            <Box sx={{ ml: 2 }}>
                <Button variant='contained' onClick={handleSave}>Save</Button>
            </Box>
        </Box>
    );
};

export default AdminUserPanel;
