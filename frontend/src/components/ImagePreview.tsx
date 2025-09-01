import React from 'react';
import { IconButton, Box } from '@mui/material';

interface ImagePreviewProps {
url: string;
alt?: string;
}

const ImagePreview = ({ url, alt }: ImagePreviewProps): JSX.Element => (
<IconButton size="small" onClick={() => window.open(url, '_blank')}>
	<Box
		component="img"
		src={url}
		alt={alt ?? 'preview'}
		sx={{ width: 60, height: 60, objectFit: 'cover' }}
	/>
</IconButton>
);

export default ImagePreview;
