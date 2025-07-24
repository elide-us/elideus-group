import { Box, IconButton, Select, MenuItem } from '@mui/material';
import { ChevronLeft, ChevronRight } from '@mui/icons-material';

interface PaginationProps {
    page: number;
    setPage: (p: number) => void;
    totalPages: number;
    itemsPerPage: number;
    setItemsPerPage: (n: number) => void;
}

const PaginationControls = ({ page, setPage, totalPages, itemsPerPage, setItemsPerPage }: PaginationProps): JSX.Element => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton disabled={page === 0} onClick={() => setPage(page - 1)}><ChevronLeft /></IconButton>
        <span>{page + 1} / {totalPages}</span>
        <IconButton disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}><ChevronRight /></IconButton>
        <Select size='small' value={itemsPerPage} onChange={e => setItemsPerPage(Number(e.target.value))}>
            {[5, 10, 20].map(n => <MenuItem key={n} value={n}>{n}/page</MenuItem>)}
        </Select>
    </Box>
);

export default PaginationControls;
