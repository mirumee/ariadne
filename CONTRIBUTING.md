# Contributing

Thank you for your interest in contributing to Ariadne!

We welcome bug reports, questions, pull requests, and general feedback.

We also ask all contributors to familiarize themselves with and follow project's code of conduct, available in the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) file kept in the repository's main directory.


# Reporting bugs, asking for help, offering feedback and ideas

You can use [GitHub issues](https://github.com/mirumee/ariadne/issues) to report bugs, ask for help, share your ideas, or simply offer feedback. We are curious what you think of Ariadne!


## Development setup

Ariadne is written to support Python 3.9, 3.10, 3.11, 3.12, and 3.13.

We use [Hatch](https://github.com/pypa/hatch) for project management


The codebase is formatted using [ruff](https://github.com/astral-sh/ruff).
To format the code, use the following command:
```bash
hatch fmt
```


The contents of the `ariadne` package are annotated with types and validated using [mypy](http://mypy-lang.org/index.html). To run type checking with mypy, use:
```bash 
hatch run types:check
```


Tests are developed using [pytest](https://pytest.org/) and are managed with Hatch.
We use [Codecov](https://codecov.io/gh/mirumee/ariadne) for monitoring coverage.


To run the tests, use:
```bash
hatch test
```


To run integrations tests use:
```bash
hatch run test-integration-fastapi:test
hatch run test-integration-flask:test
hatch run test-integration-starlette:test
```


To run all checks (formatting, type checking, and tests), you can use:
```bash
hatch run check
```

We require all changes to be done via pull requests, and to be approved by member-ranked users before merging.


## Working on issues

We consider all issues which are not assigned to anybody as being available for contributors. The **[help wanted](https://github.com/mirumee/ariadne/labels/help%20wanted)** label is used to single out issues that we consider easier or higher priority on the list of things that we would like to see.

If you've found issue you want to help with, please add your comment to it - this lets other contributors know what issues are being worked on, as well as allowing maintainers to offer guidance and help.


## Pull requests

We don't require pull requests to be followed with bug reports. If you've found a typo or a silly little bug that has no issue or pull request already, you can open your own pull request. We only ask that this PR provides context or explanation for what problem it fixes, or which area of the project it improves.
