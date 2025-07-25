import type { CSSProperties } from 'react';
import '@mui/material/styles';
import '@mui/material/Typography';

declare module '@mui/material/styles' {
    interface TypographyVariants {
        pageTitle: CSSProperties;
    }
    interface TypographyVariantsOptions {
        pageTitle?: CSSProperties;
    }
}

declare module '@mui/material/Typography' {
    interface TypographyPropsVariantOverrides {
        pageTitle: true;
    }
}
