# GitHub Repository Lookup

Angel can answer requests such as `Angel, give me a list of my GitHub repos.`

- Uses the public GitHub REST API for public repositories.
- Default owner: `tcdoverlord`.
- Override with `ANGEL_GITHUB_OWNER`.
- A GitHub profile URL in the message takes priority.
- No GitHub token is required for public repository listings.
