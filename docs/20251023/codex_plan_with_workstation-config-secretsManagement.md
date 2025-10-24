having AWS carve out a hard-coded ~/.aws/ while everyone else invents their own subdirectories is messy. Since we can’t change
  their defaults, the best we can do is standardise how we organise provider credentials on top of what each SDK expects. Here’s a pattern that
  keeps things tidy without fighting the tools:

  ———

  ### 1. Central “Secrets Workspace”

  - Create ~/.config/secrets/ (follows XDG best practices) and treat that as your canonical store for static credentials.
  - Inside it, keep one file per provider with a consistent naming convention:

    ~/.config/secrets/
      aws-ops.env
      gemini.env
      anthropic.env
      bing.env
  - Each file is just KEY=VALUE pairs. They never leave disk unencrypted unless you choose to expose them.

  ### 2. Automate Loading (direnv or helper scripts)

  - Use direnv or a sessenv shell function to source the right provider file into the environment only when you explicitly opt in:

    use_secrets() {
      for secret_file in "$@"; do
        . "$HOME/.config/secrets/${secret_file}"
      done
    }
    Then call use_secrets aws-ops.env gemini.env in direnv or before running a tool.
    Then call use_secrets aws-ops.env gemini.env in direnv or before running a tool.
  - For short-lived commands (e.g., Codex session), prefix:

    export $(grep -v '^#' ~/.config/secrets/aws-ops.env | xargs)

  ### 3. Provider-Specific Expectations

  | Provider     | What they expect | What you store | Notes |
  |--------------|------------------|----------------|-------|
  | AWS      | ~/.aws/{config,credentials} or env vars | Keep master keys in ~/.config/secrets/aws-*.env and let bootstrap script sync them into
  ~/.aws/credentials as needed. | Use profile-per-account; prefer assume-role or SSO when possible. |
  | Google/Gemini | GOOGLE_APPLICATION_CREDENTIALS pointing at a JSON key or GEMINI_API_KEY | Keep JSON files under ~/.config/google/, env files
  in ~/.config/secrets/gemini.env (GEMINI_API_KEY, etc.). | You can symlink or set env var to point at the JSON; avoid scattering copies. |
  | Anthropic | ANTHROPIC_API_KEY | ~/.config/secrets/anthropic.env | Wrapper scripts for claude can source that file. |
  | Bing / Azure | Usually env vars (BING_API_KEY, AZURE_OPENAI_KEY, etc.) | ~/.config/secrets/bing.env | Document expected var names in the file
  header. |
  | OpenAI (if needed) | OPENAI_API_KEY | ~/.config/secrets/openai.env | Same pattern. |

  ### 4. Manage Sprawl with Metadata

  - At the top of each .env file, include comments describing what the key is for, when it expires, and which role/account it hits.
  - Keep a manifest (~/.config/secrets/README.md) listing each file, the associated provider, and rotation cadence.

  ### 5. Encryption and Rotation

  - Encrypt ~/.config/secrets/ with age, sops, or your password manager’s CLI, and decrypt only when you need the creds.
  - Script rotation (rotate_gemini.sh) to update the file, sync to the provider, and re-encrypt.
  - Audit occasionally with a helper like:

    rg --files-with-matches 'AKIA|sk-' ~ --hidden --glob '!.git/*'

  ### 6. Keep Dotfiles in Sync

  - Reference the secrets directory from .bash/bash_env or .bashrc with a single conditional:

    if [ -f "$HOME/.config/secrets/bootstrap.env" ]; then
      . "$HOME/.config/secrets/bootstrap.env"
    fi
  - For Codex or other automated sessions, expose only what’s needed:

    AWS_PROFILE=ops GEMINI_API_KEY=$(grep GEMINI_API_KEY ~/.config/secrets/gemini.env | cut -d= -f2) mix run …

  By anchoring everything under ~/.config/secrets (or a similar central location), you get one “source of truth,” but each provider still sees
  what it expects—AWS caches in ~/.aws, Google reads its JSON path, etc. No more random exports in .bashrc, and you can script/automate access so
  the sprawl is contained.

  If you want a portable version, bundle it into your dotfiles/workstation bootstrap:

  1. scripts/secrets_setup.sh — creates the directory, copies templates, sets permissions.
  2. docs/secrets-playbook.md — defines conventions for each provider (variable names, CLI commands to refresh tokens, where to store JSON keys).
  3. Update your shell aliases/scripts (llm.py, claude, etc.) to source the relevant .env on launch.

  That gives you a clean workflow: everything lives in one tidy namespace, you load what you need when you need it, and Codex (or any other tool)
  can hook in as long as it’s pointed at the right profile or env file.

