import React, { useRef, useState } from 'react';
import { Box, Button, LinearProgress, TextField, Typography } from '@mui/material';
import { Cancel } from '@mui/icons-material';
import axios from 'axios';

interface FileUploadProps {
    onComplete?: () => Promise<void> | void;
}

const FileUpload = ({ onComplete }: FileUploadProps): JSX.Element => {
    const [fileName, setFileName] = useState('');
    const [uploading, setUploading] = useState(false);
    const [uploaded, setUploaded] = useState(0);
    const [total, setTotal] = useState(0);
    const [bps, setBps] = useState(0);
    const controllerRef = useRef<AbortController | null>(null);

    const handleFile = async (e: React.ChangeEvent<HTMLInputElement>): Promise<void> => {
        const file = e.target.files?.[0];
        if (!file) return;
        setFileName(file.name);
        controllerRef.current = new AbortController();
        setUploading(true);
        const start = Date.now();
        try {
            await uploadWithProgress(file, controllerRef.current.signal, (loaded, totalBytes) => {
                const elapsed = (Date.now() - start) / 1000;
                setUploaded(loaded);
                setTotal(totalBytes);
                setBps(loaded / Math.max(elapsed, 0.001));
            });
            if (onComplete) await onComplete();
        } finally {
            setUploading(false);
            setUploaded(0);
            setTotal(0);
            setBps(0);
            setFileName('');
            if (e.target) e.target.value = '';
        }
    };

    const handleCancel = (): void => {
        controllerRef.current?.abort();
    };

    const percent = total ? (uploaded / total) * 100 : 0;

    return (
        <Box sx={{ border: '1px solid', borderColor: 'grey.500', p: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Button variant="contained" component="label">
                Select File
                <input type="file" hidden onChange={handleFile} />
            </Button>
            <TextField value={fileName} InputProps={{ readOnly: true }} sx={{ flexGrow: 1 }} />
            {uploading && (
                <>
                    <Box sx={{ flexGrow: 1, position: 'relative' }}>
                        <LinearProgress variant="determinate" value={percent} />
                        <Typography variant="caption" sx={{ position: 'absolute', left: '50%', top: 0, bottom: 0, display: 'flex', alignItems: 'center', transform: 'translateX(-50%)' }}>
                            {`${uploaded} / ${total} (${Math.round(bps)} B/s)`}
                        </Typography>
                    </Box>
                    <Button onClick={handleCancel} startIcon={<Cancel />}>Cancel</Button>
                </>
            )}
        </Box>
    );
};

const uploadWithProgress = async (
    file: File,
    signal: AbortSignal,
    onProgress: (loaded: number, total: number) => void,
): Promise<void> => {
    const toUpload = await fileToUpload(file);
    const request = {
        op: 'urn:storage:files:upload_files:1',
        payload: { files: [toUpload] },
        version: 1,
        timestamp: new Date().toISOString(),
    };
    const headers: Record<string, string> = {};
    if (typeof localStorage !== 'undefined') {
        try {
            const raw = localStorage.getItem('authTokens');
            if (raw) {
                const { sessionToken } = JSON.parse(raw);
                if (sessionToken) headers.Authorization = `Bearer ${sessionToken}`;
            }
        } catch {
            /* ignore token parsing errors */
        }
    }
    await axios.post('/rpc', request, {
        headers,
        signal,
        onUploadProgress: (e) => {
            if (e.total) onProgress(e.loaded, e.total);
        },
    });
};

const fileToUpload = (file: File): Promise<{ name: string; content_b64: string; content_type?: string }> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const result = reader.result as string;
            const content_b64 = result.split(',')[1] ?? '';
            resolve({ name: file.name, content_b64, content_type: file.type || undefined });
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

export default FileUpload;

