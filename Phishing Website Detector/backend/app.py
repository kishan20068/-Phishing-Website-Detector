from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import joblib
import numpy as np
import os
import re
from urllib.parse import urlparse
from datetime import datetime
import csv
from werkzeug.utils import secure_filename
import whois

ADMIN_PASSWORD = 'admin123'  # Change this to a strong password!
API_KEY = 'mysecretkey123'  # Change this to a strong, secret value!

POPULAR_DOMAINS = set([
    'google.com', 'amazon.com', 'wikipedia.org', 'microsoft.com', 'apple.com', 'github.com', 'facebook.com', 'twitter.com', 'youtube.com', 'linkedin.com'
])

def get_domain_age_days(domain):
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if creation_date:
            age = (datetime.now() - creation_date).days
            return age if age >= 0 else 0
    except Exception:
        pass
    return 0

def extract_features(url):
    features = {}
    parsed = urlparse(url)
    hostname = parsed.hostname
    features['length_of_url'] = len(url)
    features['num_dots'] = url.count('.')
    features['has_at_symbol'] = int('@' in url)
    features['has_https'] = int(url.lower().startswith('https'))
    features['num_subdomains'] = len(hostname.split('.')) - 2 if hostname else 0
    features['has_ip'] = int(bool(re.match(r"^(http[s]?://)?(\d{1,3}\.){3}\d{1,3}(:\d+)?", url)))
    features['suspicious_keywords'] = int(any(kw in url.lower() for kw in ['login', 'secure', 'update', 'verify', 'account', 'banking']))
    features['domain_length'] = len(hostname) if hostname else 0
    features['has_hyphen'] = int('-' in hostname) if hostname else 0
    features['is_shortened'] = int(any(s in url for s in ['bit.ly', 'tinyurl', 'goo.gl', 'ow.ly', 't.co', 'is.gd', 'buff.ly', 'adf.ly']))
    features['has_double_slash_path'] = int('//' in parsed.path)
    features['has_exe_extension'] = int(url.lower().endswith('.exe'))
    features['domain_age_days'] = get_domain_age_days(hostname) if hostname else 0
    domain_for_pop = hostname.replace('www.', '') if hostname else ''
    features['is_popular_domain'] = int(domain_for_pop in POPULAR_DOMAINS)
    return features

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
model = joblib.load('backend/model.pkl')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # API key check
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({'error': 'Unauthorized: Invalid or missing API key.'}), 401
    data = request.json
    url = data.get('url', '')
    features = extract_features(url)
    X = np.array([list(features.values())])
    proba = model.predict_proba(X)[0]
    prediction = int(model.predict(X)[0])
    confidence = float(np.max(proba))
    # Simple explanation logic
    explanation = []
    if features['has_at_symbol']:
        explanation.append('URL contains @ symbol')
    if features['has_ip']:
        explanation.append('URL uses IP address')
    if features['suspicious_keywords']:
        explanation.append('Suspicious keyword in URL')
    if not features['has_https']:
        explanation.append('No HTTPS')
    if features['num_subdomains'] > 2:
        explanation.append('Many subdomains')
    if not explanation:
        explanation.append('No obvious phishing signs')
    explanation_str = ', '.join(explanation)
    # Log phishing detections
    if prediction == 1:
        log_path = 'backend/phishing_log.csv'
        file_exists = os.path.isfile(log_path)
        with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['timestamp', 'url', 'confidence', 'explanation'])
            writer.writerow([
                datetime.now().isoformat(),
                url,
                f"{confidence:.3f}",
                explanation_str
            ])
    return jsonify({
        'prediction': prediction,
        'confidence': confidence,
        'explanation': explanation_str
    })

