import { Typography, Divider } from '@mui/material';

export const PageTitle = ({ title }: { title: string }): JSX.Element => (
    <>
        <Typography variant='pageTitle'>{title}</Typography>
        <Divider />
    </>
);
