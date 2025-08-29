import type { ReactNode } from 'react';
import { Typography } from '@mui/material';

interface PageTitleProps {
        children: ReactNode;
}

export default function PageTitle({ children }: PageTitleProps): JSX.Element {
        return (
                <Typography variant="pageTitle" align="right">
                        {children}
                </Typography>
        );
}
