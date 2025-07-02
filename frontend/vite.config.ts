import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
	const isProduction = mode === 'production'
	
	return {
    	plugins: [react()],
   		base: isProduction ? '/static/' : '/',
    	build: {
      		outDir: '../static',
      		assetsDir: 'assets',
  		}
	}
})
