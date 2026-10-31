<script lang="ts">
    import { resolve } from '$app/paths';
    import Logo from '$lib/components/Logo.svelte';
    import OpenEntry from '$lib/components/OpenEntry.svelte';
    import TrackCard from '$lib/components/TrackCard.svelte';
    import { ARCHIVE, MATH, SITE, TRACKS } from '$lib/site';

    let { data } = $props();

    const blurb = (id: string) => TRACKS.find((t) => t.id == id)!.blurb;
</script>

<svelte:head>
    <title>{SITE.name}: {SITE.tagline}</title>
    <meta property="og:title" content="{SITE.name}: {SITE.tagline}" />
    <meta name="description" content={SITE.description} />
    <meta property="og:description" content={SITE.description} />
</svelte:head>

<section class="hero">
    <p class="eyebrow">GNSS · IMU · camera · one GPS-disciplined timebase</p>
    <h1><Logo variant="lockup" /><span class="visually-hidden">{SITE.name}</span></h1>
    <p class="hero-tagline">{SITE.tagline}</p>
    <div class="hero-actions">
        <a class="button primary" href={resolve('/archive')}>The work so far</a>
        <a class="button" href={SITE.repo} rel="external">View source</a>
    </div>
</section>

<section class="landing-open">
    <h2>On the table</h2>
    {#each data.open as entry (entry.link.key)}
        <OpenEntry {entry} />
    {:else}
        <p class="muted">
            No entry is open on this branch. <code>/wf-start &lt;slug&gt; &lt;kind&gt;</code> opens one.
        </p>
    {/each}
</section>

{#if data.component}
    <section class="landing-body prose">
        <data.component />
    </section>
{/if}

<section class="landing-tracks">
    <h2>Where things are</h2>
    <div class="card-grid">
        <TrackCard id="start" eyebrow="Begin" blurb={blurb('start')} />
        <TrackCard id="system" eyebrow="What is true now" blurb={blurb('system')} />
    </div>
    <div class="card-grid secondary">
        <TrackCard id="archive" eyebrow="How it came to be" blurb={ARCHIVE.blurb} />
        <TrackCard id="reference" eyebrow="Look it up" blurb={blurb('reference')} />
        <TrackCard id="math" eyebrow="What it rests on" blurb={MATH.blurb} />
    </div>
</section>
