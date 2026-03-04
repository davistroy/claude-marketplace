# Deprecated Commands

This directory contains commands that have been deprecated and removed from the active plugin. They are archived here for reference.

## Deprecated Commands

### convert-hooks
- **Deprecated:** 2026-03-04
- **Reason:** Claude Code now handles cross-platform hooks natively. This was a one-time Windows setup utility that is rarely needed. Users can ask Claude ad-hoc for bash-to-PowerShell conversion when required.
- **Replacement:** Ask Claude directly to convert hook scripts, or rely on Claude Code's built-in cross-platform hook support.

### setup-statusline
- **Deprecated:** (pending)
- **Reason:** Claude Code now has a built-in `statusline-setup` agent type that configures status lines. This command was Windows/PowerShell-specific and duplicates built-in functionality.
- **Replacement:** Use Claude Code's built-in status line configuration.

### check-updates
- **Deprecated:** (pending)
- **Reason:** Update checking functionality is being folded into `/validate-plugin` as a `--check-updates` flag rather than maintained as a standalone command.
- **Replacement:** Use `/validate-plugin --check-updates` (once implemented).
