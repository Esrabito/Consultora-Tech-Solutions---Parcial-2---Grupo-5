from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def inicio():
    return render_template("main/inicio.html")
