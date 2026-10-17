# Adapt paths to your own checkouts. Run commands in two terminals.
# Kompiler: configure external Kristal Framework and start with your existing invocation.
# Inspect the existing Konstellation bridge with tools/install.py --status first.
# Do not use --apply on an already-integrated or modified checkout.
$env:KONSTELLATION_KOMPILER_URL = "http://127.0.0.1:7788"
$env:KONSTELLATION_ENABLE_KOMPILER_LOCAL = "true" # ONLY on trusted local machine
$env:KONSTELLATION_DEPLOYMENT_PROFILE = "local"
# Optional: if Kompiler local API is configured with a bearer token:
# $env:KONSTELLATION_KOMPILER_TOKEN = "PUT_SECRET_IN_ENV_NOT_IN_FILE"
# In Konstellation checkout: npm install; npm run build; npm start
