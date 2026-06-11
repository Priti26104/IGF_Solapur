# 🌸 IGF Sadhana Tracker
### ISKCON Girls Forum – Spiritual Community Management System

A beautiful, mobile-first Django web application for tracking daily sadhana, managing mentor-mentee relationships, announcements, and spiritual progress.

---

## ✨ Features

| Feature | Admin | Mentor | Mentee |
|---|---|---|---|
| Dashboard with analytics | ✅ | ✅ | ✅ |
| Send invitations via email | ✅ (mentor) | ✅ (mentee) | — |
| View all users | ✅ | own mentees | — |
| Daily sadhana form | ✅ | ✅ | ✅ |
| Sadhana calendar view | ✅ | ✅ | ✅ |
| Reports + CSV export | ✅ | own group | own |
| Announcements | ✅ post | ✅ post | view |
| Lectures | ✅ manage | view | view |
| Hierarchy tree | ✅ | — | — |
| Streak tracking | ✅ | ✅ | ✅ |
| In-app notifications | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start

### 1. Clone / Extract the project
```bash
cd igf_project
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings (email, secret key, etc.)
```

### 5. Run migrations
```bash
python manage.py migrate
```

### 6. Seed demo data (optional but recommended)
```bash
python manage.py seed_demo
```
This creates:
- **Admin** → `admin@igf.org` / `igfadmin123`
- **Mentor** → `priya@igf.org` / `mentor123`
- **Mentee** → `ananya@igf.org` / `mentee123`
- 30 days of sample sadhana entries
- Sample announcements and lectures

### 7. Run the development server
```bash
python manage.py runserver
```
Visit: **http://localhost:8000**

---

## 📁 Project Structure

```
igf_project/
├── core/                          ← Single app for everything
│   ├── models.py                  ← ALL models (User, Invite, Sadhana, etc.)
│   ├── forms.py                   ← ALL forms
│   ├── views.py                   ← ALL views
│   ├── urls.py                    ← URL routing
│   ├── decorators.py              ← Role-based access decorators
│   ├── admin.py                   ← Django admin registration
│   ├── templatetags/
│   │   └── igf_tags.py            ← Custom template filters
│   └── management/commands/
│       └── seed_demo.py           ← Demo data seeder
│
├── templates/
│   ├── base.html                  ← Base layout with sidebar
│   ├── accounts/                  ← Login, register, invite templates
│   ├── admin_panel/               ← Admin dashboard, mentors, hierarchy
│   ├── mentor/                    ← Mentor dashboard
│   ├── mentee/                    ← Mentee dashboard
│   ├── sadhana/                   ← Form, calendar, detail
│   └── common/                    ← Reports, announcements, lectures, profile
│
├── static/
│   ├── css/igf.css                ← Full custom CSS (pink theme)
│   └── js/igf.js                  ← Interactive JS (charts, sidebar, etc.)
│
├── igf_project/
│   ├── settings.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
└── .env.example
```

---

## 🗄️ Models (all in `core/models.py`)

| Model | Purpose |
|---|---|
| `User` | Custom user model with role (admin/mentor/mentee) + hierarchy |
| `InviteToken` | JWT-style UUID invite tokens (7-day expiry, single use) |
| `SadhanaEntry` | Daily sadhana: chanting, wake time, mangal arati, reading, hearing, service |
| `Announcement` | Text + image + PDF announcements with audience targeting |
| `Lecture` | YouTube lecture links with auto-embed URL generation |
| `Notification` | In-app notifications for mentors/admin |

---

## 📧 Email Setup (Gmail)

1. Enable **2-Factor Authentication** on your Gmail
2. Go to **Google Account → Security → App Passwords**
3. Generate an app password for "Mail"
4. Set in `.env`:
```
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
```

---

## 🌐 Deployment (Render / Railway)

### Environment variables to set:
```
SECRET_KEY=<generate a strong key>
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=<your postgres URL>
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SITE_URL=https://yourdomain.com
```

### Build command:
```bash
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
```

### Start command:
```bash
gunicorn igf_project.wsgi:application
```

---

## 🎨 Color Theme

| Color | Hex | Usage |
|---|---|---|
| Soft Pink | `#F8BBD0` | Primary, borders, sidebar |
| Salmon | `#FFA07A` | Buttons, accents |
| Pink Dark | `#F06292` | Headings, active states |
| Card BG | `#FFF0F5` | Card backgrounds |
| Success | `#A5D6A7` | Completed entries |
| Warning | `#FFE082` | Partial entries |

---

## 🔮 Future Features (Roadmap)

- [ ] WhatsApp reminders via Twilio
- [ ] Ekadashi / festival calendar reminders
- [ ] Birthday reminders
- [ ] Consistency leaderboard
- [ ] PDF certificate generation
- [ ] Mentor health score
- [ ] Mobile app (Flutter)
- [ ] Dark mode
- [ ] Excel export

---

## 🙏 Hare Krishna!

*Built with love for the ISKCON Girls Forum community.*
