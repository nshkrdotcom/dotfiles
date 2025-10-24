
  Dotfiles Repository: Follow-Up Plan

  - Secrets Handling
      - Keep .bash/bash_secrets.template authoritative; add scripts/setup_secrets.sh to copy → .bash/bash_secrets, set chmod 600, and prompt for
        values.
      - Document direnv integration so per-project envs load automatically (e.g., .envrc referencing ~/.bash/bash_secrets).
  - Multi-Account Git & SSH
      - Cross-reference .gitconfig includes with .ssh/config short-hosts; document the n, v, g, f prefixes and map them to aliases (cn, cv, etc.).
      - Add a README section for the GitHub CLI switcher (gh_switch, gh_which) and how it plays with per-directory profiles.
  - Shell Bootstrap
      - Provide a scripts/bootstrap_shell.sh (or reuse the workstation script) that symlinks the dotfiles repo, ensures .bashrc sources .bash/
        components, and installs Starship/zoxide/direnv consistent with the workstation playbook.
      - Include instructions on keeping .gitignore whitelist updated and auditing for stray tracked secrets.
  - Tooling Consistency
      - Align custom scripts (scripts/findWarningsByPrefix.py, llm.py, etc.) with the workstation repo (e.g., shared ~/scripts path).
      - Document dependencies (Python, node, repomix) and provide pipx/asdf commands to install them.
  - Repo Hygiene
      - Add tests/smoke commands (e.g., ./scripts/treeSize.sh ~ ~) to verify nothing sensitive is whitelisted inadvertently.
      - Note the conflict between alias v (directory jump) and clipboard alias v; clarify intended usage or rename to avoid ambiguity.
  - Documentation
      - Expand docs/BASH_CONFIGURATION.md with credential best practices, profile switching examples, and how to interop with Codex (e.g., asking
        the assistant to run env | grep AWS_).
      - Add a new doc covering multi-account AWS/Azure/GCP workflows, referencing gh switcher, aws profiles, and shell aliases.

  These follow-ups keep both repositories aligned: bootstrap covers system-wide setup (credentials, tooling), while dotfiles manage daily-shell
  behavior with clear patterns for secrets, multi-account workflows, and automation.
