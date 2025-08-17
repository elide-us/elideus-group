import { useContext, useEffect, useState, ChangeEvent } from 'react';
import { Box, Typography, FormControlLabel, Switch, Avatar, TextField, Button, Stack, RadioGroup, Radio } from '@mui/material';
import UserContext from './shared/UserContext';
import type { UsersProfileProfile1 } from './shared/RpcModels';
import { fetchProfile, fetchSetDisplay, fetchSetOptin } from './rpc/users/profile';
import { fetchSetProvider } from './rpc/users/providers';

const UserPage = (): JSX.Element => {
        const { userData, setUserData } = useContext(UserContext);
        const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
        const [displayEmail, setDisplayEmail] = useState(false);
        const [displayName, setDisplayName] = useState('');
        const [provider, setProvider] = useState('microsoft');
        const [dirty, setDirty] = useState(false);

        useEffect(() => {
                if (!userData) return;
                void (async () => {
                        try {
                                const res: UsersProfileProfile1 = await fetchProfile();
                                setProfile(res);
                                setDisplayName(res.display_name);
                                setDisplayEmail(res.display_email);
                                setProvider(res.default_provider);
                        } catch {
                                setProfile(null);
                        }
                })();
        }, [userData]);

        const handleToggle = (): void => {
                setDisplayEmail(!displayEmail);
                setDirty(true);
        };

        const handleNameChange = (e: ChangeEvent<HTMLInputElement>): void => {
                setDisplayName(e.target.value);
                setDirty(true);
        };

        const handleProviderChange = (e: ChangeEvent<HTMLInputElement>): void => {
                setProvider(e.target.value);
                setDirty(true);
        };

        const handleCancel = (): void => {
                if (profile) {
                        setDisplayName(profile.display_name);
                        setDisplayEmail(profile.display_email);
                        setProvider(profile.default_provider);
                }
                setDirty(false);
        };

        const handleApply = async (): Promise<void> => {
                try {
                        await fetchSetDisplay({ display_name: displayName });
                        await fetchSetOptin({ display_email: displayEmail });
                        await fetchSetProvider({ provider });
                        if (userData) setUserData({ ...userData, display_name: displayName });
                        if (profile) setProfile({ ...profile, display_name: displayName, display_email: displayEmail, default_provider: provider });
                        setDirty(false);
                } catch (err) {
                        console.error('Failed to update profile', err);
                }
        };

        return (
                <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                        <Box sx={{ maxWidth: 400, width: '100%' }}>
                                <Stack spacing={2} sx={{ mt: 2, display: 'flex', alignItems: 'flex-end', textAlign: 'right' }}>
                                        <Typography variant='h5' gutterBottom>User Profile</Typography>

                                        {profile && (
                                                <Stack spacing={2} sx={{ mt: 2, alignItems: 'flex-end', width: '100%' }}>
                                                        <Avatar src={profile.profile_image ? `data:image/png;base64,${profile.profile_image}` : undefined} sx={{ width: 80, height: 80 }} />

                                                        <TextField
                                                                label='Display Name'
                                                                value={displayName}
                                                                onChange={handleNameChange}
                                                                fullWidth
                                                                slotProps={{
                                                                        input: {
                                                                                style: { textAlign: 'right' }
                                                                        }
                                                                }}
                                                        />

                                                        <Typography>Credits: {profile.credits ?? 0}</Typography>
                                                        <Typography>Email: {profile.email}</Typography>

                                                        <RadioGroup value={provider} onChange={handleProviderChange} sx={{ alignItems: 'flex-end' }}>
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

                                                        <Stack direction='row' spacing={2} sx={{ justifyContent: 'flex-end', width: '100%' }}>
                                                                <Button variant='contained' onClick={handleApply} disabled={!dirty}>Apply</Button>
                                                                <Button variant='outlined' onClick={handleCancel} disabled={!dirty}>Cancel</Button>
                                                                <Button variant='contained' color='error'>Delete</Button>
                                                        </Stack>
                                                </Stack>
                                        )}
                                </Stack>
                        </Box>
                </Box>
        );
};

export default UserPage;
