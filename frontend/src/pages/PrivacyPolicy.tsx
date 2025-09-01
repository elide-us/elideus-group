import { Box, Typography } from '@mui/material';
import PageTitle from '../components/PageTitle';

const PrivacyPolicy = (): JSX.Element => {
	return (
		<Box sx={{ p: 2 }}>
			<PageTitle>Privacy Policy</PageTitle>

			<Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
				Last updated: September 1, 2025
			</Typography>

			<Typography variant="body1" sx={{ mt: 2 }}>
				We value your privacy and are committed to protecting your personal information. This Privacy Policy explains what information we collect, how we use it, and your choices regarding your data.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				I. Information We Collect
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>Username / Display Name from your identity provider</li>
					<li>Email address from your identity provider</li>
					<li>Profile image / avatar from your identity provider</li>
					<li>Unique account identifier from your identity provider</li>
				</ul>
				We do not request or store passwords from your identity provider.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				II. How We Use Your Information
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>Account creation and login</li>
					<li>Display within the service</li>
					<li>Moderation purposes</li>
				</ul>
				We do not sell, rent, or share your personal data with third parties for any reason.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				III. Your Choices and Control
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>You may set your display name to anything you prefer. If you change providers, your name will refresh but remains editable.</li>
					<li>Your email address is hidden by default. You may choose to display it, but it cannot be edited, as it is sourced from your provider.</li>
					<li>Your profile image may be pulled from your provider, but you may replace it within the service.</li>
				</ul>
				Moderators cannot change your name, but may reset it to a default if reported or found offensive.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				IV. Account Management and Deletion
			</Typography>
			<Typography variant="body1" component="div">
				<ul>
					<li>You may link or unlink identity providers at any time.</li>
					<li>If you unlink all providers, your account enters a soft-deleted state. Minimal identifiers are retained to associate you with previously generated content.</li>
					<li>You may request permanent deletion of your account and associated data by contacting us at contact@elideusgroup.com.</li>
				</ul>
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				V. Content Privacy
			</Typography>
			<Typography variant="body1">
				Your content is private by default. You may choose to share content publicly. This choice is always under your control.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				VI. Data Retention
			</Typography>
			<Typography variant="body1">
				We retain only the minimum information necessary to operate the service: identity provider identifiers (for login/authentication), and content/preferences you create. We do not collect or store payment details, government IDs, or other sensitive personal information.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				VII. Compliance
			</Typography>
			<Typography variant="body1">
				We comply with data protection laws including the EU General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA). You have the right to access, rectify, delete, and export your data upon request.
			</Typography>

			<Typography variant="h6" sx={{ mt: 2 }}>
				VIII. Contact Us
			</Typography>
			<Typography variant="body1">
				If you have questions about this Privacy Policy or wish to exercise your rights, please contact us at: contact@elideusgroup.com
			</Typography>
		</Box>
	);
};

export default PrivacyPolicy;
