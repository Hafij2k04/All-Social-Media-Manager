# All Social Media Manager — AI Developer Handoff

This file is the shared source of truth for any AI assistant or developer continuing this repository. Read it before editing code.

## Repository
- GitHub: Hafij2k04/All-Social-Media-Manager
- Active branch: main
- Main application: social_bot_v1/bot_v1/

## Product direction
Build a modular Personal AI Social Media Assistant that manages multiple accounts across multiple platforms. One user may have several YouTube channels, Facebook pages, TikTok accounts, Instagram accounts, and other profiles.

Core principles:
1. Every task must be scoped to explicitly selected platform/account(s). Never mix data or instructions between channels.
2. Support selecting one account or multiple accounts, including multiple accounts on the same platform and accounts across platforms.
3. Maintain a separate profile, preferences, history, feedback, and performance context for each account.
4. Learn from explicit user feedback and historical outcomes through persistent memory/retrieval. Do not claim the underlying AI model has been retrained.
5. Monitor only data available through supported, authorized APIs. Never invent analytics, trends, or competitor metrics.
6. No destructive or public-facing action without explicit user approval: publishing, deleting, changing published metadata/media, disconnecting accounts, or changing important settings.
7. AI providers and creative tools are modular. A model that writes prompts is not automatically an image/video generator; use only supported integrations and APIs.
8. Do not bypass free-tier limits, quotas, account restrictions, or platform safeguards by rotating accounts.

## User experience decisions
- /start should show only the clean welcome message and main menu. Do not send a flood of channel alerts at startup.
- Add a separate Channel Health & Alerts section for reports and problems.
- Notifications should be configurable and sent for meaningful alerts, not every metric fluctuation.
- The bot should support normal text instructions and, later, voice-to-text commands.
- Before publishing, show the complete preview (video, thumbnail, title, description, target account) and request approval.

## Current implementation state
- Language selection is implemented for Bengali, English, Hindi, Urdu, Chinese, Arabic, Nepali, and Assamese.
- Status dashboard is implemented; it reports saved configuration, not proof that every platform API is live.
- Accounts are stored by platform and account name in storage.py.
- YouTube and Facebook have partial stats-sync paths; other platform analytics are placeholders until official API support is implemented.
- Analysis & Ideas previously was a placeholder.

### Latest Analysis & Ideas selection foundation
Implemented in commits:
- `0e1eabd` — multi-platform and multi-account selection UI in handlers/automation.py
- `91e0f79` — persist per-user selected accounts in storage.py
- `09c73cd` — restore saved selection when Analysis & Ideas opens
- `ace311f` — register analysis callback handler in main.py

Current behavior:
1. Open Analysis & Ideas.
2. Select one or more platforms.
3. Select one or more accounts under those platforms (or Select All / Clear).
4. Confirm; selection is saved per Telegram user.
5. Feature buttons show the selected account scope. Actual AI analysis/research workflows are the next implementation phase.

Relevant files:
- `social_bot_v1/bot_v1/handlers/automation.py`
- `social_bot_v1/bot_v1/storage.py`
- `social_bot_v1/bot_v1/main.py`

## Next development steps
1. Verify the current multi-account selection flow in Telegram; fix any reported issues.
2. Add per-account Channel Profile fields (niche, language, audience, content style, formats, goals) without breaking existing account records.
3. Build Channel Analysis using only stored/synced metrics and the selected accounts.
4. Build Niche Research, Video Ideas, and Competitor Analysis using the active AI provider; clearly distinguish user-provided facts from live researched facts.
5. Add persistent feedback/memory per user and per account.
6. Add Channel Health dashboard and scheduled monitoring from authorized API data.
7. Add notification preferences and alert thresholds.
8. Add approval workflow for any publishing, deletion, or modification.
9. Add voice transcription and natural-language task routing.
10. Add creative routing for image/video tools and a review-first publishing pipeline.

## Safe collaboration procedure for any AI assistant
Before changing code:
1. Fetch/read the latest version of this file and the exact source files you will edit from the default branch.
2. Check recent commits and current file contents. Do not rely on another chat's remembered code.
3. Make one small, scoped change at a time. Preserve working behavior and existing account data.
4. Do not overwrite a file using an old copy. Fetch the latest blob SHA immediately before updating it.
5. Never run parallel writes to the same file. Coordinate changes sequentially.
6. After each change, fetch the file again and verify the resulting content.
7. Run available syntax/tests where possible. State clearly what was and was not tested.
8. Do not deploy or claim deployment success unless the deployment status was actually checked.
9. Never put tokens, API keys, passwords, OAuth credentials, or private user data in source files, commits, prompts, or this document. Use environment secrets or secure storage.
10. If a task is unfinished, update this handoff file with the exact state, changed files, commit IDs, known issues, and next step.

