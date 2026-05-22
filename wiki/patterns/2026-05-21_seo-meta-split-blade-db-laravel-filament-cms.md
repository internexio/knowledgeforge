---
title: SEO meta split between Blade templates and DB-stored pages in Laravel/Filament CMS
source_mode: direct
novelty_type: new_pattern
grounding_score: 0.8
staleness_risk: slow_decay
importance: 3
pinned: false
created: 2026-05-21
domain: web-frameworks
topic: laravel-cms-meta-split
tags: laravel, blade, filament, cms, seo, migration, multi-tenant, metadata-management
related_entries: []
---

# SEO meta split between Blade templates and DB-stored pages in Laravel/Filament CMS

## The Gotcha

In a Laravel app where some pages are coded in Blade templates and some pages are CMS-managed (stored in a `pages` or `restaurant_pages` table and rendered by a generic `page.blade.php`), the SEO metadata (`<title>`, `<meta description>`) lives in **two different places**:

- **Blade-coded pages** (`/`, `/menu`, `/drinks`): meta strings hardcoded in the Blade file, usually via a `match($restaurant->slug)` or `match($page)` block in a per-template match statement
- **DB-stored pages** (`/happy-hour`, `/reviews`, `/about`, custom landing pages): meta in DB columns (`meta_title`, `meta_description`, `meta_keywords` on the `restaurant_pages` table), rendered by `@section('title', $page->meta_title)` in a generic template

A bulk SEO change (e.g., "fix all title tags across the site") therefore needs **both**:
1. **Code change** for the Blade-coded pages (PR + deploy)
2. **Data migration** for the DB-stored pages (`up()` method that updates the rows)

If you only do (1), the CMS pages keep their old titles. If you only do (2), the Blade pages keep theirs.

## Why This Exists

Filament (or similar CMS admin panels) enable content editors to manage page metadata without touching code. This is correct UX for a CMS — the database is the source of truth for editor-controlled pages. But most Laravel apps also have hardcoded pages (homepage, core menu pages) where SEO metadata is embedded in the template for performance, version control, and coupling with page structure.

The split is an architectural consequence: **code-driven pages prioritize developer control and version history; CMS-driven pages prioritize editor control and no-deploy agility.** Both are correct for their respective use case, but they create a split metadata surface.

## When It Applies

- Laravel app with Filament admin OR similar CMS pattern (Statamic, Voyager, Backpack, custom)
- App routes use a catch-all `Route::get('/{slug}', ...)` pattern that loads page records from DB
- SEO meta is rendered via `@section('title', $page->meta_title)` in a generic page template
- Multi-tenant / multi-restaurant / multi-location setups amplify this — each tenant has its own row per page slug
- You're planning a bulk SEO change that affects both hardcoded and CMS-managed pages

## How to Detect This Split in an Unfamiliar Codebase

```bash
# 1. Look for @section('title') in templates — find the rendering surface
grep -r "@section('title'" resources/views/

# 2. Look for $page->meta_title or similar — find DB-stored fields
grep -rE 'meta_title|meta_description' resources/views/ app/ database/

# 3. Look for a generic page template (page.blade.php, content.blade.php)
find resources/views -name "page.blade.php" -o -name "content.blade.php"

# 4. Look for the catch-all route
grep -E "Route::get.*\{slug\}|publishedPages" routes/web.php

# 5. Check the database schema for meta columns
grep -E "meta_title|meta_description" database/migrations/*.php
```

If steps 3 and 4 both produce hits, you have the split.

## Fix Pattern: Paired Code + Migration

The correct fix always requires **two changes in a single PR**:

### Change 1: Update Blade Template

```php
// resources/views/restaurant/menu.blade.php (or whichever template)

// Old pattern: hardcoded meta via match statement
$seoData = match($restaurant->slug) {
    'laca-bar' => [
        'title' => '...',
        'description' => '...',
        'h1' => '...',
    ],
    'laca-cafe' => [...],
    'laca-38th' => [...],
    default => ['title' => 'Menu', 'description' => 'Our menu', 'h1' => 'Menu'],
};

@section('title', $seoData['title'])
@section('description', $seoData['description'])

<h1>{{ $seoData['h1'] }}</h1>
```

### Change 2: Create a Paired Data Migration

```php
// database/migrations/YYYY_MM_DD_seo_update_meta.php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        // Define the updates as an array of [restaurant_slug, page_slug, fields_to_update]
        $updates = [
            ['laca-bar', 'happy-hour', [
                'meta_title' => 'La Cà Bar Happy Hour — Happy Hour & Specials',
                'meta_description' => 'Join us for happy hour at La Cà Bar...',
            ]],
            ['laca-bar', 'reviews', [
                'meta_title' => 'La Cà Bar Reviews — Vietnamese Pho in Tacoma',
                'meta_description' => 'See reviews from customers...',
            ]],
            ['laca-cafe', 'happy-hour', [
                'meta_title' => 'La Cà Café Happy Hour — Specials & Deals',
                'meta_description' => 'Join us for happy hour at La Cà Café...',
            ]],
            // ... more updates
        ];

        foreach ($updates as [$restaurantSlug, $pageSlug, $fields]) {
            $restaurantId = DB::table('restaurants')
                ->where('slug', $restaurantSlug)
                ->value('id');

            if (! $restaurantId) {
                continue; // Restaurant doesn't exist; skip
            }

            DB::table('restaurant_pages')
                ->where('restaurant_id', $restaurantId)
                ->where('slug', $pageSlug)
                ->update($fields);
        }
    }

    public function down(): void
    {
        // Down-migrations for title/meta are tricky because the prior value isn't usually
        // worth restoring (it was old SEO copy). Make this a no-op by design.
        // Document this decision: "This migration is forward-only; rollback requires manual restoration."
    }
};
```

