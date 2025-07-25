import { useEffect, useState, useContext, useRef } from 'react';
import type { ChangeEvent } from 'react';
import { Box, List, ListItem, Typography, IconButton, Link as MuiLink, Tooltip } from '@mui/material';
import { Delete, ContentCopy, Link as LinkIcon, Add } from '@mui/icons-material';
import EditBox from './shared/EditBox';
import PaginationControls from './shared/PaginationControls';
import { PageTitle } from './shared/PageTitle';
import { fetchList, fetchDelete, fetchUpload } from './rpc/frontend/files';
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

    useEffect(() => { void load(); }, [userData?.bearerToken]);

    const totalPages = Math.max(1, Math.ceil(files.length / itemsPerPage));
    const paginated = files.slice(page * itemsPerPage, (page + 1) * itemsPerPage);

    const handleDelete = async (name: string): Promise<void> => {
        await fetchDelete({ bearerToken: userData?.bearerToken, filename: name });
        void load();
    };

    const handleCopy = (url: string): void => {
        void navigator.clipboard.writeText(url);
    };

    const fileInput = useRef<HTMLInputElement>(null);

    const handleSelect = async (e: ChangeEvent<HTMLInputElement>): Promise<void> => {
        const file = e.target.files?.[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = async () => {
            const dataUrl = reader.result as string;
            await fetchUpload({
                bearerToken: userData?.bearerToken,
                filename: file.name,
                dataUrl,
                contentType: file.type,
            });
            void load();
        };
        reader.readAsDataURL(file);
    };

    return (
        <Box sx={{ p: 2 }}>
            <PageTitle title='File Manager' />
            <IconButton onClick={() => fileInput.current?.click()} sx={{ mb: 1 }}>
                <Add /> Upload
            </IconButton>
            <input
                type='file'
                accept='image/jpeg,image/png,image/gif,image/webp'
                ref={fileInput}
                onChange={handleSelect}
                hidden
            />
            <List>
                {paginated.map(f => (
                    <ListItem key={f.name} sx={{ gap: 1 }}>
                        <EditBox value={f.name} onCommit={() => {}} manual size='small' sx={{ width: '40ch' }} />
                        <Tooltip title='Delete'>
                            <IconButton onClick={() => void handleDelete(f.name)}><Delete /></IconButton>
                        </Tooltip>
                        <Tooltip title='Copy URL'>
                            <IconButton onClick={() => handleCopy(f.url)}><ContentCopy /></IconButton>
                        </Tooltip>
                        <Tooltip title='Open Link'>
                            <IconButton component={MuiLink} href={f.url} target='_blank' rel='noopener noreferrer'>
                                <LinkIcon />
                            </IconButton>
                        </Tooltip>
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
