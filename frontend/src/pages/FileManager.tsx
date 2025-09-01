import React, { useEffect, useState, useContext } from 'react';
import {
    Box,
    Table,
    TableHead,
    TableRow,
    TableCell,
    TableBody,
    IconButton,
    Stack,
    Checkbox,
    FormControlLabel,
} from '@mui/material';
import {
    OpenInNew,
    Link as LinkIcon,
    Delete,
    Publish,
    DriveFileMove,
    Folder,
} from '@mui/icons-material';
import {
    fetchFiles,
    fetchDeleteFiles,
    fetchSetGallery,
    fetchMoveFile,
} from '../rpc/storage/files';
import PageTitle from '../components/PageTitle';
import ColumnHeader from '../components/ColumnHeader';
import Notification from '../components/Notification';
import UserContext from '../shared/UserContext';
import FileUpload from '../components/FileUpload';
import FolderManager from '../components/FolderManager';
import AudioPreview from '../components/AudioPreview';
import ImagePreview from '../components/ImagePreview';

interface StorageFile {
    name: string;
    url: string;
    content_type?: string;
}

const FileManager = (): JSX.Element => {
    const [files, setFiles] = useState<StorageFile[]>([]);
    const { userData } = useContext(UserContext);
    const [notification, setNotification] = useState(false);
    const [notificationMsg, setNotificationMsg] = useState('');
    const [currentPath, setCurrentPath] = useState('');
    const [moveTarget, setMoveTarget] = useState<string | null>(null);

    const load = async (): Promise<void> => {
        try {
            const res: { files: StorageFile[] } = await fetchFiles();
            setFiles(res.files);
        } catch {
            setFiles([]);
        }
    };

    useEffect(() => {
        if (!userData) {
            setFiles([]);
            return;
        }
        void load();
    }, [userData]);


    const handleDelete = async (name: string): Promise<void> => {
        await fetchDeleteFiles({ files: [name] });
        await load();
    };

    const handleDeleteFolder = async (folder: string): Promise<void> => {
        const path = `${currentPath ? `${currentPath}/` : ''}${folder}/.init`;
        await fetchDeleteFiles({ files: [path] });
        await load();
    };

    const handleSetGallery = async (name: string): Promise<void> => {
        await fetchSetGallery({ name, gallery: true });
    };

    const handleCopy = async (url: string): Promise<void> => {
        await navigator.clipboard.writeText(url);
        setNotificationMsg('Link copied');
        setNotification(true);
    };

    const handleMove = async (name: string): Promise<void> => {
        if (moveTarget === null) return;
        const base = name.split('/').pop() || name;
        const dst = moveTarget ? `${moveTarget}/${base}` : base;
        await fetchMoveFile({ src: name, dst });
        await load();
    };

    const getType = (file: StorageFile): string => {
        const type = file.content_type || '';
        if (type.startsWith('audio/')) return 'audio';
        if (type.startsWith('video/')) return 'video';
        if (type.startsWith('image/')) return 'image';
        const ext = file.name.split('.').pop()?.toLowerCase() || '';
        if (['mp3', 'wav', 'ogg'].includes(ext)) return 'audio';
        if (['mp4', 'webm'].includes(ext)) return 'video';
        if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'].includes(ext)) return 'image';
        return 'other';
    };

    const renderPreview = (file: StorageFile): JSX.Element => {
        const type = getType(file);
        if (type === 'audio') {
            return <AudioPreview url={file.url} />;
        }
        if (type === 'image') {
            return <ImagePreview url={file.url} />;
        }
        return (
            <IconButton size="small" onClick={() => window.open(file.url, '_blank')}>
                <OpenInNew />
            </IconButton>
        );
    };

    const handleNotificationClose = (): void => {
        setNotification(false);
    };

    useEffect(() => {
        setMoveTarget(null);
    }, [currentPath]);

    const prefix = currentPath ? `${currentPath}/` : '';
    const folderSet = new Set<string>();
    const visibleFiles: StorageFile[] = [];
    files.forEach((file) => {
        if (!file.name.startsWith(prefix)) return;
        const rest = file.name.slice(prefix.length);
        const parts = rest.split('/');
        if (parts.length > 1) folderSet.add(parts[0]);
        else visibleFiles.push(file);
    });
    const folders = Array.from(folderSet);
    const parentPath = currentPath.split('/').slice(0, -1).join('/');
    if (currentPath) folders.unshift('..');

    const isFolderEmpty = (folder: string): boolean => {
        const fp = `${prefix}${folder}/`;
        return !files.some((f) => f.name.startsWith(fp) && f.name !== `${fp}.init`);
    };

    return (
        <Box sx={{ p: 2 }}>
            <Stack spacing={2}>
                <PageTitle>File Manager</PageTitle>
                <FileUpload onComplete={() => load()} path={currentPath} />
                <FolderManager path={currentPath} onPathChange={setCurrentPath} onRefresh={() => load()} />
                <Table size="small" sx={{ '& td, & th': { py: 0.5 } }}>
                    <TableHead>
                        <TableRow>
                            <ColumnHeader sx={{ width: '20%' }}>Preview</ColumnHeader>
                            <ColumnHeader sx={{ width: '60%' }}>Filename</ColumnHeader>
                            <ColumnHeader sx={{ width: '20%' }}>Actions</ColumnHeader>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {folders.map((folder) => {
                            const fullPath = folder === '..' ? parentPath : prefix + folder;
                            return (
                                <TableRow
                                    key={`folder-${folder}`}
                                    hover
                                    sx={{ cursor: 'pointer' }}
                                    onClick={() => setCurrentPath(fullPath)}
                                >
                                    <TableCell sx={{ width: '20%' }}>
                                        <IconButton size="small">
                                            <Folder />
                                        </IconButton>
                                    </TableCell>
                                    <TableCell sx={{ width: '60%' }}>{folder}</TableCell>
                                    <TableCell sx={{ width: '20%' }}>
                                        <Stack direction="row" spacing={1} alignItems="center">
                                            <FormControlLabel
                                                onClick={(e) => e.stopPropagation()}
                                                control={
                                                    <Checkbox
                                                        checked={moveTarget === fullPath}
                                                        disabled={
                                                            moveTarget !== null &&
                                                            moveTarget !== fullPath
                                                        }
                                                        onChange={(e) =>
                                                            setMoveTarget(
                                                                e.target.checked
                                                                    ? fullPath
                                                                    : null
                                                            )
                                                        }
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                }
                                                label="Move to"
                                            />
                                            {folder !== '..' && (
                                                <IconButton
                                                    size="small"
                                                    disabled={!isFolderEmpty(folder)}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        void handleDeleteFolder(folder);
                                                    }}
                                                >
                                                    <Delete />
                                                </IconButton>
                                            )}
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                        {visibleFiles.map((file) => (
                            <TableRow key={file.name}>
                                <TableCell sx={{ width: '20%' }}>{renderPreview(file)}</TableCell>
                                <TableCell sx={{ width: '60%' }}>{file.name}</TableCell>
                                <TableCell sx={{ width: '20%' }}>
                                    <Stack direction="row" spacing={1}>
                                        <IconButton size="small" onClick={() => void handleCopy(file.url)}>
                                            <LinkIcon />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => void handleDelete(file.name)}>
                                            <Delete />
                                        </IconButton>
                                        <IconButton size="small" onClick={() => void handleSetGallery(file.name)}>
                                            <Publish />
                                        </IconButton>
                                        <IconButton
                                            size="small"
                                            disabled={moveTarget === null}
                                            onClick={() => void handleMove(file.name)}
                                        >
                                            <DriveFileMove />
                                        </IconButton>
                                    </Stack>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </Stack>
            <Notification
                open={notification}
                handleClose={handleNotificationClose}
                severity="success"
                message={notificationMsg}
            />
        </Box>
    );
};

export default FileManager;

