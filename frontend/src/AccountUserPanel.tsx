import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Stack, Button, List, ListItemButton, ListItemText, IconButton, Typography, Avatar } from '@mui/material';
import { PageTitle } from './shared/PageTitle';
import { ArrowForwardIos, ArrowBackIos, CheckCircle, Cancel } from '@mui/icons-material';
import type { AccountUserRoles1, AccountUserProfile1, RoleItem } from './shared/RpcModels';
import { fetchRoles, fetchSetRoles, fetchProfile, fetchSetCredits, fetchEnableStorage, fetchSetDisplayName } from './rpc/account/users';
import EditBox from './shared/EditBox';
import Notification from './shared/Notification';
import { fetchList as fetchRoleList } from './rpc/account/roles';

const AccountUserPanel = (): JSX.Element => {
    const { guid } = useParams();
    const [assigned, setAssigned] = useState<string[]>([]);
    const [available, setAvailable] = useState<string[]>([]);
    const [profile, setProfile] = useState<AccountUserProfile1 | null>(null);
    const [notification, setNotification] = useState(false);
    const [username, setUsername] = useState<string>('');
    const [roles, setRoles] = useState<RoleItem[]>([]);
    const [credits, setCredits] = useState<number>(0);
    const [storageEnabled, setStorageEnabled] = useState<boolean>(false);
    const [storageUsed, setStorageUsed] = useState<number>(0);
    const [selectedLeft, setSelectedLeft] = useState<string | null>(null);
    const [selectedRight, setSelectedRight] = useState<string | null>(null);

    useEffect(() => {
        void (async () => {
            if (!guid) return;
            try {
            const userRoles: AccountUserRoles1 = await fetchRoles({ userGuid: guid });
                const roleList = await fetchRoleList();
                const prof: AccountUserProfile1 = await fetchProfile({ userGuid: guid });
                setRoles(roleList.roles);
                setAssigned(userRoles.roles);
                setAvailable(roleList.roles.map(r => r.name).filter(r => !userRoles.roles.includes(r)));
                setProfile(prof);
                setUsername(prof.username);
                setCredits(prof.credits ?? 0);
                setStorageEnabled(prof.storageEnabled ?? false);
                setStorageUsed(prof.storageUsed ?? 0);
            } catch {
                setAssigned([]);
                setAvailable([]);
                setProfile(null);
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

    const handleEnableStorage = async (): Promise<void> => {
        if (!guid) return;
        const prof = await fetchEnableStorage({ userGuid: guid });
        setProfile(prof);
        setStorageEnabled(prof.storageEnabled ?? false);
        setStorageUsed(prof.storageUsed ?? 0);
    };

    const commitName = async (val: string | number): Promise<void> => {
        if (!guid) return;
        const updated = await fetchSetDisplayName({ userGuid: guid, displayName: String(val) });
        setProfile(updated);
        setUsername(updated.username);
    };

    const handleNotificationClose = (): void => { setNotification(false); };

    const handleSave = async (): Promise<void> => {
        if (!guid) return;
        await fetchSetRoles({ userGuid: guid, roles: assigned });
        await fetchSetCredits({ userGuid: guid, credits });
        setNotification(true);
    };

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 2, p: 2 }}>
            <PageTitle title='User Management' />
            {profile && (
                <Stack spacing={2} sx={{ mb: 4, alignItems: 'center' }}>
                    <PageTitle title='User Profile' />
                    <Avatar
                        src={profile.profilePicture ? `data:image/png;base64,${profile.profilePicture}` : undefined}
                        sx={{ width: 80, height: 80 }}
                    />
                    <EditBox label='Display Name' value={username} onCommit={commitName} />
                    <Typography>Email: {profile.email}</Typography>
                    <EditBox label='Credits' type='number' value={credits} onCommit={(val: string | number) => setCredits(Number(val))} />
                    <Stack direction='row' spacing={1} alignItems='center'>
                        <Typography>Storage Enabled:</Typography>
                        {storageEnabled ? <CheckCircle color='success' /> : <IconButton onClick={handleEnableStorage}><Cancel color='error' /></IconButton>}
                    </Stack>
                    <Typography>Storage Used: {storageUsed} B</Typography>
                </Stack>
            )}
            <Stack direction='row' spacing={2}>
                <List sx={{ width: 200, border: 1 }}>
                    {available.map((r) => (
                        <ListItemButton key={r} selected={selectedLeft === r} onClick={() => setSelectedLeft(r)}>
                            <ListItemText primary={roles.find(ro => ro.name === r)?.display ?? r} />
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
                            <ListItemText primary={roles.find(ro => ro.name === r)?.display ?? r} />
                        </ListItemButton>
                    ))}
                </List>
            </Stack>
            <Box sx={{ ml: 2 }}>
                <Button variant='contained' onClick={handleSave}>Save</Button>
            </Box>
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity='success'
                message='Saved'
            />
        </Box>
    );
};

export default AccountUserPanel;
