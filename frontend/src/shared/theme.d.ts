import type { CSSProperties } from 'react';
import '@mui/material/styles';
import '@mui/material/Typography';

declare module '@mui/material/styles' {
    interface TypographyVariants {
        pageTitle: CSSProperties;
        columnHeader: CSSProperties;
    }
    interface TypographyVariantsOptions {
        pageTitle?: CSSProperties;
        columnHeader?: CSSProperties;
    }
}

declare module '@mui/material/Typography' {
    interface TypographyPropsVariantOverrides {
        pageTitle: true;
        columnHeader: true;
    }
}
