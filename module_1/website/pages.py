"""defining the routes for website"""

from flask import Blueprint, render_template

#using Blueprint to group page routes into one flask blueprint.
pages = Blueprint("pages", __name__)


@pages.route("/")
def home():
    
    return render_template("home.html", active_page="home") 
# render_template() used to locate and display HTML file from the templates folder.
#activate_page is used to tell the navigation bar which tab to highlight.



@pages.route("/contact")
def contact():
    
    return render_template("contact.html", active_page="contact")


@pages.route("/projects")
def projects():
    
    return render_template("projects.html", active_page="projects")


