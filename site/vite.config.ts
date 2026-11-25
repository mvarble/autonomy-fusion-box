import { docsSite } from '@mvarble/mesearch-workflow/site';
import { defineConfig } from 'vitest/config';

// The companion site, as `@mvarble/mesearch-workflow` builds every project's: the content database
// over `content/`, SvelteKit with mdsvex, and `$site`, which hands the shared pages the box's own
// (`src/lib/site.ts`, the logo and `katex.config.ts`).
export default defineConfig({
    plugins: await docsSite(),
    test: {
        include: ['src/**/*.test.ts'],
        // The site's own tests, of which there are none yet: the shared pages are tested upstream.
        passWithNoTests: true,
    },
});
