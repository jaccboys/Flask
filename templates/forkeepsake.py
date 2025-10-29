# <!doctype html>
# <html lang="en">
# <head>
#     <meta charset="utf-8">
#     <title>{% block title %}VINYL TECH{% endblock %}</title>
#     <meta name="viewport" content="width=device-width,initial-scale=1">
#     <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
#     <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
# </head>
# <body class="{% block body_class %}{% endblock %}">
#     <nav>
#         <div class="logo">VINYL TECH</div>
#         <div class="nav-links">
#             <a href="{{ url_for('home') }}">Home</a>
#             <a href="{{ url_for('products') }}">All</a>
#             <a href="{{ url_for('turntables') }}">Turntables</a>
#             <a href="{{ url_for('speakers') }}">Speakers</a>
#             <a href="{{ url_for('amplifiers') }}">Amplifiers</a>
#             <a href="{{ url_for('about') }}">About</a>
#         </div>
#     </nav>

#     <main class="container" style="margin-top:100px;">
#         {% block content %}{% endblock %}
#     </main>
# </body>
# </html>