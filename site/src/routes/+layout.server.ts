import { cms } from '$cms';

import { resolve } from '$app/paths';
import { linkOf, type DocumentLink } from '$lib/documents';
import { ARCHIVE, MATH, TRACKS } from '$lib/site';
import type { LayoutServerLoad } from './$types';

/** A link in the navigation. */
export type NavItem = Pick<DocumentLink, 'key' | 'title' | 'href' | 'status'>;

export interface NavSection {
    id: string;
    title: string;
    short: string;
    href: string;
    items: NavItem[];
}

// The navigation: each track's pages, the math notes, and the archive's entries.
export const load: LayoutServerLoad = () => {
    const nav: NavSection[] = [
        ...TRACKS.map((track) => ({
            ...track,
            href: resolve('/[track=track]', { track: track.id }),
            items: cms.pages.list(track.id).map(linkOf),
        })),
        { ...MATH, href: resolve('/math'), items: cms.math.list().map(linkOf) },
        { ...ARCHIVE, href: resolve('/archive'), items: cms.archive.list().map(linkOf) },
    ];
    // Where the site is hosted, when the build knows it (`SITE_URL=https://example.org`).
    const origin = (process.env.SITE_URL ?? '').replace(/\/$/, '');
    return { nav, origin };
};
