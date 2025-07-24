import { useEffect, useState, useContext } from 'react';
import { Box, List, ListItem, Typography, IconButton, Link as MuiLink } from '@mui/material';
import { Delete, ContentCopy, Link as LinkIcon } from '@mui/icons-material';
import EditBox from './shared/EditBox';
import PaginationControls from './shared/PaginationControls';
import { PageTitle } from './shared/PageTitle';
import { fetchList, fetchDelete } from './rpc/frontend/files';
import UserContext from './shared/UserContext';
import type { FileItem, FrontendFilesList1 } from './shared/RpcModels';

const FileManager = (): JSX.Element => {
    const { userData } = useContext(UserContext);

    const [page, setPage] = useState(0);
    const [itemsPerPage, setItemsPerPage] = useState(10);
    const [files, setFiles] = useState<FileItem[]>([]);

    const load = async (): Promise<void> => {
        try {
            const res: FrontendFilesList1 = await fetchList({ bearerToken: userData?.bearerToken });
            setFiles(res.files);
        } catch {
            setFiles([]);
        }
    };

    useEffect(() => { void load(); }, []);

    const totalPages = Math.max(1, Math.ceil(files.length / itemsPerPage));
    const paginated = files.slice(page * itemsPerPage, (page + 1) * itemsPerPage);

    const handleDelete = async (name: string): Promise<void> => {
        await fetchDelete({ bearerToken: userData?.bearerToken, filename: name });
        void load();
    };

    const handleCopy = (url: string): void => {
        void navigator.clipboard.writeText(url);
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='File Manager' />
            <List>
                {paginated.map(f => (
                    <ListItem key={f.name} sx={{ gap: 1 }}>
                        <EditBox value={f.name} onCommit={() => {}} manual size='small' />
                        <IconButton onClick={() => void handleDelete(f.name)}><Delete /></IconButton>
                        <IconButton onClick={() => handleCopy(f.url)}><ContentCopy /></IconButton>
                        <MuiLink href={f.url} target='_blank' rel='noopener noreferrer'><LinkIcon /></MuiLink>
                        <Typography sx={{ ml: 'auto' }}>{f.contentType}</Typography>
                    </ListItem>
                ))}
            </List>
            <PaginationControls
                page={page}
                setPage={setPage}
                totalPages={totalPages}
                itemsPerPage={itemsPerPage}
                setItemsPerPage={setItemsPerPage}
            />
        </Box>
    );
};

export default FileManager;
