import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography } from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

import PageTitle from '../components/PageTitle';
import { rpcCall } from '../shared/RpcModels';

type PublicPageResponse = {
	title: string;
	content: string | null;
	page_type: string;
	element_created_on: string | null;
	element_modified_on: string | null;
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

	useEffect(() => {
		let active = true;

		const loadPage = async (): Promise<void> => {
			if (!slug) {
				if (active) {
					setError('Page not found');
					setIsLoading(false);
				}
				return;
			}

			setIsLoading(true);
			setError(null);

			try {
				const res = await rpcCall<PublicPageResponse>('urn:public:pages:get_page:1', { slug });
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

		void loadPage();
		return () => {
			active = false;
		};
	}, [slug]);

	const modifiedDate = useMemo(
		() => formatDisplayDate(page?.element_modified_on ?? null),
		[page?.element_modified_on],
	);

	if (isLoading) {
		return <Box sx={{ p: 2, maxWidth: 800 }} />;
	}

	if (error) {
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
			<PageTitle>{page.title}</PageTitle>

			{modifiedDate && (
				<Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
					{modifiedDate}
				</Typography>
			)}

			<Box
				sx={{
					mt: 2,
					'& h1, & h2, & h3, & h4, & h5, & h6': { mt: 3, mb: 1 },
					'& p': { mt: 1, mb: 1 },
					'& ul, & ol': { pl: 3 },
					'& a': { color: 'primary.main' },
				}}
			>
				<ReactMarkdown>{page.content ?? ''}</ReactMarkdown>
			</Box>
		</Box>
	);
};

export default ContentPage;
