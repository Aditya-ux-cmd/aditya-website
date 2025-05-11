# app.py (Your Python Flask Backend)
from flask import Flask, render_template, request, redirect, url_for, session
import datetime # For the current year in footer (could also be done in JS)

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here_replace_this' # IMPORTANT: Change this!

# --- Conceptual Database/Data Storage ---
# In a real application, this would be a database (PostgreSQL, MySQL, etc.)
# For demonstration, we'll use a simple dictionary.
# NOTE: Data added via 'add_fact' will be lost when the server restarts.
facts_data = {
    "world": [
        {"id": 1, "title": "Fact about Owls", "text": "Did you know that a group of owls is called a parliament?", "image": "https://via.placeholder.com/400x250?text=Owl+Parliament"},
        {"id": 2, "title": "Fact about France", "text": "France is the most visited country in the world.", "image": "https://via.placeholder.com/400x250?text=France+Fact"},
    ],
    "science": [
        {"id": 3, "title": "Fact about Space", "text": "There are more stars in the universe than grains of sand on all the Earth's beaches.", "image": "https://via.placeholder.com/400x250?text=Space+Fact"},
        {"id": 4, "title": "Fact about Water", "text": "Hot water freezes faster than cold water (Mpemba effect).", "image": "https://via.placeholder.com/400x250?text=Water+Fact"},
    ]
}

# --- User Data (for conceptual login) ---
# NOTE: Passwords are not hashed for simplicity. Use a library like Werkzeug's security
# for password hashing in a real application!
users = {
    "testuser": {"password": "password123"} # Example user
}

# --- Routes ---

@app.context_processor
def inject_current_year():
    """Injects the current year into all templates."""
    return {'current_year': datetime.datetime.now().year}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/categories')
def categories():
    return render_template('categories.html', categories=sorted(facts_data.keys()))

@app.route('/category/<category_name>')
def view_category(category_name):
    category_facts = facts_data.get(category_name.lower(), [])
    if not category_facts:
        return "Category not found!", 404 # Or render a custom error page
    return render_template('category_facts.html', category_name=category_name, facts=category_facts)

