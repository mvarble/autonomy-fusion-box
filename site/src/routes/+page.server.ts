import { cms } from '$cms';

import { openEntries } from '$lib/server/open';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => ({ landing: cms.landing(), open: openEntries() });
