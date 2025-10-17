\# 🌸 Luniva Wellness Tracker



Luniva is a gentle companion for cycle tracking, self-care, and wellness insights. Built with Django, it empowers users to reflect, log, and grow through personalized tools and community support.



---



\## 🌿 Features



\- Menstrual cycle tracking (Cycle, FlowDay)

\- Self-care logging (sleep, water, energy, steps)

\- Diary entries with prompts

\- Gratitude journaling

\- Community prompts and anonymous comments

\- Dashboard with wellness insights

\- Profile management

\- Search functionality

\- Admin dashboard for model management

\- Email reminder logic (implemented but not connected to a live service)



---



\## 🛠️ Tech Stack



\- Python 3.13

\- Django 5.2

\- SQLite3

\- HTML/CSS (pastel theme)

\- Git \& GitHub



---



\## 📦 Setup Instructions



To run this project locally:



1\. \*\*Clone the repository\*\*

&nbsp;   ```bash

&nbsp;  git clone https://github.com/YourUsername/luniva-wellness-tracker.git

&nbsp;  cd luniva-wellness-tracker



2\. Create and activate a virtual environment:

&nbsp;  ```bash

&nbsp;   python -m venv venv

&nbsp;   venv\\Scripts\\activate



3\. Install dependencies

&nbsp;  pip install -r requirements.txt



4\. Apply migrations

&nbsp;  python manage.py migrate



5\. Create Superuser:

&nbsp;  python manage.py createsuperuser



6\. Run the development server:

&nbsp;  python manage.py runserver



\## FOLDER STRUCTURE:

tracker\_project/

├── tracker/

│   ├── templates/

│   │   ├── tracker/

│   │   │   ├── registration/

│   │   │   ├── pages/

│   │   │   ├── main/

│   │   │   ├── actions/

│   │   │   └── components/

│   ├── models.py

│   ├── views.py

│   ├── urls.py

│   ├── admin.py

├── manage.py

├── requirements.txt

├── README.md

└── .gitignore



📝 Notes

All templates are organized for clarity and reuse.



Static pages include: home, about, contact, goodbye, welcome.



Email reminder logic is implemented but not connected to a live SMTP service.



requirements.txt lists all dependencies.



.gitignore excludes sensitive and local files like db.sqlite3 and venv.



📜 License

This project is for educational use only.



---

Now you're ready to:

\- Paste this into your `README.md`

\- Save it

\- Push it to GitHub:

&nbsp; ```powershell

&nbsp; git add README.md

&nbsp; git commit -m "Final README added"

&nbsp; git push





