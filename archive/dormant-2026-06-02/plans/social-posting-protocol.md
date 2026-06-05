# Social Posting Protocol — Daily OSINT Brief

## Accounts

| Platform | Email | Password Location |
|---|---|---|
| Twitter/X | trevor.mentis@gmail.com | Ask Roderick |
| TikTok | trevor.mentis@gmail.com | Ask Roderick |

## Daily Workflow (agent-facing)

When the daily cron triggers "Post the daily OSINT brief via browser automation":

### 1. Read Pre-Generated Content

Read from `exports/social/` — the pipeline generates these after the intel brief:

| File | Content |
|---|---|
| `exports/social/twitter.txt` | Brief tweet (≤280 chars) |
| `exports/social/linkedin.txt` | Full LinkedIn post |
| `exports/social/reddit_title.txt` | Reddit title |
| `exports/social/reddit_body.txt` | Reddit body |

### 2. Post to Twitter/X

```
browser open → https://x.com/compose/post
browser snapshot → find textbox ref
browser act → click textbox ref
browser act → type (content from twitter.txt)
browser snapshot → find Post button ref
browser act → click Post button
```

**Timing:** Wait 3-4s after page load before typing. Wait 2s after posting for confirmation.

### 3. Post to TikTok (if applicable)

TikTok web posting requires navigating to tiktok.com and using the upload interface.
For now, TikTok posting is manual — no browser automation flow available.

### 4. Log the Post

Append to `memory/social-log.json`:
```json
{
  "date": "YYYY-MM-DD",
  "platform": "twitter",
  "posted": true,
  "content_preview": "First 50 chars..."
}
```

## Login Procedure (first time)

1. `browser open → https://x.com/i/flow/login`
2. Enter email: trevor.mentis@gmail.com
3. Click Next
4. Enter password (ask Roderick)
5. Click Log in
6. Handle 2FA if prompted (ask Roderick for code)

## Rules

- **Max 1-2 posts per day** — quality over quantity
- **Post after the intel brief runs** (~06:00 PT, cron at 13:00 UTC)
- **Never post without content** — if no brief is ready, skip
- **Log everything** in `memory/social-log.json`

## No API Keys Required

This entire pipeline uses browser automation — no Twitter API, no third-party posting services.
