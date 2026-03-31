import { useContext, useEffect, useMemo, useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Edit as EditIcon, History as HistoryIcon, RestoreRounded as RestoreIcon } from '@mui/icons-material';
import {
	Box,
	Button,
	Collapse,
	Link,
	List,
	ListItem,
	ListItemText,
	Table,
	TableBody,
	TableCell,
	TableContainer,
	TableHead,
	TableRow,
	TextField,
	Typography,
} from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

import MarkdownEditor from '../components/MarkdownEditor';
import PageTitle from '../components/PageTitle';
import { fetchPage as fetchWikiPage } from '../rpc/public/wiki';
import { fetchCreatePage, fetchCreateVersion, fetchListVersions, fetchVersion } from '../rpc/users/wiki';
import type { PublicWikiGetPage1, UsersWikiVersionList1, UsersWikiVersionContent1 } from '../shared/RpcModels';
import UserContext from '../shared/UserContext';

type PublicWikiResponse = PublicWikiGetPage1;
type VersionItem = UsersWikiVersionList1['versions'][number] extends infer V ? V : never;
type VersionContentResponse = UsersWikiVersionContent1;

const markdownBodySx = {
	'& h1, & h2, & h3, & h4, & h5, & h6': { mt: 3, mb: 1 },
	'& p': { mt: 1, mb: 1 },
	'& ul, & ol': { pl: 3 },
	'& a': { color: 'primary.main' },
};

const formatDisplayDate = (isoDate: string | null): string => {
	if (!isoDate) {
		return '';
	}
	const parsed = new Date(isoDate);
	if (Number.isNaN(parsed.getTime())) {
		return '';
	}
	return parsed.toLocaleDateString('en-US', {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
	});
};

const resolveWikiSlug = (pathname: string): string => {
	if (!pathname.startsWith('/wiki')) {
		return '';
	}
	const normalized = pathname.replace(/^\/wiki\/?/, '').trim();
	return normalized || 'home';
};

