Try to fulfill the following points before the Pull Request is merged:

- [ ] The PR is reviewed by one of the team members.
- [ ] If a linting PR exists, it must be merged before this PR is allowed to be merged.
- [ ] If the PR is merged in the master then a release should be be made.
- [ ] If the new code is readable, if not it should be well commented

For releases only:

- [ ] If the review of this PR is approved and the PR is followed by a release then the .env file
  in the cloud-portal repo should also be updated.
- [ ] If you are making a release then please sum up the changes since the last release on the release page using the [clog](https://github.com/clog-tool/clog-cli) tool with `clog -F`
