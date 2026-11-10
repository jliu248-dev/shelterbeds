"""Custom error pages."""
from flask import flash, redirect, render_template, url_for


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def too_large(error):
        flash("That file is too big. The limit is 5 MB.", "danger")
        return redirect(url_for("shelters.index"))
