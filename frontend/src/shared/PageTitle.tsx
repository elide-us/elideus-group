import { Typography, Divider } from '@mui/material';

export const PageTitle = ({ title }: { title: string }): JSX.Element => (
    <>
        <Typography variant='h3'>{title}</Typography>
        <Divider sx={{ mb: 2 }} />
    </>
);
