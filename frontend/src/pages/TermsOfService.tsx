import { Box, Typography } from "@mui/material";
import PageTitle from "../components/PageTitle";

const TermsOfService = (): JSX.Element => {
        return (
                <Box sx={{ p: 2 }}>
                        <PageTitle>Terms of Service</PageTitle>

                        <Typography variant="body2" sx={{ mt: 1, fontStyle: "italic" }}>
                                Last updated: September 1, 2025
                        </Typography>

                        <Typography variant="body1" sx={{ mt: 2 }}>
                                Welcome to TheOracle. By accessing or using our service, you agree to these Terms of Service
                                (&ldquo;Terms&rdquo;). Please read them carefully, as they define your rights, obligations, and acceptable
                                use of the platform.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                I. Eligibility and Accounts
                        </Typography>
                        <Typography variant="body1" component="div">
                                <ul>
                                        <li>You must be at least 13 years old to use the service (16+ in some jurisdictions).</li>
                                        <li>
                                                You must register through an OAuth identity provider (e.g., Discord, Google, Microsoft). We do
                                                not support direct password accounts.
                                        </li>
                                        <li>
                                                You are responsible for maintaining control of your linked provider accounts and ensuring that
                                                the information provided is accurate.
                                        </li>
                                </ul>
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                II. Use of Service
                        </Typography>
                        <Typography variant="body1" component="div">
                                <ul>
                                        <li>
                                                TheOracle provides AI-powered content creation and management tools, including the ability to
                                                generate, store, and share AI-generated media.
                                        </li>
                                        <li>
                                                You may purchase credits to use the service. Credits represent a license to access platform
                                                features; they have no cash value outside the platform.
                                        </li>
                                        <li>
                                                Credits may be refunded within 10 days of purchase in cases of technical failure or upon
                                                verified request when an account is deactivated.
                                        </li>
                                        <li>Excessive, automated, or abusive use of the system is prohibited.</li>
                                </ul>
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                III. Prohibited Conduct
                        </Typography>
                        <Typography variant="body1" component="div">
                                <ul>
                                        <li>
                                                Do not use the service to generate or share illegal content, including but not limited to child
                                                sexual abuse material, realistic depictions of extreme violence, or content promoting terrorism.
                                        </li>
                                        <li>Do not attempt to hack, reverse-engineer, or otherwise exploit the service or its systems.</li>
                                        <li>
                                                Do not use the service to interfere with, overload, or disrupt other services (including DOS/
                                                DDOS activity).
                                        </li>
                                        <li>
                                                Do not use the service to violate the rights of others, including copyright, trademark, or
                                                privacy rights.
                                        </li>
                                </ul>
                                Violation of these rules may result in immediate and permanent suspension of your account, with no
                                refund of credits.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                IV. Content Ownership and Licensing
                        </Typography>
                        <Typography variant="body1">
                                You retain ownership of the content you generate and upload. By using the service, you grant us a limited
                                license to host, display, and distribute your content solely for the operation of the platform. You are solely
                                responsible for ensuring your content complies with all applicable laws and these Terms.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                V. Moderation and Enforcement
                        </Typography>
                        <Typography variant="body1">
                                We use both automated systems and human moderators to enforce content guidelines. Content reported by users
                                may be temporarily restricted or removed if thresholds are met. We reserve the right to review, remove, or
                                restrict content and accounts at our discretion, including suspension or permanent termination for serious
                                violations.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                VI. Payments and Refunds
                        </Typography>
                        <Typography variant="body1" component="div">
                                <ul>
                                        <li>
                                                Payments for credits are processed through secure third-party providers; we do not store payment
                                                information.
                                        </li>
                                        <li>
                                                Refunds may be issued within 10 days of purchase for technical failures or account deactivation
                                                upon request.
                                        </li>
                                        <li>Refunds will not be provided for violations of these Terms.</li>
                                </ul>
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                VII. Termination
                        </Typography>
                        <Typography variant="body1">
                                We reserve the right to suspend or terminate your account at any time for violation of these Terms, unlawful
                                conduct, or use of the service in a manner that could harm us, other users, or third parties.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                VIII. Disclaimers and Limitation of Liability
                        </Typography>
                        <Typography variant="body1">
                                TheOracle is provided on an &ldquo;as is&rdquo; basis. We make no guarantees of uptime, accuracy, or availability.
                                To the maximum extent permitted by law, we are not liable for indirect, incidental, or consequential damages
                                arising from use of the service. Your sole remedy for dissatisfaction with the service is to stop using it.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                IX. Changes to Terms
                        </Typography>
                        <Typography variant="body1">
                                We may update these Terms from time to time. Changes will be effective upon posting. Continued use of the
                                service after changes are posted constitutes acceptance of the new Terms.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                X. Governing Law
                        </Typography>
                        <Typography variant="body1">
                                These Terms are governed by and construed in accordance with the laws of the State of Washington, USA, without
                                regard to conflict of law principles. Any disputes arising under these Terms shall be subject to the exclusive
                                jurisdiction of the courts located in Washington State.
                        </Typography>

                        <Typography variant="h6" sx={{ mt: 2 }}>
                                XI. Contact Us
                        </Typography>
                        <Typography variant="body1">
                                If you have questions about these Terms, please contact us at: contact@elideusgroup.com
                        </Typography>
                </Box>
        );
};

export default TermsOfService;
