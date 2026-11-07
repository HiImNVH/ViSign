# CP7 T096 — AWS access bootstrap evidence

| Field | Value |
|---|---|
| Date | `2026-11-07` |
| Region | `ap-southeast-2` (Sydney) |
| Project | `Rubber Ducking` |
| Stack | `visign-github-oidc` |
| Task | `T096` |
| Result | `BLOCKED` — automated OIDC deployment chưa được thiết lập |

## Attempt result

- CloudFormation accepted `infra/aws/cloudformation/bootstrap-github-oidc.yml` and started creation.
- `GitHubActionsOidcProvider` failed with HTTP `403`: an AWS-managed Service Control Policy explicitly
  denied `iam:CreateOpenIDConnectProvider` for the Free Plan project.
- The stack finished `ROLLBACK_COMPLETE`.
- The provider resource finished `DELETE_COMPLETE`; no `ViSignGitHubDeployRole`, IAM user, access key,
  compute, storage or production workload was created by this attempt.
- Account/organization/request identifiers are intentionally omitted from repository evidence.

## Human access fallback

- Hoang Tin accepted the AWS Settings invitation and appears as a team member alongside the owner.
- Team membership permits project resource work but not owner-only administrative/financial actions.
- Tín may use only Tín's own AWS Builder ID session in Console/CloudShell for temporary integration.
- Root credentials, owner session, payment method and static AWS keys MUST NOT be shared or created.

## Decision gate

- Keep the AWS Free Plan; do not upgrade Paid Plan or activate Advanced Features without a separate,
  explicit owner decision after reviewing spend-limit and billing impact.
- Do not retry the OIDC stack while the SCP blocker remains.
- Do not replace OIDC with `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` GitHub secrets.
- Manual integration does not satisfy T091/T096; both tasks remain open until quality-gated deployment,
  least-privilege identity, production smoke and rollback evidence pass.

## Next checkpoint

Before creating EC2/EIP/ECR/S3/CloudFront resources, T095 must have an approved resource/cost scope,
the current quality gate must pass, and the owner must explicitly confirm the cloud creation step.
