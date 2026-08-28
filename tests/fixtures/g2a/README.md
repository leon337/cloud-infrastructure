# G2-A disposable integration fixtures

The executable G2-A integration tests create all Project manifests and Git workspaces inside temporary directories at test time.

This directory intentionally contains no live workspace, credential, secret, repository checkout, or NODE-01 state. It exists only to document that `tests/test_g2a_integration.py` is disposable and must not depend on `/home/ubuntu/mcf-workspaces`.