**Critical:** Both changes must ship in the same PR. The deployment workflow must run `php artisan migrate --force` after pulling the new code.

## Naming Conventions

- **Migration filename pattern:** `YYYY_MM_DD_000001_seo_[scope]_update_meta.php` — descriptive enough to `grep` for later
  - Example: `2026_05_21_000001_seo_p0_menu_titles.php`
  - Reason: Makes it easy to find all SEO-related migrations later when debugging meta data issues

## Anti-Patterns This Corrects

- **Update DB titles via Filament admin manually** — works once, but isn't code-tracked; no PR history, no rollback capability across environments
- **Add `meta_title` to a config file** — doesn't scale; DB-stored is correct for CMS pages because editors need to change them without code deploy
- **Use Filament admin programmatically via Tinker** — works once, isn't idempotent, isn't reviewable, and can't be replayed on new staging instances
- **Write a "fix-seo.php" script that hits the prod DB directly** — bypasses migration tracking; if rerun creates duplicate updates or data corruption
- **Blade-only update without migration** — CMS pages miss the change; causes silent SEO regression
- **Migration-only update without Blade change** — hardcoded pages miss the change; causes inconsistent titles across the site

## Down-Migration Handling

Title/meta down-migrations are tricky because the prior value isn't usually worth restoring (it was old SEO copy). It's reasonable to make `down()` a no-op — but **document this decision explicitly** in the migration or in a migration-notes section:

```php
public function down(): void
{
    // This migration is forward-only by design.
    // Reason: Restoring old SEO metadata is not helpful — if you need to roll back,
    // re-deploy the previous code (which will re-render the old titles) rather than
    // attempt to restore the DB to a stale SEO state.
    // (If you absolutely must restore prior titles, do so manually from git history or backups.)
}
```

## Concrete Grounding (This Session)

- **Project:** Tuan NW Laravel 11 + Filament 3
- **Discovered:** Pages `/happy-hour` and `/reviews` serve from `resources/views/restaurant/page.blade.php` which renders `@section('title', $page->meta_title)`. The `restaurant_pages` table holds `meta_title`, `meta_description`, `meta_keywords` columns. Slugs are exactly `happy-hour` and `reviews` (kebab-case).
- **Confirmed Blade-coded:** `/`, `/menu`, `/drinks` use per-template `match($restaurant->slug)` blocks for `$seoData`
- **P0 scope required both:** 
  - Blade code changes: title trims on Bar + 38th `/menu` pages, H1 rewrites on `/menu` and `/drinks`
  - Data migration: update meta_title/meta_description for Cafe `/happy-hour`, Bar `/reviews`, 38th `/happy-hour`, 38th `/reviews`, Bar `/happy-hour`
- **Migration filename used:** `2026_05_21_000001_seo_p0_update_page_meta.php`
- **Deploy:** GitHub Actions workflow runs `php artisan migrate --force` after pulling code + migrations → both pieces deploy in one PR
- **Verification method:** Post-deploy smoke test navigates to both Blade-coded and CMS-managed pages, takes screenshots, compares title tags to expected values

## When This Does NOT Apply

- **Single-source-of-truth sites** — all pages are either Blade OR DB, never both
- **Pages with no SEO metadata changes pending** — split doesn't matter if you're not changing titles
- **Static site generators** — metadata is baked into compiled HTML; no runtime split to manage
- **Headless CMS with single delivery layer** — the API returns metadata consistently; no split between data sources

## Related Patterns & Resources

- **Laravel migrations for data updates:** Similar pattern for any bulk data changes (not schema changes)
- **Multi-tenant routing in Laravel:** Pages table pattern with per-tenant rows
- **Filament resource publishing:** How CMS admin panels serialize metadata to the DB
- **SEO metadata best practices:** Ensure consistency across all pages (meta_title length, uniqueness, keyword alignment)

## Source Context

Candidate derived from tuannw-2026-05-21-p0-seo-deploy session. The Tuan NW multi-location restaurant chain has a Laravel 11 app with a hybrid metadata model: 3 hardcoded Blade pages (homepage, menu, drinks) + 5 CMS-managed restaurant_pages (happy-hour, reviews, about, etc.). During a P0 SEO audit and deployment, the split required paired code + migration changes. The pattern is generalizable: any Filament (or similar CMS) + hardcoded Blade app will encounter this split when doing bulk SEO updates.

Reuse value: Applicable to any Laravel app using Filament or similar admin panels for CMS-managed pages alongside hardcoded Blade pages. The pattern ensures bulk metadata changes deploy consistently across both sources, preventing silent SEO regressions where one class of pages misses the update.

