# For developers

## Adding new backends

See [interface.py], which defines the interface of a backend and may serve as a template for creating new backends.



## Creating new release

To create a new release, it is good to have a release summary.

To add this, create a milestone that matches the new version and tag, e.g., `v1.0.8`.

Then create a new issue, adding it to the milestone and add the `release-summary` label.

For the issue description, write the actual release summary.
This will be included as part of the changelog as well as the release notes on GitHub.

Then, go to [create a new GitHub releases](https://github.com/EMMC-ASBL/tripper/releases/new) and select the tag that matches the milestone (creating a new one).
Add again the tag as the release title (optionally write something else that defines this release as a title).

Finally, press the "Publish release" button and ensure the release workflow succeeds (check [the release workflow](https://github.com/EMMC-ASBL/tripper/actions/workflows/cd_release.yml)).




[interface.py]: https://github.com/EMMC-ASBL/tripper/blob/master/tripper/interface.py
