---
title: Laravel 11 ignores Kernel.php — schedules must live in routes/console.php (plus 3 sub-traps)
source_mode: debugger
novelty_type: reusable_diagnostic
grounding_score: 1.0
staleness_risk: slow_decay
importance: 5
pinned: true
created: 2026-05-26
domain: infrastructure
topic: deployment
tags: empirical, deployment, scheduling, quality-gate
related_entries: []
---

# Laravel 11 ignores Kernel.php — schedules must live in routes/console.php (plus 3 sub-traps)

## The core trap

Laravel 11's bootstrap (`bootstrap/app.php`) reads scheduled tasks from `routes/console.php`. The legacy `app/Console/Kernel.php::schedule()` method is **completely ignored** after a Laravel 10→11 upgrade. The file isn't deleted by the upgrade — it just stops being called. Existing schedules silently stop firing with no error and no log.

In one project this orphaned an every-minute menu-sync schedule for ~8 months without anyone noticing — discovered only when investigating why a custom cron entry needed to be added.

## Three additional traps stacked on the core one

These compound the diagnostic difficulty because each is silent on its own:

### Trap 2: `schedule:run` is not auto-wired by Forge

Laravel Forge sets up other crons (security monitoring, certbot renewals, etc.) but does NOT add `* * * * * php artisan schedule:run` to the forge user's crontab. Manually required:

```cron
* * * * * cd /home/forge/<site> && php artisan schedule:run >> /dev/null 2>&1
```

Without this, even a correctly-registered schedule in `routes/console.php` fires zero times.

### Trap 3: Method order — `name()` must precede `withoutOverlapping()` for closure schedules

Closure-based schedules (`Schedule::call(...)`) require a name BEFORE `withoutOverlapping()` is added:

```php
// ❌ Throws "A scheduled event name is required to prevent overlapping" during package:discover
Schedule::call(fn () => doWork())
    ->everyFifteenMinutes()
    ->withoutOverlapping()
    ->name('my-task');

// ✅ name() first
Schedule::call(fn () => doWork())
    ->name('my-task')
    ->everyFifteenMinutes()
    ->withoutOverlapping();
```

Command-based schedules (`Schedule::command(...)`) auto-derive the name from the command signature, so this trap only fires on closures. Symptom: `composer dump-autoload` (or any operation triggering `php artisan package:discover`) fails with a `CallbackEvent.php:142` error referencing the name requirement.

### Trap 4: `dailyAt()` and `between()` interpret times in APP_TIMEZONE — not server local time

If `APP_TIMEZONE=UTC` in `.env` (Laravel default), then:

```php
->dailyAt('06:05')          // means 06:05 UTC (= 23:05 PT or 22:05 PT depending on DST)
->between('10:00', '22:00') // means 10:00-22:00 UTC (= 02:00-14:00 PT)
```

The fix is per-schedule:

```php
Schedule::command('my:job')
    ->dailyAt('06:05')
    ->timezone('America/Los_Angeles')  // now means 06:05 PT
    ->withoutOverlapping();
```

Or globally via `Schedule::useTimezone(...)`, but per-schedule is safer for multi-tenant or shared codebases.

## Diagnostic checklist

When a Laravel 11 scheduled task isn't firing:

1. **Is it in `routes/console.php`?** If it's in `app/Console/Kernel.php::schedule()`, move it. Kernel.php is dead.
2. **Is `schedule:run` in any cron?** Check forge user's crontab, root's crontab, and `/etc/cron.d/`. If absent, add it.
3. **Does `php artisan schedule:list` show your task?** If yes, registration is good. If no, route file load issue (check syntax, ensure file is in `bootstrap/app.php`'s `commands:` slot).
4. **Is the time correct?** Compare `php artisan schedule:list` "Next Due" against your expected wall-clock time. If off by a fixed offset (e.g., 7-8 hours), it's the timezone trap — add `->timezone(...)`.
5. **For closures: does `package:discover` succeed?** If it fails on `CallbackEvent.php:142`, your `name()` is after `withoutOverlapping()`.

## When this DOES apply

- Any Laravel 10→11 upgrade where pre-existing `Kernel.php::schedule()` was relied on
- Any Laravel 11+ project being set up on Forge for the first time
- Any project where `APP_TIMEZONE=UTC` but operations are anchored to a different timezone (restaurants, retail, regional services)

## When this DOES NOT apply

- Laravel 10 and earlier — Kernel.php scheduling still works
- Single-developer projects where the developer is in UTC anyway
- Projects where schedule:run was already wired before the upgrade (the cron entry survives the upgrade; only the in-code schedule registrations break)

## Grounding

All four traps were hit during a single deploy session on 2026-05-26 for the tuannw Laravel 11.36.1 project on a DigitalOcean staging server. Each was diagnosed and fixed sequentially:

- Trap 1 (Kernel dead): discovered after `schedule:list` returned only the `inspire` command despite a schedule registered in Kernel.php; confirmed via reading `bootstrap/app.php`'s `commands:` slot pointing only to `routes/console.php`
- Trap 2 (no cron): forge crontab inspection showed only security monitoring entries; manually added `* * * * * cd ... && php artisan schedule:run` 
- Trap 3 (method order): caught during GitHub Actions deploy when `package:discover` failed with the exact "name is required" error; fixed by reordering
- Trap 4 (timezone): `schedule:list` showed `Next Due: 13 hours from now` for what should have been `Next Due: 7 hours from now` — debugged via checking `APP_TIMEZONE=UTC`; fixed with `->timezone('America/Los_Angeles')`

Original session was a Phase 1 dashboard SEO snapshot pipeline deploy. All four traps blocked the deploy independently and required separate commits to resolve.

## Source Context

Session: laravel-11-scheduler-discovery-2026-05-26. Debugger mode analyzing production deployment failures after Laravel 11.36.1 upgrade on Tuan NW restaurant website. The multi-location Laravel app uses menu synchronization and reporting tasks via scheduler. Silent orphaning of existing schedules caused 8-month data sync gap (Trap 1). Cascade failures on Trap 2-4 compounded diagnostic difficulty during emergency deploy.