const WikiPage = (): JSX.Element => {
	const location = useLocation();
	const { userData } = useContext(UserContext);
	const slug = useMemo(() => resolveWikiSlug(location.pathname), [location.pathname]);
	const [isLoading, setIsLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);
	const [page, setPage] = useState<PublicWikiResponse | null>(null);
	const [isEditing, setIsEditing] = useState(false);
	const [editContent, setEditContent] = useState('');
	const [editSummary, setEditSummary] = useState('');
	const [isSaving, setIsSaving] = useState(false);
	const [versions, setVersions] = useState<VersionItem[] | null>(null);
	const [showVersions, setShowVersions] = useState(false);
	const [isRestoringVersion, setIsRestoringVersion] = useState<number | null>(null);
	const [isCreating, setIsCreating] = useState(false);
	const [createTitle, setCreateTitle] = useState('');
	const [createContent, setCreateContent] = useState('');
	const [createSummary, setCreateSummary] = useState('');
	const [isCreatingSaving, setIsCreatingSaving] = useState(false);

	const parentSlug = useMemo(() => {
		const lastSlash = slug.lastIndexOf('/');
		return lastSlash > 0 ? slug.substring(0, lastSlash) : null;
	}, [slug]);

	const defaultTitle = useMemo(() => {
		const lastSegment = slug.split('/').pop() ?? slug;
		return lastSegment
			.split('-')
			.map((word) => word.charAt(0).toUpperCase() + word.slice(1))
			.join(' ');
	}, [slug]);

	const loadPage = async (requestedSlug: string): Promise<PublicWikiResponse> => {
		const res = await fetchWikiPage({ slug: requestedSlug });
		setPage(res as PublicWikiResponse);
		return res as PublicWikiResponse;
	};

	useEffect(() => {
		let active = true;

		const run = async (): Promise<void> => {
			if (!slug) {
				if (active) {
					setError('Page not found');
					setIsLoading(false);
				}
				return;
			}

			setIsLoading(true);
			setError(null);
			setIsEditing(false);
			setEditSummary('');
			setVersions(null);
			setShowVersions(false);
			setIsCreating(false);
			setCreateTitle('');
			setCreateContent('');
			setCreateSummary('');

			try {
				const res = await fetchWikiPage({ slug });
				if (active) {
					setPage(res);
				}
			} catch (err) {
				if (!active) {
					return;
				}
				if (axios.isAxiosError(err) && err.response?.status === 404) {
					setError('Page not found');
				} else {
					setError('Unable to load page content. Please try again later.');
				}
			} finally {
				if (active) {
					setIsLoading(false);
				}
			}
		};

		void run();
		return () => {
			active = false;
		};
	}, [slug]);

	const modifiedDate = useMemo(
		() => formatDisplayDate(page?.element_modified_on ?? null),
		[page?.element_modified_on],
	);

	const handleStartEdit = (): void => {
		if (!page) {
			return;
		}
		setEditContent(page.content ?? '');
		setEditSummary('');
		setIsEditing(true);
	};

	const handleCancelEdit = (): void => {
		setIsEditing(false);
		setEditContent('');
		setEditSummary('');
	};

	const handleSave = async (): Promise<void> => {
		if (!page || !slug || !editContent.trim()) {
			return;
		}
		setIsSaving(true);
		setError(null);
		try {
			await fetchCreateVersion({
				slug: page.slug,
				content: editContent,
				edit_summary: editSummary || null,
			});
			await loadPage(slug);
			setIsEditing(false);
			setEditSummary('');
			setVersions(null);
		} catch {
			setError('Unable to save your changes. Please try again.');
		} finally {
			setIsSaving(false);
		}
	};

	const handleToggleVersions = async (): Promise<void> => {
		if (!page) {
			return;
		}
		const nextExpanded = !showVersions;
		setShowVersions(nextExpanded);
		if (!nextExpanded || versions) {
			return;
		}
		try {
			const res = await fetchListVersions({ slug: page.slug });
			setVersions(res.versions as any[]);
		} catch {
			setError('Unable to load version history. Please try again.');
		}
	};

	const handleCreate = async (): Promise<void> => {
		if (!slug || !createTitle.trim() || !createContent.trim()) {
			return;
		}
		setIsCreatingSaving(true);
		setError(null);
		try {
			await fetchCreatePage({
				slug,
				title: createTitle,
				content: createContent,
				parent_slug: parentSlug,
				edit_summary: createSummary || null,
			});
			await loadPage(slug);
			setIsCreating(false);
			setCreateTitle('');
			setCreateContent('');
			setCreateSummary('');
		} catch {
			setError('Unable to create the page. Please try again.');
		} finally {
			setIsCreatingSaving(false);
		}
	};

	const handleRestoreVersion = async (versionNumber: number): Promise<void> => {
		if (!page || !slug) {
			return;
		}
		setIsRestoringVersion(versionNumber);
		setError(null);
		try {
			const version = await fetchVersion({
				slug: page.slug,
				version: versionNumber,
			});
			await fetchCreateVersion({
				slug: page.slug,
				content: version.element_content,
				edit_summary: `Restored from version ${versionNumber}`,
			});
			await loadPage(slug);
			setVersions(null);
			setShowVersions(false);
		} catch {
			setError('Unable to restore that version. Please try again.');
		} finally {
			setIsRestoringVersion(null);
		}
	};

	if (isLoading) {
		return <Box sx={{ p: 2, maxWidth: 800 }} />;
	}

	if (error && !page) {
		if (userData && error === 'Page not found') {
			return (
				<Box sx={{ p: 2, maxWidth: 800 }}>
					{isCreating ? (
						<>
							<PageTitle>Create: {slug}</PageTitle>
							<TextField
								size="small"
								fullWidth
								sx={{ mt: 2 }}
								label="Page title"
								value={createTitle}
								onChange={(event) => {
									setCreateTitle(event.target.value);
								}}
							/>
							<Box sx={{ mt: 2 }}>
								<MarkdownEditor
									value={createContent}
									onChange={setCreateContent}
									minHeight={300}
									placeholder="Write your page content here..."
								/>
							</Box>
							<TextField
								size="small"
								fullWidth
								sx={{ mt: 2 }}
								placeholder="Edit summary (optional)"
								value={createSummary}
								onChange={(event) => {
									setCreateSummary(event.target.value);
								}}
							/>
							<Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
								<Button
									variant="contained"
									onClick={() => void handleCreate()}
									disabled={isCreatingSaving || !createTitle.trim() || !createContent.trim()}
								>
									Create Page
								</Button>
								<Button variant="outlined" onClick={() => setIsCreating(false)} disabled={isCreatingSaving}>
									Cancel
								</Button>
							</Box>
						</>
					) : (
						<>
							<PageTitle>This page does not exist yet</PageTitle>
							<Typography variant="body1" sx={{ mt: 2 }}>
								The wiki page <strong>{slug}</strong> has not been created.
							</Typography>
							<Button
								variant="contained"
								sx={{ mt: 2 }}
								startIcon={<EditIcon />}
								onClick={() => {
									setCreateTitle(defaultTitle);
									setIsCreating(true);
								}}
							>
								Create this page
							</Button>
						</>
					)}
				</Box>
			);
		}

		return (
			<Box sx={{ p: 2, maxWidth: 800 }}>
				<PageTitle>{error}</PageTitle>
			</Box>
		);
	}

	if (!page) {
		return (
			<Box sx={{ p: 2, maxWidth: 800 }}>
				<PageTitle>Page not found</PageTitle>
			</Box>
		);
	}

	return (
		<Box sx={{ p: 2, maxWidth: 800 }}>
			<Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 2 }}>
				<Box>
					<PageTitle>{page.title}</PageTitle>

					{modifiedDate && (
						<Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
							{modifiedDate}
						</Typography>
					)}
				</Box>
				{page.permissions?.can_edit && (
					<Button
						variant="outlined"
						size="small"
						startIcon={<EditIcon />}
						onClick={isEditing ? handleCancelEdit : handleStartEdit}
					>
						{isEditing ? 'Cancel' : 'Edit'}
					</Button>
				)}
			</Box>

			{error && (
				<Typography color="error" sx={{ mt: 2 }}>
					{error}
				</Typography>
			)}

			{isEditing ? (
				<Box sx={{ mt: 2 }}>
					<MarkdownEditor value={editContent} onChange={setEditContent} minHeight={360} />
					<TextField
						size="small"
						fullWidth
						sx={{ mt: 2 }}
						placeholder="Edit summary (optional)"
						value={editSummary}
						onChange={(event) => {
							setEditSummary(event.target.value);
						}}
					/>
					<Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
						<Button variant="contained" onClick={() => void handleSave()} disabled={isSaving || !editContent.trim()}>
							Save
						</Button>
						<Button variant="outlined" onClick={handleCancelEdit} disabled={isSaving}>
							Cancel
						</Button>
					</Box>
				</Box>
			) : (
				<>
					<Box sx={{ mt: 2, ...markdownBodySx }}>
						<ReactMarkdown>{page.content ?? ''}</ReactMarkdown>
					</Box>

					{page.children.length > 0 && (
						<Box sx={{ mt: 4 }}>
							<Typography variant="h6">Sub-pages</Typography>
							<List dense>
								{page.children.map((child) => (
									<ListItem key={child.slug} disableGutters>
										<ListItemText
											primary={
												<Link component={RouterLink} to={`/wiki/${child.slug}`} underline="hover">
													{child.title}
												</Link>
											}
											slotProps={{
												primary: { variant: 'body2' },
											}}
										/>
									</ListItem>
								))}
							</List>
						</Box>
					)}

					{page.permissions?.can_edit && (
						<Box sx={{ mt: 3 }}>
							<Button
								startIcon={<HistoryIcon />}
								onClick={() => {
									void handleToggleVersions();
								}}
							>
								Version History
							</Button>
							<Collapse in={showVersions} timeout="auto" unmountOnExit>
								<Box sx={{ mt: 1 }}>
									<TableContainer>
										<Table size="small">
											<TableHead>
												<TableRow>
													<TableCell>Version #</TableCell>
													<TableCell>Date</TableCell>
													<TableCell>Summary</TableCell>
													<TableCell align="right">Actions</TableCell>
												</TableRow>
											</TableHead>
											<TableBody>
												{(versions ?? []).map((version) => {
													const isCurrent = version.element_version === page.version;
													return (
														<TableRow key={version.recid}>
															<TableCell>{version.element_version}</TableCell>
															<TableCell>{formatDisplayDate(version.element_created_on)}</TableCell>
															<TableCell>{version.element_edit_summary ?? '—'}</TableCell>
															<TableCell align="right">
																{!isCurrent && (
																	<Button
																		size="small"
																		startIcon={<RestoreIcon fontSize="small" />}
																		disabled={isRestoringVersion === version.element_version}
																		onClick={() => {
																			void handleRestoreVersion(version.element_version);
																		}}
																	>
																		Restore
																	</Button>
																)}
															</TableCell>
														</TableRow>
													);
												})}
											</TableBody>
										</Table>
									</TableContainer>
								</Box>
							</Collapse>
						</Box>
					)}
				</>
			)}
		</Box>
	);
};

export default WikiPage;
