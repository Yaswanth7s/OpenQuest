# OpenQuest

OpenQuest is a Django application for discovering opportunities and building teams around community challenges.

## Features

- Individual and organization accounts
- Organization profile submission and administrator verification
- Verified-organization opportunity publishing and individual applications
- Searchable community challenges, comments, teams, submissions, and reviews
- Django admin for account, organization, opportunity, and community management

## Run from a GitHub ZIP (Windows PowerShell)

1. On GitHub, choose **Code → Download ZIP**, then extract the archive.
2. Install Python 3.10 or later. In PowerShell, change to the extracted folder
   containing `manage.py`.
3. Create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate a local secret key and replace the example `SECRET_KEY` value in
`.env` with it. You can edit the file in Notepad:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
notepad .env
```

Then create the local database and start the development server:

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open **http://127.0.0.1:8000/** (use `http`, not `https`). The ZIP contains the
source and `.env.example`, but not your private `.env`, local SQLite database,
or uploaded files. Each person creates their own database by running
`migrate`; use `createsuperuser` if they need an admin account.

The local SQLite database and uploaded files are stored in `db.sqlite3` and
`media/`. Only profile photos are served as public media in development;
resumes, verification documents, and submission attachments use authenticated
download views. Do not commit `.env`, the database, or uploaded files.

## Local setup (Windows PowerShell)

For a Git checkout, use the same setup steps above after cloning the
repository and changing to its directory.

Password reset emails are printed to the development console. For deployed email, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `DEFAULT_FROM_EMAIL`, and the `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and TLS/SSL settings for your mail provider.

To verify the project:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

## Organization verification

An organization registers, completes its organization profile, and waits for review. In Django admin, open **Organization profiles** and use the approve/reject actions. Only approved organizations can publish opportunities or review community submissions.

## Production notes

Set a strong `SECRET_KEY`, `DEBUG=False`, and the deployment hostnames in `ALLOWED_HOSTS`. Set `CSRF_TRUSTED_ORIGINS` to the site's HTTPS origins and make sure TLS is correctly terminated before enabling `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE`. Enable HSTS subdomains/preload only when every affected hostname is permanently HTTPS-ready. Configure `DATABASE_ENGINE`, `DATABASE_NAME`, and, where needed, `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, and `DATABASE_PORT`; install the database driver's Python adapter. Configure SMTP for password-reset delivery. Use persistent private media storage for resumes, verification documents, and submission attachments; do not expose the development `/media/` route publicly. Run `python manage.py collectstatic` and configure the hosting platform to serve `STATIC_ROOT`.

The included SQLite configuration and development media serving are intended for local development, not a multi-user production deployment.
