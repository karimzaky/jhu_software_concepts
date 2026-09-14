"""defining the routes for website"""

from flask import Blueprint 

#using Blueprint to group page routes into one flask blueprint.
pages = Blueprint ("Pages", __name__) 

@pages.route("/")

def home():
    return "Home Page"


@pages.route("/contact")
def contact():
    return "Contact Page"


@pages.route("/projects")
def projects():
    return "Projects Page"