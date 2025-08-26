import type { ReactNode } from 'react';
import { TableCell, Typography, type SxProps } from '@mui/material';

interface ColumnHeaderProps {
    width?: string;
    sx?: SxProps;
    children?: ReactNode;
}

export default function ColumnHeader({ width, sx, children }: ColumnHeaderProps): JSX.Element {
    return (
        <TableCell sx={{ width, ...sx }}>
            {children ? <Typography variant="columnHeader">{children}</Typography> : null}
        </TableCell>
    );
}
