# MedTracker
I built this app to help me keep track of when I last took some medications that have strict rules about how often you can take them. It's pretty niche, but maybe others will find it useful as well.

When I concieved of this app, I had just started taking Sumatriptan, which can only be taken twice in 24 hours, and you have to wait at least 2 hours between doses. Due to the condition I was put on that medication for, I was having trouble figuring out the timing and remembering when I could take it again, so here we are. Once you enter the details of your meds, a quick glance at the main page will tell you if you can take it again or not, and if not, when you can.

This app is designed to be self-hosted on a private network. There is no authentication or authorization built in, so all of the records contained in it are accessible to anyone who can reach it. I might fix this in the future, but it's not really on the roadmap at the moment.

The app consists of three containers:

- Nginx - handles the static content for the frontend
- Flask - handles the dynamic content for the front end, as well as being the actual application itself
- PostgreSQL - database

Nginx is really only there to handle the CSS and JS files, since Flask wasn't handling it well. If you are running Nginx Proxy Manager as a reverse proxy in front of this, make sure you have Cache Assets, and Block Common Exploits disabled in the proxy host config or it will break CSS and JS.

I haven't load tested this app at all, so I have no idea how it will behave with a large number of medications, if you're unfortunate enough to need it for that.

## Installation
1. Clone the repository
2. Make any changes you want to the `docker-compose.yml` file, such as changing the database password or the port that Nginx runs on
   - If you want to change the database password, edit the `POSTGRES_PASSWORD` environment variable in the `docker-compose.yml` file under the `postgres` service.
   - If you want to change the port that Nginx runs on, edit the `ports` section under the `nginx` service. The default is `5080:80`.
   - Don't change the `exposes:` section under the `app` service, as that is used to connect the Flask app to the Nginx container.
    - If you want to change the port that the Flask app runs on, you also need to update the nginx.conf file in the `nginx` directory to match the new port.
3. Run `docker compose up -d` to build and start in one command
4. Open your web browser and navigate to `http://<your-server-ip>:5080` (or whatever port you choose to run Nginx on)
5. Give it a minute or to to start up, then refresh the page
6. Add your medications and start tracking them!


## Important Note
This app is not medical advice, and I am not a doctor. If you have questions about your medications, please consult your doctor or pharmacist. This is simply a tool to help you keep track of when you last took your medications, and when you can take them again. <b>*Use it at your own risk.*</b>