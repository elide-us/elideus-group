import React, { useContext, useState } from 'react';
import { Box, Typography, FormControlLabel, Switch, Avatar, TextField, Button, Stack, RadioGroup, Radio } from '@mui/material';
import UserContext from './shared/UserContext';
import { fetchSetDisplayName } from './rpc/frontend/user';

const UserPage = (): JSX.Element => {
    const { userData, setUserData } = useContext(UserContext);
    const [displayEmail, setDisplayEmail] = useState<boolean>(userData?.displayEmail ?? false);
    const [displayName, setDisplayName] = useState<string>(userData?.username ?? '');
    const [dirty, setDirty] = useState<boolean>(false);
    const [provider, setProvider] = useState<string>(userData?.defaultProvider ?? 'microsoft');

    const handleToggle = (): void => {
        const val = !displayEmail;
        setDisplayEmail(val);
        setDirty(true);
    };

    const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
        setDisplayName(e.target.value);
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
        const updated = await fetchSetDisplayName({ bearerToken: userData.bearerToken, displayName });
        setUserData({ ...userData, username: updated.username, displayEmail });
        setDirty(false);
    };

    return (
        <Box sx={{ maxWidth: 400, width: '100%' }}>
            <Stack spacing={2} sx={{ mt: 2 }}>
                <Typography variant='h5' gutterBottom>User Profile</Typography>
                    {userData && (
                        <Stack spacing={2} sx={{ mt: 2 }}>
                            <Avatar src={userData.profilePicture ?? undefined} sx={{ width: 80, height: 80 }} />
                            <TextField label='Display Name' value={displayName} onChange={handleNameChange} fullWidth />
                            <Typography>Credits: {userData.credits ?? 0}</Typography>
                            <Typography>Storage Used: {userData.storageUsed ?? 0} MB</Typography>
                            <Typography>Email: {userData.email}</Typography>
                            <RadioGroup value={provider} onChange={handleProviderChange}>
                                <FormControlLabel value='microsoft' control={<Radio />} label='Microsoft' />
                                <FormControlLabel value='google' control={<Radio />} label='Google' disabled />
                                <FormControlLabel value='discord' control={<Radio />} label='Discord' disabled />
                                <FormControlLabel value='apple' control={<Radio />} label='Apple' disabled />
                            </RadioGroup>
                            <FormControlLabel
                                control={<Switch checked={displayEmail} onChange={handleToggle} />}
                                label='Display email publicly'
                            />
                            <Stack direction='row' spacing={2}>
                                <Button variant='contained' onClick={handleApply} disabled={!dirty}>Apply</Button>
                                <Button variant='outlined' onClick={handleCancel} disabled={!dirty}>Cancel</Button>
                                <Button variant='contained' color='error'>Delete</Button>
                            </Stack>
                        </Stack>
                    )}
            </Stack>
        </Box>
    );
};

export default UserPage;
