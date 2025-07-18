import { useContext, useState } from 'react';
import { Box, Typography, FormControlLabel, Switch } from '@mui/material';
import UserContext from './shared/UserContext';

const UserPage = (): JSX.Element => {
    const { userData, setUserData } = useContext(UserContext);
    const [displayEmail, setDisplayEmail] = useState<boolean>(userData?.displayEmail ?? false);

    const handleToggle = (): void => {
        const val = !displayEmail;
        setDisplayEmail(val);
        if (userData) {
            setUserData({ ...userData, displayEmail: val });
        }
    };

    return (
        <Box sx={{ mt: 4 }}>
            <Typography variant='h5' gutterBottom>User Profile</Typography>
            <FormControlLabel
                control={<Switch checked={displayEmail} onChange={handleToggle} />}
                label='Display email publicly'
            />
        </Box>
    );
};

export default UserPage;
