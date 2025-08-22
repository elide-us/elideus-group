/// <reference types='vite/client' />

declare module '*.png' {
	const src: string;
	export default src;
}

interface ImportMetaEnv {
	readonly VITE_GOOGLE_CLIENT_ID?: string;
}

interface ImportMeta {
	readonly env: ImportMetaEnv;
}
