import { useContext, useEffect, useState, ChangeEvent } from 'react';
import { Box, Typography, FormControlLabel, Switch, Avatar, TextField, Button, Stack, RadioGroup, Radio } from '@mui/material';
import UserContext from './shared/UserContext';
import type { UsersProfileProfile1 } from './shared/RpcModels';
import { fetchProfile, fetchSetDisplay, fetchSetOptin } from './rpc/users/profile';
import { fetchSetProvider, fetchLinkProvider, fetchUnlinkProvider } from './rpc/users/providers';
import googleConfig from './config/google';

declare global {
interface Window {
google: any;
}
}

const UserPage = (): JSX.Element => {
		const { userData, setUserData, clearUserData } = useContext(UserContext);
		const [profile, setProfile] = useState<UsersProfileProfile1 | null>(null);
		const [displayEmail, setDisplayEmail] = useState(false);
		const [displayName, setDisplayName] = useState('');
		const [provider, setProvider] = useState('microsoft');
		const [dirty, setDirty] = useState(false);
		const [providers, setProviders] = useState<string[]>([]);

	const normalizeGuid = (guid: unknown): string => {
		if (typeof guid === 'string') return guid;
		if (guid && typeof guid === 'object') {
			const val = (guid as { toString?: () => string }).toString;
			if (val) {
				try {
					return val.call(guid);
				} catch {
					/* ignore */
				}
			}
		}
		return '';
	};

	useEffect(() => {
		if (!userData) return;
		void (async () => {
			try {
				const res: any = await fetchProfile();
				const profileData: UsersProfileProfile1 = { ...res, guid: normalizeGuid(res.guid) };
				setProfile(profileData);
								setDisplayName(profileData.display_name);
								setDisplayEmail(profileData.display_email);
								setProvider(profileData.default_provider);
								setProviders(profileData.auth_providers?.map(p => p.name) ?? []);
			} catch {
				setProfile(null);
			}
		})();
	}, [userData]);

		const handleToggle = (): void => {
				setDisplayEmail(!displayEmail);
				setDirty(true);
		};

		const handleNameChange = (e: ChangeEvent<HTMLInputElement>): void => {
				setDisplayName(e.target.value);
				setDirty(true);
		};

		const handleProviderChange = (e: ChangeEvent<HTMLInputElement>): void => {
				setProvider(e.target.value);
				setDirty(true);
		};

		const handleCancel = (): void => {
				if (profile) {
						setDisplayName(profile.display_name);
						setDisplayEmail(profile.display_email);
						setProvider(profile.default_provider);
				}
				setDirty(false);
		};

		const handleApply = async (): Promise<void> => {
				try {
						await fetchSetDisplay({ display_name: displayName });
						await fetchSetOptin({ display_email: displayEmail });
						await fetchSetProvider({ provider });
						if (userData) setUserData({ ...userData, display_name: displayName });
						if (profile) setProfile({ ...profile, display_name: displayName, display_email: displayEmail, default_provider: provider });
						setDirty(false);
				} catch (err) {
console.error('Failed to update profile', err);
				}
		};

		const handleUnlink = async (name: string): Promise<void> => {
				if (providers.length <= 1 && !window.confirm('This will delete your account. Continue?')) return;
				try {
						await fetchUnlinkProvider({ provider: name });
						const updated = providers.filter(p => p !== name);
						setProviders(updated);
						if (profile) {
								const authProviders = profile.auth_providers?.filter(p => p.name !== name) ?? [];
								setProfile({ ...profile, auth_providers: authProviders });
						}
						if (updated.length === 0) clearUserData();
				} catch (err) {
console.error('Failed to unlink provider', err);
				}
		};

		const handleLink = async (name: string): Promise<void> => {
				if (name !== 'microsoft' && name !== 'google') return;
				try {
					   if (name === 'google') {
							   if (!window.google || !window.crypto) throw new Error('Google API not loaded');
							   const base64UrlEncode = (buffer: ArrayBuffer): string => {
									   const bytes = new Uint8Array(buffer);
									   let binary = '';
									   for (const b of bytes) binary += String.fromCharCode(b);
									   return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
							   };
							   const generateVerifier = (): string => {
									   const array = new Uint8Array(32);
									   window.crypto.getRandomValues(array);
									   return base64UrlEncode(array.buffer);
							   };
							   const pkceChallenge = async (verifier: string): Promise<string> => {
									   const data = new TextEncoder().encode(verifier);
									   const digest = await window.crypto.subtle.digest('SHA-256', data);
									   return base64UrlEncode(digest);
							   };
							   const codeVerifier = generateVerifier();
							   const codeChallenge = await pkceChallenge(codeVerifier);
							   const code = await new Promise<string>((resolve) => {
									   const codeClientConfig = {
											   client_id: googleConfig.clientId,
											   scope: googleConfig.scope,
											   redirect_uri: googleConfig.redirectUri,
											   code_challenge: codeChallenge,
											   code_challenge_method: 'S256',
											   callback: (resp: any) => resolve(resp.code),
									   };
console.debug('[UserPage] initCodeClient config', codeClientConfig);
									   const client = window.google.accounts.oauth2.initCodeClient(codeClientConfig);
									   client.requestCode();
							   });
console.debug('[UserPage] authorization code received', code);
							   await fetchLinkProvider({ provider: name, code, code_verifier: codeVerifier });
					   } else {
							   await fetchLinkProvider({ provider: name });
					   }
						const updated = [...providers, name];
						setProviders(updated);
						if (profile) {
								const authProviders = [...(profile.auth_providers ?? []), { name, display: name.charAt(0).toUpperCase() + name.slice(1) }];
								setProfile({ ...profile, auth_providers: authProviders });
						}
				} catch (err) {
console.error('Link provider not implemented', err);
				}
		};

		const allProviders = [
				{ name: 'microsoft', display: 'Microsoft', enabled: true },
				{ name: 'google', display: 'Google', enabled: true },
				{ name: 'discord', display: 'Discord', enabled: false },
				{ name: 'apple', display: 'Apple', enabled: false }
		];

		return (
				<Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
						<Box sx={{ maxWidth: 400, width: '100%' }}>
								<Stack spacing={2} sx={{ mt: 2, display: 'flex', alignItems: 'flex-end', textAlign: 'right' }}>
										<Typography variant='h5' gutterBottom>User Profile</Typography>

										{profile && (
												<Stack spacing={2} sx={{ mt: 2, alignItems: 'flex-end', width: '100%' }}>
														<Avatar src={profile.profile_image ? `data:image/png;base64,${profile.profile_image}` : undefined} sx={{ width: 80, height: 80 }} />

														<TextField
																label='Display Name'
																value={displayName}
																onChange={handleNameChange}
																fullWidth
																slotProps={{
																		input: {
																				style: { textAlign: 'right' }
																		}
																}}
														/>

														<Typography>Credits: {profile.credits ?? 0}</Typography>
														<Typography>Email: {profile.email}</Typography>

														<RadioGroup value={provider} onChange={handleProviderChange} sx={{ alignItems: 'flex-end' }}>
																{allProviders.filter(p => p.enabled && providers.includes(p.name)).map(p => (
																		<FormControlLabel key={p.name} value={p.name} control={<Radio />} label={p.display} />
																))}
														</RadioGroup>

														{allProviders.map(p => {
																const linked = providers.includes(p.name);
																return (
																		<Stack key={p.name} direction='row' spacing={1} sx={{ justifyContent: 'flex-end', width: '100%' }}>
																				<Typography>{p.display}</Typography>
																				{linked ? (
																						<Button variant='outlined' onClick={() => handleUnlink(p.name)}>{providers.length === 1 ? 'Delete' : 'Unlink'}</Button>
																				) : (
																						<Button variant='contained' onClick={() => handleLink(p.name)} disabled={!p.enabled}>{p.enabled ? 'Link' : 'Link (Coming Soon)'}</Button>
																				)}
																		</Stack>
																);
														})}

														<FormControlLabel
																control={<Switch checked={displayEmail} onChange={handleToggle} />}
																label='Display email publicly'
																labelPlacement='start'
																sx={{ alignSelf: 'flex-end' }}
														/>

														<Stack direction='row' spacing={2} sx={{ justifyContent: 'flex-end', width: '100%' }}>
																<Button variant='contained' onClick={handleApply} disabled={!dirty}>Apply</Button>
																<Button variant='outlined' onClick={handleCancel} disabled={!dirty}>Cancel</Button>
																<Button variant='contained' color='error'>Delete</Button>
														</Stack>
												</Stack>
										)}
								</Stack>
						</Box>
				</Box>
		);
};

export default UserPage;
