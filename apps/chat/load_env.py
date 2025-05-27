def load_env(filepath=".env"):
    try:
        with open(filepath) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    import os
                    os.environ.setdefault(key, value)
    except FileNotFoundError:
        print(f"[WARNING] .env file not found at {filepath}")
