import { Typography, Divider } from '@mui/material';

export const PageTitle = ({ title }: { title: string }): JSX.Element => (
    <>
        <Typography variant='h5'>{title}</Typography>
        <Divider sx={{ mb: 2 }} />
    </>
);
