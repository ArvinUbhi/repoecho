# Publish a release

The repository is MIT licensed. Public npm publication requires an authorised npm account; GitHub access alone cannot publish to npm. The initial 1.6.0 package is prepared but not published until that authentication step is completed.

## First publication

Use a clean checkout of the approved main commit with Node 24 and npm 11.5.1+:

```sh
npm ci --ignore-scripts
npm test
npm run check:release
npm publish --dry-run
npm login --auth-type=web --registry=https://registry.npmjs.org
npm publish --access public
```

Authenticate in npm's browser flow, including any required account verification or second factor. Do not paste tokens into issues or chat. Confirm ownership of the `repoecho` package name at publication time; availability is not a reservation. Never overwrite a published version: npm versions are immutable.

After success verify `npm view repoecho@1.6.0 version`, update the README's pending-publication note, and configure trusted publishing for subsequent releases.

## Subsequent releases using GitHub Actions

In the npm package settings add GitHub Actions as a trusted publisher: owner `ArvinUbhi`, repository `repoecho`, workflow filename `publish.yml`, environment `npm`. In GitHub create the `npm` environment and protect it with an appropriate release reviewer. This workflow uses GitHub-hosted runners and short-lived OIDC credentials; do not add an npm token to the repository.

1. Update `package.json`, `package-lock.json`, Python `VERSION`, version-dependent tests and CHANGELOG.md together. Use MAJOR.MINOR.PATCH; do not bump cache compatibility for a packaging-only release.
2. Commit to main and wait for all tests to pass.
3. Push a matching `vMAJOR.MINOR.PATCH` tag on the approved main commit.
4. The publish workflow reruns Python and npm platform tests, verifies the tag/version and main ancestry, then publishes with provenance through the protected environment.
5. Verify the public package and install it into a clean environment before announcing availability. A failed npm authentication step means nothing was published.

The Tests workflow also produces a tested `.tgz` artifact for internal review or offline deployment. The package's publishConfig targets public npm; corporate mirroring is a separate administrator-managed step. Do not tag the initial already-published version to trigger another publish.
