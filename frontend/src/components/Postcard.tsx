import { Box, IconButton, Link } from '@mui/material';
import FlagIcon from '@mui/icons-material/Flag';

interface PostcardProps {
    src: string;
    guid: string;
    displayName: string;
    filename: string;
    onReport: () => void;
    contentType?: string | null;
}

const Postcard = ({ src, guid, displayName, filename, onReport, contentType }: PostcardProps): JSX.Element => {
    const isVideo = contentType?.startsWith('video/');
    const isAudio = contentType?.startsWith('audio/');
    return (
        <Box sx={{ width: 200 }}>
            <Box sx={{ position: 'relative' }}>
                {isVideo ? (
                    <video src={src} controls style={{ width: '100%' }} />
                ) : isAudio ? (
                    <audio src={src} controls style={{ width: '100%' }} />
                ) : (
                    <img src={src} alt={displayName} style={{ width: '100%' }} />
                )}
                <IconButton
                    size="small"
                    color="error"
                    onClick={onReport}
                    sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(255,255,255,0.7)' }}
                >
                    <FlagIcon fontSize="small" />
                </IconButton>
            </Box>
            <Box sx={{ mt: 1 }}>
                <Box>{filename}</Box>
                <Link
                    href={`/profile/${guid}`}
                    underline="hover"
                    sx={{ fontSize: '0.8rem', color: 'text.secondary' }}
                >
                    {displayName}
                </Link>
            </Box>
        </Box>
    );
};

export default Postcard;
