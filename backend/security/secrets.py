import keyring

SERVICE_NAME = "jarsvis_x_secrets"

def set_secret(key_name: str, secret_value: str):
    """Securely stores an API key or secret in the OS keyring."""
    keyring.set_password(SERVICE_NAME, key_name, secret_value)

def get_secret(key_name: str) -> str:
    """Retrieves a secret from the OS keyring."""
    return keyring.get_password(SERVICE_NAME, key_name)

def delete_secret(key_name: str):
    """Removes a secret from the OS keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, key_name)
    except keyring.errors.PasswordDeleteError:
        pass
