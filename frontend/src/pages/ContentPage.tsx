import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Edit as EditIcon, History as HistoryIcon, RestoreRounded as RestoreIcon } from '@mui/icons-material';
import {
	Box,
	Button,
	Collapse,
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
import { fetchPage } from '../rpc/public/pages';
import { fetchCreateVersion, fetchListVersions, fetchVersion } from '../rpc/users/pages';
import type { PublicPagesGetPage1, UsersPagesVersionList1 } from '../shared/RpcModels';

type PublicPageResponse = PublicPagesGetPage1;
type VersionItem = UsersPagesVersionList1['versions'][number] extends infer V ? V : never;

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

const ContentPage = (): JSX.Element => {
	const { slug } = useParams();
	const [isLoading, setIsLoading] = useState<boolean>(true);
	const [error, setError] = useState<string | null>(null);
	const [page, setPage] = useState<PublicPageResponse | null>(null);
	const [isEditing, setIsEditing] = useState(false);
	const [editContent, setEditContent] = useState('');
	const [editSummary, setEditSummary] = useState('');
	const [isSaving, setIsSaving] = useState(false);
	const [versions, setVersions] = useState<VersionItem[] | null>(null);
	const [showVersions, setShowVersions] = useState(false);
	const [isRestoringVersion, setIsRestoringVersion] = useState<number | null>(null);

	const loadPage = async (requestedSlug: string): Promise<PublicPageResponse> => {
		const res = await fetchPage({ slug: requestedSlug });
		setPage(res as PublicPageResponse);
		return res as PublicPageResponse;
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

			try {
				const res = await fetchPage({ slug });
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
				summary: editSummary || null,
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
				summary: `Restored from version ${versionNumber}`,
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
															<TableCell>{version.element_summary ?? '—'}</TableCell>
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

export default ContentPage;
