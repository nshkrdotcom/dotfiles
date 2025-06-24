# Bash Configuration Organization

This document explains how the bash configuration has been organized for better security, maintainability, and organization.

## File Structure

```
~/.bashrc           # Main bash configuration (system settings, tool initialization)
~/.bash_aliases     # Custom aliases and functions
~/.bash_env         # Non-sensitive environment variables
~/.bash_secrets     # Sensitive environment variables (API keys, passwords)
~/.gitignore        # Protects sensitive files from being committed
```

## File Descriptions

### `~/.bashrc`
The main bash configuration file containing:
- Standard bash settings (history, prompt, colors)
- Tool initialization (pyenv, nvm, cargo)
- Sourcing of other configuration files
- System-level configurations

### `~/.bash_aliases`
Contains all custom aliases and functions organized by category:
- Directory navigation aliases
- File listing aliases
- Git aliases and functions
- Clipboard utilities
- Application shortcuts
- Development functions (Elixir, Python)
- Environment management functions

### `~/.bash_env`
Non-sensitive environment variables organized by category:
- Development tools configuration
- PATH extensions
- Database configuration (non-production)
- AI/LLM configuration (non-sensitive settings)
- Application configuration

### `~/.bash_secrets`
Sensitive environment variables including:
- API keys (Google/Gemini, etc.)
- Database credentials with passwords
- Application secrets
- **File permissions: 600 (owner read/write only)**

## Security Features

1. **File Permissions**: `.bash_secrets` has restrictive 600 permissions
2. **Whitelist Git Protection**: `.gitignore` uses a whitelist approach - ignores everything by default, only allows explicitly safe files
3. **Separation of Concerns**: Sensitive data isolated from regular configuration
4. **Clear Documentation**: Each file clearly marked with its purpose
5. **Defense in Depth**: Multiple layers of protection (permissions + gitignore + file separation)

## Usage

All files are automatically loaded when you start a new bash session or run:
```bash
source ~/.bashrc
```

## Best Practices

1. **Never commit `.bash_secrets`** to version control
2. **Keep API keys in `.bash_secrets`** only
3. **Use environment-specific configurations** for different projects
4. **Regularly audit** what's in your secrets file
5. **Consider using a password manager** for production environments
6. **Whitelist approach**: The `.gitignore` uses a secure-by-default approach - only explicitly safe files are allowed to be committed

## Git Security Model

The `.gitignore` uses a **whitelist approach**:
- `*` - Ignores everything by default
- `!filename` - Explicitly allows safe files
- Sensitive files are explicitly blacklisted even if whitelisted

This means:
- **Maximum security by default** - new files are ignored unless explicitly allowed
- **No accidental commits** of sensitive data
- **Easy to audit** what files can be committed

## Maintenance

- **Adding new aliases**: Edit `~/.bash_aliases`
- **Adding non-sensitive env vars**: Edit `~/.bash_env`
- **Adding API keys/secrets**: Edit `~/.bash_secrets`
- **System configuration**: Edit `~/.bashrc`

## Migration Notes

All environment variables and aliases have been moved from the original `.bashrc` to their appropriate files. The functionality remains exactly the same, but now with better organization and security. 