@app.route('/analytics')
def analytics():
    log_path = 'backend/phishing_log.csv'
    total_checks = 0
    phishing_count = 0
    legit_count = 0
    recent_phishing = []
    if os.path.isfile(log_path):
        with open(log_path, 'r', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            phishing_count = len(reader)
            total_checks = phishing_count  # Only phishing are logged
            # For demo, assume legit_count = total_checks * 2 (since only phishing are logged)
            legit_count = phishing_count * 2
            recent_phishing = reader[-10:][::-1] if len(reader) > 0 else []
    return render_template('analytics.html',
        total_checks=total_checks+legit_count,
        phishing_count=phishing_count,
        legit_count=legit_count,
        recent_phishing=recent_phishing
    )

@app.route('/history')
def history():
    log_path = 'backend/phishing_log.csv'
    history = []
    if os.path.isfile(log_path):
        with open(log_path, 'r', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            history = reader[::-1] if len(reader) > 0 else []  # Newest first
    return jsonify(history)

@app.route('/history_page')
def history_page():
    log_path = 'backend/phishing_log.csv'
    history = []
    if os.path.isfile(log_path):
        with open(log_path, 'r', encoding='utf-8') as csvfile:
            reader = list(csv.DictReader(csvfile))
            history = reader[::-1] if len(reader) > 0 else []  # Newest first
    return render_template('history.html', history=history)

@app.route('/feedback', methods=['POST'])
def feedback():
    api_key = request.headers.get('x-api-key')
    if api_key != API_KEY:
        return jsonify({'error': 'Unauthorized: Invalid or missing API key.'}), 401
    data = request.json
    url = data.get('url', '')
    prediction = data.get('prediction', '')
    user_feedback = data.get('user_feedback', '')
    log_path = 'backend/user_feedback.csv'
    file_exists = os.path.isfile(log_path)
    with open(log_path, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['timestamp', 'url', 'prediction', 'user_feedback'])
        writer.writerow([
            datetime.now().isoformat(),
            url,
            prediction,
            user_feedback
        ])
    return jsonify({'status': 'ok'})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    status = None
    success = False
    if request.method == 'POST':
        password = request.form.get('password')
        file = request.files.get('dataset')
        if password != ADMIN_PASSWORD:
            status = 'Incorrect password.'
        elif not file or not file.filename.endswith('.csv'):
            status = 'Please upload a valid CSV file.'
        else:
            filename = secure_filename('phishing_site_urls.csv')
            file.save(os.path.join('backend', filename))
            # Retrain model
            try:
                import pandas as pd
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.model_selection import train_test_split
                import joblib
                import re
                from urllib.parse import urlparse
                # Feature extraction (same as above)
                def extract_features(url):
                    features = {}
                    features['length_of_url'] = len(url)
                    features['num_dots'] = url.count('.')
                    features['has_at_symbol'] = int('@' in url)
                    features['has_https'] = int(url.lower().startswith('https'))
                    features['num_subdomains'] = len(urlparse(url).hostname.split('.')) - 2 if urlparse(url).hostname else 0
                    features['has_ip'] = int(bool(re.match(r"^(http[s]?://)?(\d{1,3}\.){3}\d{1,3}(:\d+)?", url)))
                    features['suspicious_keywords'] = int(any(kw in url.lower() for kw in ['login', 'secure', 'update', 'verify', 'account', 'banking']))
                    features['domain_length'] = len(urlparse(url).hostname) if urlparse(url).hostname else 0
                    features['has_hyphen'] = int('-' in urlparse(url).hostname) if urlparse(url).hostname else 0
                    features['is_shortened'] = int(any(s in url for s in ['bit.ly', 'tinyurl', 'goo.gl', 'ow.ly', 't.co', 'is.gd', 'buff.ly', 'adf.ly']))
                    features['has_double_slash_path'] = int('//' in urlparse(url).path)
                    features['has_exe_extension'] = int(url.lower().endswith('.exe'))
                    return features
                df = pd.read_csv('backend/phishing_site_urls.csv')
                feature_rows = []
                for _, row in df.iterrows():
                    feats = extract_features(row['url'])
                    feats['label'] = row['label']
                    feature_rows.append(feats)
                feature_df = pd.DataFrame(feature_rows)
                X = feature_df.drop('label', axis=1)
                y = feature_df['label']
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
                model = RandomForestClassifier()
                model.fit(X_train, y_train)
                joblib.dump(model, 'backend/model.pkl')
                status = 'Model retrained successfully!'
                success = True
            except Exception as e:
                status = f'Error during retraining: {e}'
    return render_template('admin.html', status=status, success=success)

if __name__ == '__main__':
    app.run(debug=True) 