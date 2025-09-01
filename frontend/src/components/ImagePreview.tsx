import React from 'react';
import { Box, IconButton } from '@mui/material';

interface ImagePreviewProps {
    url: string;
}

const ImagePreview = ({ url }: ImagePreviewProps): JSX.Element => (
    <IconButton size="small" onClick={() => window.open(url, '_blank')} sx={{ p: 0 }}>
        <Box
            component="img"
            src={url}
            alt=""
            sx={{ width: 120, height: 30, objectFit: 'cover' }}
        />
    </IconButton>
);

export default ImagePreview;
