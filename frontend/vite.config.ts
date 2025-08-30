import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
	const isProduction = mode === "production";

	return {
		plugins: [react()],
		base: isProduction ? "/static/" : "/",
                build: {
                        outDir: "../static",
                        assetsDir: "assets",
                        rollupOptions: {
                                output: {
                                        manualChunks(id) {
                                                if (id.includes("node_modules")) {
                                                        return "vendor";
                                                }
                                                const match = id.match(/src\/pages\/(system|service|admin)\//);
                                                if (match) {
                                                        return match[1];
                                                }
                                        },
                                },
                        },
                },
	};
});
