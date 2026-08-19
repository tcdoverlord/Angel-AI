# Angel AI — Git Checkpoints

## Genesis 1.0

### Commit

```text
8b06235
Genesis 1.0: WeatherBrain and recovery bootstrap
```

### Tag

```text
v1.0.0
Angel AI Genesis 1.0
```

The tag was verified to point to:

```text
8b062354b8c96768f55eb0932ed8c99a603adead
```

### GitHub

`main` was pushed successfully.

`v1.0.0` was pushed successfully.

Verified state:

```text
8b06235 (HEAD -> main, tag: v1.0.0, origin/main)
```

## Safety

Do not rewrite Genesis history.

Do not force-push.

Do not modify the `v1.0.0` tag.

Future changes should be new commits on `main`.

## Before Significant Changes

Run:

```powershell
git status --short
git branch --show-current
git log --oneline --decorate -5
```

Then inspect the affected files.

## Checkpoint Pattern

```text
Inspect
Protect
Implement
Validate
Commit
Verify
```

Keep unrelated changes out of commits.
