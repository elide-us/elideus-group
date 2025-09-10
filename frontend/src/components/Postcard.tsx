import { Box, IconButton, Link } from '@mui/material';
import FlagIcon from '@mui/icons-material/Flag';

interface PostcardProps {
	src: string;
	guid: string;
	displayName: string;
	onReport: () => void;
}

const Postcard = ({ src, guid, displayName, onReport }: PostcardProps): JSX.Element => {
	return (
	    <Box sx={{ width: 200 }}>
	        <Box sx={{ position: 'relative' }}>
	            <img src={src} alt={displayName} style={{ width: '100%' }} />
	            <IconButton
	                size="small"
	                color="error"
	                onClick={onReport}
	                sx={{ position: 'absolute', bottom: 4, right: 4, bgcolor: 'rgba(255,255,255,0.7)' }}
	            >
	                <FlagIcon fontSize="small" />
	            </IconButton>
	        </Box>
	        <Link href={`/profile/${guid}`} underline="hover">
	            {displayName}
	        </Link>
	    </Box>
	);
};

export default Postcard;
