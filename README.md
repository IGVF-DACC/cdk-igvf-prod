# cdk-igvf-prod
This repo is for defining and deploying infrastructure in the `igvf-prod` account that is shared or outlives a particular application's lifecycle (VPCs, security groups, etc).

## Type checking with Mypy
Type annotations can be statically checked with `mypy`:
```bash
$ pip install -r requirements-dev.txt
$ mypy --strict .
```

## Updating snapshots
When making changes review snapshot test failures, and when happy with changes update snapshots:
```bash
$ pytest --snapshot-update
```
