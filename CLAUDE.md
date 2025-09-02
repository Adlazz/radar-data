# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Django blog application called "Radar Data" that provides a simple content management system with published posts. The project uses Django 5.2.5 with Bootstrap 5 for styling and django-crispy-forms for form handling.

## Development Commands

### Virtual Environment
- Activate virtual environment: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
- Install dependencies: `pip install -r requirements.txt`

### Django Management
- Run development server: `python manage.py runserver`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`
- Collect static files: `python manage.py collectstatic`
- Run Django shell: `python manage.py shell`

### Database
- Database file: `db.sqlite3` (SQLite)
- Reset database: Delete `db.sqlite3` and run `python manage.py migrate`

## Architecture

### Django Apps
- **core/**: Main project configuration and settings
  - `settings.py`: Project settings with Bootstrap 5 and Crispy Forms configured
  - `urls.py`: Root URL configuration routing to post views
  - Django project name: "core"

- **posts/**: Blog functionality
  - `models.py`: Post model with title, slug, excerpt, content, published status, and timestamps
  - `views.py`: Function-based views for post list and detail pages
  - `admin.py`: Admin interface configuration

### Key Models
- **Post**: Main content model with:
  - Auto-generated slugs from titles
  - Published status filtering
  - Image field for illustrative images (optional)
  - Ordering by creation date
  - Images uploaded to `media/posts/` directory

### Templates Structure
- `templates/base.html`: Base template with Bootstrap 5 navbar, messages, and footer
- `templates/posts/`: Post-specific templates
- Uses Bootstrap 5 CDN for styling
- Spanish language base template ("es")

### URL Patterns
- `/`: Post list view
- `/post/<slug>/`: Individual post detail view
- `/admin/`: Django admin interface

### Dependencies
- Django 5.2.5
- django-crispy-forms 2.4 with crispy-bootstrap5 2025.6
- Pillow 11.1.0 for image handling
- Bootstrap 5.3.3 (via CDN)

### Static and Media Files
- Static files served from `static/` directory
- Media files (uploads) served from `media/` directory  
- Post images uploaded to `media/posts/`
- Currently empty but configured for future CSS/JS additions
- Bootstrap loaded via CDN in base template

## Development Notes

- Project uses function-based views (not class-based)
- Slug generation is automatic based on post title
- Posts have published/unpublished status for content control
- Spanish language interface ("Inicio" navigation, "es" lang attribute)
- Uses SQLite database for simplicity
- Debug mode enabled in development settings