## Important limitations
- A GitHub connection lets an AI tool inspect and edit repository files if that connector supports those actions. It does not automatically transfer chat history, reasoning, or task state between AI services.
- This handoff file is intended to transfer project context. The receiving assistant must still inspect the latest repository state before editing.
- Multiple assistants should not edit the same files concurrently. Use one assistant at a time or coordinate separate files and review the combined changes.
- External services (Google Flow, Gemini, Canva, YouTube, Meta, TikTok, etc.) require their own supported official integrations, permissions, quotas, and credentials. A connected GitHub account alone does not grant those capabilities.


### Platform-specific account credential setup (2026-11-15)
- `handlers/platforms.py` now uses `PLATFORM_ACCOUNT_FIELDS` as the per-platform credential-field registry.
- YouTube shows Channel ID/Handle, API Key (public data only), and OAuth 2.0 token (private data/upload).
- Facebook shows Page ID and Page Access Token.
- Instagram shows Professional Account ID and Instagram/Meta Access Token.
- TikTok shows profile username, separate OAuth Open ID, and user access token. A profile handle is not the TikTok Open ID.
- LinkedIn shows Person/Organization URN and OAuth access token.
- Unknown/custom platforms do not get misleading generic API-key/token fields. Add their correct schema to `PLATFORM_ACCOUNT_FIELDS` before connecting them.
- Existing account records and legacy Facebook token storage are preserved.
- This is a credential UI/schema improvement, not completed OAuth authorization flows. Tokens are still entered manually; real OAuth connect/callback, refresh-token lifecycle, and platform API integrations remain future work.
- Official auth distinction: YouTube API keys are for public data; OAuth 2.0 is required for private data and upload. TikTok Content Posting requires user OAuth, approved `video.publish` scope, and Open ID. Meta Page/Instagram access depends on the relevant Page/Professional account permissions. LinkedIn uses OAuth 2.0 and granted product scopes.
- Commits: `f2d2b4e` (platform-specific fields), `2596410` (labels and setup guidance), `58efda2` (TikTok Open ID separation), `e0f9e8f` (TikTok prompt correction).


## YouTube OAuth 2.0 connection flow (2026-11-15)

Implemented the first platform OAuth flow for YouTube:
- The YouTube account dashboard has a **Connect YouTube with Google** action.
- The bot creates a random, one-time OAuth state with a 10-minute expiry and a Telegram user/account reference.
- Flask routes `/oauth/youtube/start` and `/oauth/youtube/callback` redirect to Google and exchange the authorization code.
- Requested scopes: `youtube.readonly` and `youtube.upload`.
- Access and refresh tokens are encrypted with Fernet before being stored in the JSON account record. `TOKEN_ENCRYPTION_KEY` is mandatory for OAuth.
- Refresh helper is available in `oauth.get_valid_youtube_access_token(platform, account_name)`; use this when implementing authenticated YouTube API calls.
- Token refresh is implemented as a helper but is not yet wired into upload or analytics services.
- Google client credentials are environment-only: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and exact `GOOGLE_REDIRECT_URI`.
- `GOOGLE_REDIRECT_URI` must be the deployed HTTPS Render service URL plus `/oauth/youtube/callback`.
- Generate a Fernet key locally with Python: `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())`. Put the output in Render as `TOKEN_ENCRYPTION_KEY`; never commit or paste it into chat.
- In Google Cloud Console, configure an OAuth client for a Web application, add the exact callback URL to Authorized redirect URIs, enable YouTube Data API v3, and configure the OAuth consent screen/test users as required.
- The app has not been tested against a real Google OAuth client and has not been deployed. The user must configure the four environment variables and redeploy before the Connect button can complete a real connection.
- Existing manually entered tokens remain supported for compatibility; new OAuth tokens are encrypted.


### User's Render OAuth callback URL (confirmed 2026-11-16)
The user's Render public service URL is `https://all-social-media-manager.onrender.com`.
The exact Google Authorized redirect URI and Render `GOOGLE_REDIRECT_URI` value is:
`https://all-social-media-manager.onrender.com/oauth/youtube/callback`
The same value is now the code default in `config.py`; set it explicitly in Render as well to avoid ambiguity.
The callback now calls YouTube Data API `channels.list?part=snippet&mine=true` using the authorized access token and saves the returned channel ID/title/custom URL with the encrypted credentials. This validates which channel the Google account authorized.
To generate the Fernet-compatible key on the user's Windows PC without installing any package, run:
`python -c "import secrets,base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"`
Copy the one-line output into Render Environment Variables as `TOKEN_ENCRYPTION_KEY`. Keep it private and never change it after OAuth tokens have been encrypted, or existing saved tokens will become unreadable.
