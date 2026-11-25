import { navigation, siteOrigin } from '@mvarble/mesearch-workflow/app/lib/nav.ts';

import type { LayoutServerLoad } from './$types';

// The navigation: each track's pages, the math notes, and the archive's entries.
export const load: LayoutServerLoad = () => ({ nav: navigation(), origin: siteOrigin() });