@app.route('/fact/<int:fact_id>')
def view_fact(fact_id):
    found_fact = None
    current_category = None # To correctly handle next/prev fact within category

    for category_name, category_facts in facts_data.items():
        for i, fact in enumerate(category_facts):
            if fact['id'] == fact_id:
                found_fact = fact
                current_category = category_name
                # Determine next/previous fact IDs within the same category
                prev_fact_id = category_facts[i-1]['id'] if i > 0 else None
                next_fact_id = category_facts[i+1]['id'] if i < len(category_facts) - 1 else None
                break
        if found_fact:
            break

    if not found_fact:
        return "Fact not found!", 404

    # --- 5-Minute/5-Fact Limit Logic (Conceptual & Client-Side Session based) ---
    # This is a simplified logic. For robust production, combine with server-side
    # database tracking for each user, and more sophisticated timing.
    if 'username' not in session: # Only apply limit if not logged in
        if 'fact_view_timestamps' not in session:
            session['fact_view_timestamps'] = {}
        if 'fact_ids_viewed' not in session:
            session['fact_ids_viewed'] = set() # Use a set to count unique facts

        # Add current fact to viewed unique facts
        session['fact_ids_viewed'].add(fact_id)

        # Track timestamp of current view
        session['fact_view_timestamps'][str(fact_id)] = datetime.datetime.now().timestamp()

        # Clean up old timestamps (e.g., older than 5 minutes)
        cutoff_time = datetime.datetime.now().timestamp() - (5 * 60) # 5 minutes ago
        session['fact_view_timestamps'] = {
            k: v for k, v in session['fact_view_timestamps'].items()
            if v >= cutoff_time
        }

        # Count unique facts viewed within the last 5 minutes
        unique_facts_in_timeframe = len(session['fact_view_timestamps'])

        # Check if limit is exceeded (e.g., more than 5 unique facts viewed within 5 minutes)
        if unique_facts_in_timeframe > 5:
            return redirect(url_for('login', next=request.url, message="You've viewed too many facts. Please login to view more!"))
        elif len(session['fact_ids_viewed']) > 10: # Example: Limit total unique facts viewed without login
            return redirect(url_for('login', next=request.url, message="You've viewed many facts. Please login to continue exploring!"))

    return render_template('single_fact.html', fact=found_fact,
                           prev_fact_id=prev_fact_id, next_fact_id=next_fact_id,
                           current_category=current_category)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # In a real app, you'd use werkzeug.security.check_password_hash
        if username in users and users[username]['password'] == password:
            session['username'] = username
            # Clear session fact view tracking on successful login
            session.pop('fact_view_timestamps', None)
            session.pop('fact_ids_viewed', None)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    return render_template('login.html', message=request.args.get('message'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return render_template('register.html', error="Username already exists.")
        # In a real app, you'd use werkzeug.security.generate_password_hash
        users[username] = {"password": password}
        session['username'] = username
        # Clear session fact view tracking on successful registration
        session.pop('fact_view_timestamps', None)
        session.pop('fact_ids_viewed', None)
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('fact_view_timestamps', None)
    session.pop('fact_ids_viewed', None)
    return redirect(url_for('home'))

@app.route('/add_fact', methods=['GET', 'POST'])
def add_fact():
    if 'username' not in session:
        return redirect(url_for('login', message="Please login to add facts."))
    # In a real app, you'd also check for user roles (e.g., only 'admin' or 'contributor' can add)

    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']
        image = request.form['image'] # For simplicity, taking a URL
        category = request.form['category'].lower().replace(' ', '_') # Normalize category name

        if not title or not text or not image or not category:
            return render_template('add_fact.html', categories=sorted(facts_data.keys()), error="All fields are required.")

        if category not in facts_data:
            facts_data[category] = []

        # Assign a new ID. In a real DB, this is auto-incremented.
        all_fact_ids = [f['id'] for cat in facts_data.values() for f in cat]
        new_id = max(all_fact_ids) + 1 if all_fact_ids else 1

        facts_data[category].append({
            "id": new_id,
            "title": title,
            "text": text,
            "image": image
        })
        return redirect(url_for('view_category', category_name=category))
    return render_template('add_fact.html', categories=sorted(facts_data.keys()))

@app.route('/remove_fact/<int:fact_id>', methods=['POST'])
def remove_fact(fact_id):
    if 'username' not in session:
        return redirect(url_for('login', message="Please login to remove facts."))
    # IMPORTANT: In a real app, only administrators should have this permission.

    found_and_removed = False
    for category_name, category_facts in list(facts_data.items()): # Iterate over a copy
        initial_len = len(category_facts)
        facts_data[category_name] = [fact for fact in category_facts if fact['id'] != fact_id]
        if len(facts_data[category_name]) < initial_len:
            found_and_removed = True
            # If a category becomes empty, you might want to remove it from facts_data
            if not facts_data[category_name]:
                del facts_data[category_name]
            break # Fact found and removed from its category

    if found_and_removed:
        return redirect(url_for('home')) # Or redirect to a more relevant page
    else:
        return "Fact not found for removal.", 404 # Or render an error page

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # In a real application, you would process this form data:
        # - Send an email (using Flask-Mail, SMTPlib, etc.)
        # - Save to a database
        # - Implement CAPTCHA to prevent spam
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        print(f"Contact Form Submission: Name={name}, Email={email}, Subject={subject}, Message={message}")
        return render_template('contact.html', success_message="Your message has been sent!")
    return render_template('contact.html')

# For search functionality (Conceptual)
@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    search_results = []
    if query:
        for category_name, category_facts in facts_data.items():
            for fact in category_facts:
                # Simple keyword search in title and text
                if query in fact['title'].lower() or query in fact['text'].lower():
                    search_results.append(fact)
    return render_template('search_results.html', query=query, results=search_results)


# Run the application
if __name__ == '__main__':
    # For local development, debug=True enables reloader and debugger
    app.run(debug=True)