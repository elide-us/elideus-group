import { createTheme, type Theme } from '@mui/material/styles';

const ElideusTheme: Theme = createTheme({
	palette: {
		mode: 'dark',
		primary: { main: '#4CAF50' },
		secondary: { main: '#f48fb1' },
		background: { default: '#121212', paper: '#000000' },
		text: { primary: '#ffffff', secondary: '#b0b0c5' },
	},
	typography: {
		fontFamily: 'Roboto, Arial, sans-serif',
		h1: { fontSize: '1.6rem', fontWeight: 600 },
		h2: { fontSize: '1.35rem', fontWeight: 500 },
		body1: { fontSize: '0.875rem', lineHeight: 1.5 },
		body2: { fontSize: '0.8rem', lineHeight: 1.4 },
		button: { textTransform: 'none', fontSize: '0.8rem' },
	},
	components: {
		MuiButton: {
			styleOverrides: {
				root: {
					textTransform: 'none',
					fontSize: '0.8rem',
					borderRadius: '4px',
				},
				contained: {
					backgroundColor: '#4CAF50',
					color: '#000000',
					'&:hover': {
						backgroundColor: '#43A047',
					},
					'&.Mui-disabled': {
						backgroundColor: 'rgba(76, 175, 80, 0.3)',
						color: 'rgba(0, 0, 0, 0.5)',
					},
				},
				outlined: {
					borderColor: '#333333',
					color: '#888888',
					'&:hover': {
						borderColor: '#555555',
						backgroundColor: 'rgba(255, 255, 255, 0.04)',
					},
				},
				text: {
					color: '#888888',
					'&:hover': {
						backgroundColor: 'rgba(255, 255, 255, 0.04)',
					},
				},
				containedError: {
					backgroundColor: '#F44336',
					color: '#FFFFFF',
					'&:hover': {
						backgroundColor: '#D32F2F',
					},
				},
				outlinedError: {
					borderColor: 'rgba(244, 67, 54, 0.4)',
					color: '#F44336',
					'&:hover': {
						borderColor: '#F44336',
						backgroundColor: 'rgba(244, 67, 54, 0.08)',
					},
				},
				containedSuccess: {
					backgroundColor: '#4CAF50',
					color: '#000000',
					'&:hover': {
						backgroundColor: '#43A047',
					},
				},
			},
			defaultProps: {
				disableElevation: true,
			},
		},
		MuiIconButton: {
			styleOverrides: {
				root: {
					color: '#888888',
					'&:hover': {
						backgroundColor: 'rgba(255, 255, 255, 0.06)',
					},
				},
			},
		},
		MuiCheckbox: {
			styleOverrides: {
				root: {
					color: '#555555',
					'&.Mui-checked': {
						color: '#4CAF50',
					},
				},
			},
		},
		MuiSwitch: {
			styleOverrides: {
				switchBase: {
					'&.Mui-checked': {
						color: '#4CAF50',
						'& + .MuiSwitch-track': {
							backgroundColor: '#4CAF50',
						},
					},
				},
				track: {
					backgroundColor: '#555555',
				},
			},
		},
		MuiRadio: {
			styleOverrides: {
				root: {
					color: '#555555',
					'&.Mui-checked': {
						color: '#4CAF50',
					},
				},
			},
		},
		MuiDialog: {
			styleOverrides: {
				paper: {
					backgroundColor: '#000000',
					border: '1px solid #1A1A1A',
					borderRadius: '8px',
				},
			},
		},
		MuiDialogTitle: {
			styleOverrides: {
				root: {
					fontSize: '1rem',
					fontWeight: 600,
					fontFamily: 'Georgia, "Times New Roman", serif',
					padding: '14px 18px 8px',
				},
			},
		},
		MuiDialogContent: {
			styleOverrides: {
				root: {
					padding: '8px 18px',
				},
			},
		},
		MuiDialogActions: {
			styleOverrides: {
				root: {
					padding: '8px 18px 14px',
				},
			},
		},
		MuiLinearProgress: {
			styleOverrides: {
				root: {
					backgroundColor: '#1A1A1A',
				},
				bar: {
					backgroundColor: '#4CAF50',
				},
			},
		},
		MuiPaper: {
			styleOverrides: {
				root: {
					backgroundImage: 'none',
				},
			},
		},
		MuiListItemButton: {
			styleOverrides: {
				root: {
					'&.Mui-selected': {
						backgroundColor: 'rgba(76, 175, 80, 0.12)',
						'&:hover': {
							backgroundColor: 'rgba(76, 175, 80, 0.18)',
						},
					},
				},
			},
		},
		MuiSelect: {
			styleOverrides: {
				root: {
					fontSize: '0.8rem',
				},
			},
		},
		MuiMenuItem: {
			styleOverrides: {
				root: {
					fontSize: '0.8rem',
				},
			},
		},
		MuiAutocomplete: {
			styleOverrides: {
				root: {
					fontSize: '0.8rem',
				},
			},
		},
		MuiCardMedia: {
			styleOverrides: {
				root: {
					maxWidth: '60%',
					marginBottom: '50px',
				},
			},
		},
		MuiTextField: {
			styleOverrides: {
				root: {
					margin: '8px',
					'& .MuiInputBase-input': {
						padding: '8px',
					},
				},
			},
		},
		MuiTabs: {
			styleOverrides: {
				root: {
					minHeight: 36,
				},
				indicator: {
					backgroundColor: '#4CAF50',
				},
			},
		},
		MuiTab: {
			styleOverrides: {
				root: {
					textTransform: 'none',
					fontSize: '0.8rem',
					minHeight: 36,
					padding: '6px 12px',
					color: '#888888',
					'&.Mui-selected': {
						color: '#4CAF50',
					},
				},
			},
		},
		MuiChip: {
			defaultProps: {
				variant: 'outlined',
				size: 'small',
			},
			styleOverrides: {
				root: {
					borderRadius: '3px',
					fontWeight: 500,
					fontSize: '0.7rem',
					height: 'auto',
					padding: '1px 0',
				},
				outlined: {
					borderWidth: '1px',
				},
				colorSuccess: {
					color: '#4CAF50',
					borderColor: 'rgba(76, 175, 80, 0.25)',
					backgroundColor: 'rgba(76, 175, 80, 0.12)',
				},
				colorWarning: {
					color: '#FFC107',
					borderColor: 'rgba(255, 193, 7, 0.20)',
					backgroundColor: 'rgba(255, 193, 7, 0.10)',
				},
				colorError: {
					color: '#F44336',
					borderColor: 'rgba(244, 67, 54, 0.20)',
					backgroundColor: 'rgba(244, 67, 54, 0.10)',
				},
				colorInfo: {
					color: '#2196F3',
					borderColor: 'rgba(33, 150, 243, 0.20)',
					backgroundColor: 'rgba(33, 150, 243, 0.10)',
				},
				colorDefault: {
					color: '#888888',
					borderColor: 'rgba(136, 136, 136, 0.20)',
					backgroundColor: 'rgba(136, 136, 136, 0.10)',
				},
			},
		},
		MuiTypography: {
			variants: [
				{
					props: { variant: 'pageTitle' },
					style: {
						fontSize: '1.5rem',
						fontWeight: 600,
						marginBottom: '4px',
						textAlign: 'left',
						fontFamily: 'Georgia, "Times New Roman", serif',
						color: '#f5f5f2',
					},
				},
				{
					props: { variant: 'columnHeader' },
					style: {
						fontSize: '0.85rem',
						fontWeight: 700,
						fontFamily: 'Georgia, Times, "Times New Roman", serif',
						fontVariant: 'small-caps',
					},
				},
			],
		},
	},
});

export default ElideusTheme;
