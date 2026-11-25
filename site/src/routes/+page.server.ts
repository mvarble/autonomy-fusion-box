import { cms } from '$cms';

import { openEntries } from '@mvarble/mesearch-workflow/app/lib/server/open.ts';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => ({ landing: cms.landing(), open: openEntries() });
