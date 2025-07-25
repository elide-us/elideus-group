import React, { useContext, useState, useEffect, useRef } from 'react';
import { Box, Typography, FormControlLabel, Switch, Avatar, Button, Stack, RadioGroup, Radio } from '@mui/material';
import { PageTitle } from './shared/PageTitle';
import UserContext from './shared/UserContext';
import { fetchSetDisplayName } from './rpc/frontend/user';
import EditBox, { EditBoxHandle } from './shared/EditBox';
import Notification from './shared/Notification';
import { fetchList as fetchRoleList } from './rpc/system/roles';
import type { SystemRolesList1 } from './shared/RpcModels';

const UserPage = (): JSX.Element => {
    const { userData, setUserData } = useContext(UserContext);
    const [displayEmail, setDisplayEmail] = useState<boolean>(userData?.displayEmail ?? false);
    const [displayName, setDisplayName] = useState<string>(userData?.username ?? '');
    const [dirty, setDirty] = useState<boolean>(false);
    const [provider, setProvider] = useState<string>(userData?.defaultProvider ?? 'microsoft');
    const [roleMap, setRoleMap] = useState<Record<string, string>>({});
    const [notification, setNotification] = useState(false);
    const nameRef = useRef<EditBoxHandle>(null);

    const storageUsedMb = ((userData?.storageUsed ?? 0) / (1024 * 1024)).toFixed(2);

    const handleNotificationClose = (): void => { setNotification(false); };

    useEffect(() => {
        void (async () => {
            try {
                const res: SystemRolesList1 = await fetchRoleList();
                const map: Record<string, string> = {};
                res.roles.forEach(r => { map[r.name] = r.display; });
                setRoleMap(map);
            } catch {
                setRoleMap({});
            }
        })();
    }, []);

    useEffect(() => {
        if (!userData) return;
        setDisplayName(userData.username);
        setDisplayEmail(userData.displayEmail);
        setProvider(userData.defaultProvider);
    }, [userData]);

    const handleToggle = (): void => {
        const val = !displayEmail;
        setDisplayEmail(val);
        setDirty(true);
    };

    const handleProviderChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setProvider(e.target.value);
        setDirty(true);
    };

    const handleCancel = (): void => {
        if (userData) {
            setDisplayName(userData.username);
            setDisplayEmail(userData.displayEmail);
            setProvider(userData.defaultProvider);
        }
        setDirty(false);
    };

    const handleApply = async (): Promise<void> => {
        if (!userData) return;
        await nameRef.current?.commit();
        const updated = await fetchSetDisplayName({ bearerToken: userData.bearerToken, displayName });
        setUserData({ ...userData, username: updated.username, displayEmail });
        setDirty(false);
        setNotification(true);
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
            <Box sx={{ maxWidth: 400, width: '100%' }}>
                <Stack
                spacing={2}
                sx={{ mt: 2, display: 'flex', alignItems: 'flex-end', textAlign: 'right' }}
                >
                <PageTitle title='User Profile' />

                {userData && (
                    <Stack spacing={2} sx={{ mt: 2, alignItems: 'flex-end', width: '100%' }}>
                    <Avatar
                        src={userData.profilePicture ?? undefined}
                        sx={{ width: 80, height: 80 }}
                    />

                    <EditBox
                        ref={nameRef}
                        label='Display Name'
                        value={displayName}
                        onCommit={(val: string | number) => { setDisplayName(String(val)); setDirty(true); }}
                        manual
                        fullWidth
                        slotProps={{ input: { style: { textAlign: 'right' } } }}
                    />

                    <Typography>Credits: {userData.credits ?? 0}</Typography>
                    <Typography>Storage Enabled: {userData.storageEnabled ? 'Yes' : 'No'}</Typography>
                    <Typography>Storage Used: {storageUsedMb} MB</Typography>
                    <Typography>Email: {userData.email}</Typography>
                    <Typography>
                        Roles: {userData.roles.map(r => roleMap[r] ?? r).join(', ')}
                    </Typography>

                    <RadioGroup
                        value={provider}
                        onChange={handleProviderChange}
                        sx={{ alignItems: 'flex-end' }}
                    >
                        <FormControlLabel value='microsoft' control={<Radio />} label='Microsoft' />
                        <FormControlLabel value='google' control={<Radio />} label='Google' disabled />
                        <FormControlLabel value='discord' control={<Radio />} label='Discord' disabled />
                        <FormControlLabel value='apple' control={<Radio />} label='Apple' disabled />
                    </RadioGroup>

                    <FormControlLabel
                        control={<Switch checked={displayEmail} onChange={handleToggle} />}
                        label='Display email publicly'
                        labelPlacement='start'
                        sx={{ alignSelf: 'flex-end' }}
                    />

                    <Stack
                        direction='row'
                        spacing={2}
                        sx={{ justifyContent: 'flex-end', width: '100%' }}
                    >
                        <Button variant='contained' onClick={handleApply} disabled={!dirty}>
                        Apply
                        </Button>
                        <Button variant='outlined' onClick={handleCancel} disabled={!dirty}>
                        Cancel
                        </Button>
                        <Button variant='contained' color='error'>
                        Delete
                        </Button>
                    </Stack>
                    </Stack>
                )}
                </Stack>
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

export default UserPage;
