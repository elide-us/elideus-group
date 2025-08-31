import { Box, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';

const PrivacyPolicy = (): JSX.Element => {
	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Privacy Policy</PageTitle>
			<Typography variant="h6" sx={{ mt: 2 }}>
				Data We Collect
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>Username from your identity provider</li>
					<li>Email address from your identity provider</li>
					<li>Profile image from your identity provider</li>
				</ul>
			</Typography>
			<Typography variant="h6" sx={{ mt: 2 }}>
				Your Control
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>You may set your display name to anything you prefer. Changing providers refreshes the name from the provider but it remains editable.</li>
					<li>Your email address is hidden by default. You may choose to display it, but it is sourced from the provider and not editable.</li>
				</ul>
			</Typography>
			<Typography variant="body1" sx={{ mt: 2 }}>
				We keep no other information about users, payment providers or personal details. Our objective is to comply with modern EU privacy standards.
			</Typography>
			<Typography variant="body1" sx={{ mt: 2 }}>
				Moderators cannot set your name but may reset it to the provider default if reported or offensive.
			</Typography>
			<Typography variant="body1" sx={{ mt: 2 }}>
				Unlinking your account from all providers will soft-delete your account; we retain unique identifiers to match you to previously generated content.
			</Typography>
			<Typography variant="body1" sx={{ mt: 2 }}>
				Your content is private by default. You may flag content to be shared publicly if you desire.
			</Typography>
		</Box>
	);
};

export default PrivacyPolicy;
