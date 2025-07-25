import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
import re
from urllib.parse import urlparse
import socket
import whois
from datetime import datetime

# Small set of popular domains for demo
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

# --- Feature extraction from URL ---
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
    # New features:
    features['domain_age_days'] = get_domain_age_days(hostname) if hostname else 0
    # Remove www. for popularity check
    domain_for_pop = hostname.replace('www.', '') if hostname else ''
    features['is_popular_domain'] = int(domain_for_pop in POPULAR_DOMAINS)
    return features

# --- Load and process dataset ---
df = pd.read_csv('backend/phishing_site_urls.csv')  # Now expects columns: url,label

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