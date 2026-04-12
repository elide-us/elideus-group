import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

interface NotificationProps {
	open: boolean;
	handleClose: () => void;
	severity: 'success' | 'info' | 'warning' | 'error';
	message: string;
}

const Notification = ({ open, handleClose, severity, message }: NotificationProps): JSX.Element => (
	<Snackbar open={open} autoHideDuration={6000} onClose={handleClose}>
		<Alert onClose={handleClose} severity={severity} sx={{ width: '100%' }}>
			{message}
		</Alert>
	</Snackbar>
);

export default Notification;
