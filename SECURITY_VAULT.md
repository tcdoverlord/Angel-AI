# GitHub Credential Vault Notes

The vault stores the GitHub personal access token encrypted at rest using PBKDF2-SHA256 and AES-256-GCM.

The Settings page provides:
- Create / Replace Vault
- Test GitHub API
- Unlock / Lock
- Delete Credentials
- Reset Vault

Delete and Reset require the vault master password plus an explicit `DELETE` or `RESET` confirmation. These actions remove Angel's local vault files only; revoke the GitHub token separately in GitHub if it should be invalidated.
